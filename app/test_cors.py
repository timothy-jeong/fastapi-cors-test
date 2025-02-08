import pytest
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import ORJSONResponse
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware

# Import CustomCORSMiddleware (adjust the import path as necessary)
from app.middleware.cors import CORSMiddleware as CustomCORSMiddleware
from app import CommonResponse
from app import general_exception_handler

ORIGIN_HEADER = {"Origin": "https://google.com"}
CORS_RESPONSE_HEADER = "access-control-allow-origin"

def create_app(middleware_class):
    """
    Create a FastAPI app with the given CORS middleware.
    """
    app = FastAPI(default_response_class=ORJSONResponse)

    # Add the specified CORS middleware
    app.add_middleware(
        middleware_class,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ###################
    # Normal endpoint #
    ###################
    @app.get("/health", response_model=CommonResponse)
    async def is_health():
        return CommonResponse(message="I'm healthy!")

    #############################
    # Exception endpoints       #
    #############################
    @app.get("/exception", response_model=CommonResponse)
    async def throws_exception():
        raise Exception("General exception occurred!")

    @app.get("/exception/http", response_model=CommonResponse)
    async def throws_http_exception():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="HTTPException occurred!"
        )

    ###########################################
    # Exception in dependency (general case)  #
    ###########################################
    async def dependency_exception() -> str:
        raise Exception("Exception raised in dependency!")
    
    @app.get("/exception/depend", response_model=CommonResponse)
    async def throws_exception_in_depend(the_thing: str = Depends(dependency_exception)):
        return CommonResponse(message="You should never see this")

    ###############################################
    # Exception in dependency (HTTPException case)#
    ###############################################
    async def dependency_exception_http() -> str:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="HTTPException in dependency!"
        )
    
    @app.get("/exception/http/depend", response_model=CommonResponse)
    async def throws_exception_in_depend_http(the_thing: str = Depends(dependency_exception_http)):
        return CommonResponse(message="You should never see this either")

    app.add_exception_handler(Exception, general_exception_handler)

    return app

# Create a pytest fixture that parameterizes the middleware used by the app.
@pytest.fixture(params=[
    pytest.param(StarletteCORSMiddleware, id="default"),
    pytest.param(CustomCORSMiddleware, id="custom")
])
def client(request) -> TestClient:
    middleware_class = request.param
    app = create_app(middleware_class)
    # Prevent re-raising exceptions so that the exception handler's response is returned.
    client_instance = TestClient(app, raise_server_exceptions=False)
    # Attach the middleware type to the TestClient instance.
    client_instance.middleware_type = request.node.callspec.id  # "default" or "custom"
    return client_instance

###############
# Test Cases#
###############

def test_health(client: TestClient):
    """
    Test the /health endpoint to verify that a normal response includes CORS headers.
    """
    response = client.get("/health", headers=ORIGIN_HEADER)
    assert response.status_code == 200
    # Verify that the CORS header is present.
    assert response.headers.get(CORS_RESPONSE_HEADER) is not None

def test_http_exception(client: TestClient):
    """
    Test the /exception/http endpoint to verify that HTTPExceptions include CORS headers.
    """
    response = client.get("/exception/http", headers=ORIGIN_HEADER)
    # We expect a 500 error and the CORS header to be present.
    assert response.status_code == 500
    assert response.headers.get(CORS_RESPONSE_HEADER) is not None

def test_http_exception_in_dependency(client: TestClient):
    """
    Test that HTTPExceptions raised in dependency functions are caught and that
    the resulting error responses include CORS headers.
    """
    response = client.get("/exception/http/depend", headers=ORIGIN_HEADER)
    assert response.status_code == 500
    assert response.headers.get(CORS_RESPONSE_HEADER) is not None

def test_exception(client: TestClient):
    """
    Test the /exception endpoint to verify that error responses (general exceptions)
    behave as expected:
        - For default middleware: no CORS header.
        - For custom middleware: CORS header is present.
    """
    middleware_type = client.middleware_type
    response = client.get("/exception", headers=ORIGIN_HEADER)
    # Expect a 500 status code for general exceptions.
    assert response.status_code == 500

    if middleware_type == "default":
        # With default middleware, the CORS header is expected to be absent.
        assert response.headers.get(CORS_RESPONSE_HEADER) is None, (
            "Expected no CORS header for default middleware when a general exception occurs"
        )
    else:
        # With custom middleware, the CORS header should be present.
        assert response.headers.get(CORS_RESPONSE_HEADER) is not None, (
            "Expected CORS header for custom middleware when a general exception occurs"
        )
        
def test_exception_in_dependency(client: TestClient): 
    """
    Test that exceptions raised in dependency functions are caught and that
    the resulting error responses include CORS headers.
    """
    middleware_type = client.middleware_type
    response = client.get("/exception/depend", headers=ORIGIN_HEADER)
    # Expect a 500 status code for general exceptions.
    assert response.status_code == 500

    if middleware_type == "default":
        assert response.headers.get(CORS_RESPONSE_HEADER) is None, (
            "Expected no CORS header for default middleware when a general exception occurs"
        )
    else:
        assert response.headers.get(CORS_RESPONSE_HEADER) is not None, (
            "Expected CORS header for custom middleware when a general exception occurs"
        )
