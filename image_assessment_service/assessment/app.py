import os
import pathlib
from typing import List, Optional

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv

from image_assessment_service.assessment.services.base import AssessmentService
from image_assessment_service.assessment.services.classification.service import (
    CLASSIFICATION_FEATURES,
    ClassificationService,
)
from image_assessment_service.assessment.services.registry import SERVICES, register_services
from image_assessment_service.assessment.features_meta import FEATURE_META
from image_assessment_service.apis.admin_api import router as admin_router
from image_assessment_service.apis.annotation_api import router as annotation_router
from image_assessment_service.apis.assess_api import router as assess_router
from image_assessment_service.apis.dashboard_api import router as dashboard_router
from image_assessment_service.apis.profile_api import router as profile_router
from image_assessment_service.apis.task_api import router as task_router
from image_assessment_service.autorization.models import core
from image_assessment_service.autorization.models.database import (
    db_session,
    get_engine,
    init_database,
)
from image_assessment_service.autorization.routers.csrf import router as csrf_router
from image_assessment_service.autorization.routers.items import router as item_router
from image_assessment_service.autorization.routers.tokens import router as tokens_router
from image_assessment_service.autorization.routers.users import router as user_router
from image_assessment_service.config import get_config, get_templates
from image_assessment_service.core.middleware.session import SessionMiddleware
from image_assessment_service.dependencies import get_container
from image_assessment_service.logger import LOG_LEVELS, set_log_level
from image_assessment_service.rate_limit import setup_rate_limiter

load_dotenv()

CURRENT_PATH = pathlib.Path(__file__).resolve().parents[1]
STATIC_FILES_PATH = CURRENT_PATH / "static/"


class AssessmentApp:
    """Приложение разметки изображений.

    Собирает включённые сервисы/фичи, инициализирует их при старте и регистрирует
    роутеры/статику/мидлвары. Точка входа — ``cli.py`` (все включённые или
    ``--services`` для подмножества).
    """

    def __init__(self, service_codes: Optional[List[str]] = None):
        self.service_codes = service_codes

    def build_services(self) -> List[AssessmentService]:
        config = get_config()
        codes = self.service_codes
        if codes is None:
            codes = self._enabled_service_codes(config)

        services = []
        for code in codes:
            if code == "classification":
                services.extend(ClassificationService().build_features())
            elif code in CLASSIFICATION_FEATURES:
                services.append(CLASSIFICATION_FEATURES[code]())
            elif code in ("detection", "segmentation"):
                services.append(SERVICES[code]())
        return services

    def _enabled_service_codes(self, config) -> List[str]:
        codes = ["detection", "segmentation"]
        codes.extend(
            code for code, cfg in config.services.classification.features.items() if cfg.enabled
        )
        return codes

    def build_app(self) -> FastAPI:
        self._init_storage()

        app = FastAPI(title="Image Assessment Service")
        app.add_middleware(SessionMiddleware)
        setup_rate_limiter(app)

        services = self.build_services()
        register_services(services)
        structlog.get_logger().info(
            f"Enabled services: {[s.code for s in services]}"
        )

        self._register_startup_hook(app, services)
        self._register_exception_handlers(app)
        self._register_routers(app)
        self._register_static(app)

        return app

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        config = get_config()
        app = self.build_app()
        run_app(app, host or config.application.host, port or config.application.port)

    # ---- internals ----

    def _init_storage(self) -> None:
        init_database()
        core.Base.metadata.create_all(bind=get_engine())

    def _register_startup_hook(self, app: FastAPI, services: List[AssessmentService]) -> None:
        @app.on_event("startup")
        async def startup_event():
            with db_session() as db:
                for service in services:
                    service.init(db)
            container = get_container()
            await container.data_uploader_service.start_cleanup_daemon()

    def _register_exception_handlers(self, app: FastAPI) -> None:
        self._register_not_found_handler(app)
        self._register_global_handler(app)

    def _register_not_found_handler(self, app: FastAPI) -> None:
        @app.exception_handler(404)
        async def not_found_exception_handler(request: Request, _: Exception):
            if is_api_request(request):
                return JSONResponse(
                    status_code=404,
                    content={
                        "detail": "Not found",
                        "path": str(request.url.path),
                    },
                )
            return RedirectResponse(url="/assess/main", status_code=302)

    def _register_global_handler(self, app: FastAPI) -> None:
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            _log_unhandled_exception(request, exc)
            return JSONResponse(
                status_code=500,
                content={"detail": "Unexpected server error."},
            )

    def _register_routers(self, app: FastAPI) -> None:
        self._register_api_routers(app)
        self._register_user_routers(app)
        self._register_page_routers(app)

    def _register_api_routers(self, app: FastAPI) -> None:
        app.include_router(assess_router)
        config = get_config()
        for code, router in self._feature_routers():
            meta = FEATURE_META[code]
            cfg = config.feature_config(code)
            if cfg is not None and cfg.enabled:
                app.include_router(router, prefix=f"/assess/{meta['path']}", tags=['API'])
            else:
                self._register_disabled_feature_routes(app, meta)
        app.include_router(item_router, prefix='/assess/items')
        app.include_router(csrf_router, prefix='/assess/csrf')

    def _feature_routers(self):
        from image_assessment_service.apis.aesth_api import aesth_api
        from image_assessment_service.apis.classify_api import classify_api
        from image_assessment_service.apis.image_filter_api import image_filter_api
        from image_assessment_service.apis.tech_api import tech_api

        return [
            ("tech", tech_api),
            ("aesth", aesth_api),
            ("filter", image_filter_api),
            ("classify", classify_api),
        ]

    def _register_disabled_feature_routes(self, app: FastAPI, meta: dict) -> None:
        prefix = f"/assess/{meta['path']}"

        @app.get(prefix, include_in_schema=False)
        @app.get(f"{prefix}/{{path:path}}", include_in_schema=False)
        async def not_developed(request: Request, path: str = ""):
            if is_api_request(request):
                return JSONResponse(
                    status_code=404,
                    content={
                        "detail": "Assessment feature is not enabled",
                        "path": str(request.url.path),
                    },
                )
            return get_templates().TemplateResponse(
                "not_developed.html",
                {
                    "request": request,
                    "service_name": meta["title"],
                    "service_code": meta["path"],
                },
            )

    def _register_user_routers(self, app: FastAPI) -> None:
        app.include_router(user_router, prefix='/assess/users')
        app.include_router(tokens_router, prefix='/assess/tokens')

    def _register_page_routers(self, app: FastAPI) -> None:
        app.include_router(task_router)
        app.include_router(annotation_router)
        app.include_router(dashboard_router)
        app.include_router(admin_router)
        app.include_router(profile_router)

    def _register_static(self, app: FastAPI) -> None:
        self._mount_main_static(app)
        self._mount_assess_static(app)
        self._mount_user_static(app)
        self._mount_page_static(app)

    def _mount_main_static(self, app: FastAPI) -> None:
        app.mount(
            "/static_assess",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "main")),
            name="static",
        )
        app.mount(
            "/assess/common",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "common"), html=True),
            name="common",
        )

    def _mount_assess_static(self, app: FastAPI) -> None:
        config = get_config()
        for code, meta in FEATURE_META.items():
            cfg = config.feature_config(code)
            if cfg is None or not cfg.enabled:
                continue
            app.mount(
                f"/assess/{meta['path']}",
                StaticFiles(directory=os.path.join(STATIC_FILES_PATH, meta['path']), html=True),
                name="static",
            )

    def _mount_user_static(self, app: FastAPI) -> None:
        app.mount(
            "/assess/users/register",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "register"), html=True),
            name="static",
        )
        app.mount(
            "/assess/users/auth",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "login"), html=True),
            name="static",
        )
        app.mount(
            "/assess/users/confirm_email",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "email_confirm"), html=True),
            name="static",
        )

    def _mount_page_static(self, app: FastAPI) -> None:
        app.mount(
            "/static_tasks",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "tasks")),
            name="static",
        )
        app.mount(
            "/static_annotations",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "annotations")),
            name="static",
        )
        app.mount(
            "/static_dashboard",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "dashboard")),
            name="static",
        )
        app.mount(
            "/static_profile",
            StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "profile")),
            name="static",
        )


def is_api_request(request: Request) -> bool:
    accept_header = request.headers.get("accept", "").lower()
    api_keywords = ["application/json"]
    if any(keyword in accept_header for keyword in api_keywords):
        return True

    content_type = request.headers.get("content-type", "").lower()
    if any(keyword in content_type for keyword in api_keywords):
        return True

    api_header = ["x-api-key", "authorization", "api-key"]
    for header in api_header:
        if header in request.headers:
            return True

    return False


def _log_unhandled_exception(request: Request, exc: Exception) -> None:
    import traceback

    logger = structlog.get_logger()
    logger.error(
        f"Unhandled exception for request: {request.url}",
        error_message=str(exc),
        trace=traceback.extract_tb(exc.__traceback__),
    )


def run_app(app, host, port):
    import uvicorn

    set_log_level(level=LOG_LEVELS['INFO'])
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None,
        proxy_headers=True,
        forwarded_allow_ips='*',
    )