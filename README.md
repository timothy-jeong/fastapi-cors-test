# Custom CORSMiddleware for Exception Handling in FastAPI

## Overview

In FastAPI applications, I discovered that the built-in Starlette CORSMiddleware (the same as `fastapi.middleware.cors.CORSMiddleware`) does not always attach the expected CORS headers when custom exceptions occur. This can cause issues for clients accessing the API from different origins. To address this, I created a `CustomCORSMiddleware` that properly adds CORS headers even when an exception is raised during request processing.

*Note: This repository is intended solely to share these findings and is not meant to propose a new library or additional specifications for FastAPI.*

## Why I Conducted These Tests

The tests were initiated to isolate and fix an issue where error responses—both from general exceptions and HTTP-specific exceptions—were missing CORS headers. Since proper CORS handling is critical for cross-origin requests (especially in production environments), it is essential to ensure that even exception responses include the correct CORS headers. Our testing covers a range of scenarios, including:
- Normal responses.
- Exceptions thrown directly from endpoints.
- Exceptions raised within dependency functions.

## Exposed Endpoints

The application defines several endpoints to cover different response cases:

- **`/health`**  
  - **Purpose:** Returns a normal healthy response.  
  - **Description:** This endpoint confirms that standard responses correctly include the CORS headers set by the middleware.

- **`/exception`**  
  - **Purpose:** Triggers a general Python exception.  
  - **Description:** This endpoint tests how the application handles unexpected errors. The global exception handler should catch the error and return a JSON response with the proper CORS headers.

- **`/exception/http`**  
  - **Purpose:** Raises an HTTPException.  
  - **Description:** This endpoint tests the handling of HTTP-specific exceptions. The response is processed by the global exception handler and should include the CORS headers.

- **`/exception/depend`**  
  - **Purpose:** Raises an exception within a dependency function.  
  - **Description:** This endpoint verifies that exceptions raised in dependency functions are handled by the global exception handler and that the resulting error response contains the necessary CORS headers.

- **`/exception/http/depend`**  
  - **Purpose:** Raises an HTTPException within a dependency function.  
  - **Description:** This endpoint checks that HTTPExceptions thrown by dependencies are caught and returned with proper CORS headers attached.

## Test Code

The test suite is designed to verify that:
- Normal responses include the CORS headers.
- Error responses triggered by general exceptions (non-HTTPException) behave differently depending on the middleware:
  - **Default Starlette CORSMiddleware:** Error responses lack CORS headers.
  - **CustomCORSMiddleware:** Error responses include the correct CORS headers.
- HTTPException responses consistently include the proper CORS headers in both the default and custom middleware cases.

The tests are parameterized to run against both middleware implementations. A custom attribute is attached to the TestClient instance to distinguish which middleware is being used, so that assertions can be adjusted accordingly.

## CustomCORSMiddleware Implementation Details

The `CustomCORSMiddleware` extends the built-in Starlette CORSMiddleware to overcome the limitation of missing CORS headers on error responses. Key implementation details include:

- **ASGI Message Interception:**  
  The middleware intercepts the ASGI `send` function by wrapping it in a `send_wrapper` closure. This wrapper checks for messages of type `http.response.start` (which includes the headers) and injects the CORS headers before passing the message on.

- **Preflight Request Handling:**  
  The middleware checks if the request is a preflight (OPTIONS) request. If so, it immediately generates a preflight response with the correct CORS headers, bypassing the main application.

- **Exception Handling:**  
  Within a `try/except` block, if an exception is raised during request processing, the middleware:
  - Logs the exception.
  - Creates a JSON response (using `JSONResponse`) with a custom error message.
  - Manually attaches the CORS headers (using the defined `self.simple_headers` and helper method `allow_explicit_origin`) to the error response.
  - Sends this response so that even error responses include the correct CORS headers.

- **Header Injection Logic:**  
  The middleware uses helper methods (such as `allow_explicit_origin`) to determine whether to mirror the request’s `Origin` header or use a wildcard (`*`). This ensures that if a cookie is present or specific origin matching is required, the correct header is applied.

## Usage

### Running the Application

1. Install the necessary dependencies.
    ```bash
    pip install -r requirements.txt
    ```

2. choose user cors middleware at main.py </br>
You can choose between the built-in `StarletteCORSMiddleware` or the custom one (`CustomCORSMiddleware`). For example:

    ```python
    from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
    from app.middleware.cors import CORSMiddleware as CustomCORSMiddleware

    app.add_middleware(
        StarletteCORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

3. Start the FastAPI server using Uvicorn:
   ```bash
   uvicorn main:app --reload
    ```

4. send API request with Origin Header<br/>
you can observe /exception and /exception/depend are doesn't work as expected
    ```bash
    curl -i -X GET -H "Origin: https://google.com" http://127.0.0.1:8000/health

    curl -i -X GET -H "Origin: https://google.com" http://127.0.0.1:8000/exception

    curl -i -X GET -H "Origin: https://google.com" http://127.0.0.1:8000/exception/http

    curl -i -X GET -H "Origin: https://google.com" http://127.0.0.1:8000/exception/depend

    curl -i -X GET -H "Origin: https://google.com" http://127.0.0.1:8000/exception/http/depend 
    ```

5. run test code (optional)
    ```
    pytest
    ```