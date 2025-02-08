import logging

from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import Message, Send

from app import CommonResponse

logger = logging.getLogger(__name__)

class CORSMiddleware(StarletteCORSMiddleware):
    async def __call__(self, scope, receive, send):
        # If the scope type is not "http", simply call the app.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        headers = Headers(scope=scope)
        origin = headers.get("origin")

        if origin is None:
            await self.app(scope, receive, send)
            return
        # Handle preflight requests.
        if method == "OPTIONS" and "access-control-request-method" in headers:
            response = self.preflight_response(request_headers=headers)
            await response(scope, receive, send)
            return
        
        # Define a send_wrapper closure (capturing headers and origin).
        async def send_wrapper(message: Message) -> Send:
            """
            Additional implementation code.
            """
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                mutable_headers = MutableHeaders(scope=message)
                mutable_headers.update(self.simple_headers)
                if self.allow_all_origins and "cookie" in headers:
                    self.allow_explicit_origin(mutable_headers, origin)
                elif not self.allow_all_origins and self.is_allowed_origin(origin):
                    self.allow_explicit_origin(mutable_headers, origin)
            await send(message)

        # Wrap the send() call to add CORS headers to the actual response.
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            logger.exception(exc)
            response = JSONResponse(
                status_code=500,
                content=CommonResponse(message="error!!").model_dump()
            )

            # When an exception occurs, create a response similar to that returned
            # by the exception handler and add the CORS headers.
            for key, value in self.simple_headers.items():
                response.headers[key] = value
            if self.allow_all_origins and "cookie" in headers:
                self.allow_explicit_origin(response.headers, origin)
            elif not self.allow_all_origins and self.is_allowed_origin(origin):
                self.allow_explicit_origin(response.headers, origin)
            await response(scope, receive, send)
