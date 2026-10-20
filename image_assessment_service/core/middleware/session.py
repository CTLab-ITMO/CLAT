from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid


class SessionMiddleware(BaseHTTPMiddleware):
    """Simple session middleware that adds session_id cookie"""

    def __init__(self, app, session_cookie_name: str = "session_id"):
        super().__init__(app)
        self.session_cookie_name = session_cookie_name

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get(self.session_cookie_name)

        if not session_id:
            session_id = str(uuid.uuid4())

        request.state.session_id = session_id

        response = await call_next(request)

        if not request.cookies.get(self.session_cookie_name):
            response.set_cookie(
                key=self.session_cookie_name,
                value=session_id,
                httponly=False,
                secure=False,
                max_age=86400 * 30
            )

        return response