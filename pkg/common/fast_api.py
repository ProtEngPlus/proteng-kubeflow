from collections.abc import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute


def GetLoggingRouteClass(logger):
    class CustomRoute(APIRoute):
        def get_route_handler(self) -> Callable:
            original_route_handler = super().get_route_handler()

            async def custom_route_handler(request: Request) -> Response:
                body = await request.body()
                logger.info(
                    f"method={request.method} path={request.url.path} headers={request.headers} body={body.decode('utf-8')} query_params={request.query_params}"
                )
                response: Response = await original_route_handler(request)
                return response

            return custom_route_handler

    return CustomRoute
