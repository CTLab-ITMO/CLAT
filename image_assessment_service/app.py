import structlog
from fastapi.staticfiles import StaticFiles
import os
import pathlib

from image_assessment_service.apis.image_filter_api import image_filter_api
from image_assessment_service.apis.classify_api import classify_api
from image_assessment_service.apis.tech_api import tech_api
from image_assessment_service.apis.aesth_api import aesth_api
from image_assessment_service.logger import set_log_level, LOG_LEVELS
from image_assessment_service.autorization.routers.csrf import router as csrf_router
from image_assessment_service.autorization.routers.users import router as user_router
from image_assessment_service.autorization.routers.items import router as item_router
from image_assessment_service.autorization.routers.tokens import router as tokens_router
from image_assessment_service.autorization.models.database import init_database, get_engine
from image_assessment_service.autorization.models import core
from image_assessment_service.apis.task_api import router as task_router
from image_assessment_service.apis.annotation_api import router as annotation_router
from image_assessment_service.apis.dashboard_api import router as dashboard_router
from image_assessment_service.apis.admin_api import router as admin_router
from image_assessment_service.apis.profile_api import router as profile_router
from image_assessment_service.apis.assess_api import router as assess_router
from image_assessment_service.dependencies import get_container
from image_assessment_service.core.middleware.session import SessionMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from .rate_limit import setup_rate_limiter

from dotenv import load_dotenv
load_dotenv()

CURRENT_PATH = pathlib.Path(__file__).resolve().parents[0]
STATIC_FILES_PATH = CURRENT_PATH / "static/"


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


def build_app() -> FastAPI:
    init_database()
    core.Base.metadata.create_all(bind=get_engine())

    app = FastAPI(title="Image Assessment Service")

    app.add_middleware(SessionMiddleware)
    setup_rate_limiter(app)

    @app.on_event("startup")
    async def startup_event():
        container = get_container()
        await container.data_uploader_service.start_cleanup_daemon()

    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, _: Exception):
        if is_api_request(request):
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Not found",
                    "path": str(request.url.path)
                }
            )
        return RedirectResponse(url="/assess/main", status_code=302)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        import traceback

        logger = structlog.get_logger()
        logger.error(
            f"Unhandled exception for request: {request.url}",
            error_message=str(exc),
            trace=traceback.extract_tb(exc.__traceback__)
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Unexpected server error."},
        )

    app.include_router(assess_router)
    app.mount("/static_assess", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "main")), name="static")

    app.mount("/assess/common", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "common"), html=True),
              name="common")

    app.include_router(classify_api, prefix='/assess/classify', tags=['API'])
    app.mount("/assess/classify", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "classify"), html=True),
              name="static")

    app.include_router(tech_api, prefix='/assess/tech', tags=['API'])
    app.mount("/assess/tech", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "tech"), html=True), name="static")

    app.include_router(image_filter_api, prefix='/assess/image_filter', tags=['API'])
    app.mount("/assess/image_filter", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "image_filter"), html=True),
              name="static")

    app.include_router(aesth_api, prefix='/assess/aesth', tags=['API'])
    app.mount("/assess/aesth", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "aesth"), html=True),
              name="static")

    app.include_router(item_router, prefix='/assess/items')

    app.include_router(csrf_router, prefix='/assess/csrf')
    app.include_router(user_router, prefix='/assess/users')
    app.mount("/assess/users/register", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "register"), html=True),
              name="static")
    app.mount("/assess/users/auth", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "login"), html=True),
              name="static")
    app.mount("/assess/users/confirm_email",
              StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "email_confirm"), html=True),
              name="static")

    app.include_router(tokens_router, prefix='/assess/tokens')

    app.include_router(task_router)
    app.include_router(annotation_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)
    app.include_router(profile_router)

    app.mount("/static_tasks", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "tasks")), name="static")
    app.mount("/static_annotations", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "annotations")),
              name="static")
    app.mount("/static_dashboard", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "dashboard")), name="static")
    app.mount("/static_profile", StaticFiles(directory=os.path.join(STATIC_FILES_PATH, "profile")), name="static")

    return app
