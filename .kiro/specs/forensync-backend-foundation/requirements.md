# Requirements Document

## Introduction

ForenSync is a digital forensics web application. This document specifies the requirements for the backend foundation — the structural, architectural, and operational layer that all future ForenSync features will be built on top of.

The backend is written in Python using Flask. It must support the Application Factory pattern, Flask Blueprints for modular routing, centralized configuration, environment-variable-driven settings, logging, global error handling, CORS for the React frontend, and a clean folder structure for REST API development.

No database models, authentication, parsers, or frontend code are in scope.

---

## Glossary

- **App**: The Flask application instance created by the Application Factory.
- **Application_Factory**: The `create_app()` function responsible for initializing and returning the configured Flask application.
- **Blueprint**: A Flask Blueprint object that groups a set of related routes and registers them with the App.
- **Config**: The centralized configuration object loaded from environment variables and `.env` files.
- **CORS_Handler**: The Flask-CORS extension instance attached to the App.
- **Error_Handler**: The global error-handling layer registered on the App that intercepts unhandled exceptions and HTTP errors.
- **Logger**: The application-level logging instance configured during App initialization.
- **Response_Formatter**: A reusable utility function that produces standardized JSON API responses.
- **Health_Blueprint**: The Blueprint exposing a `/health` endpoint for uptime checks.
- **Upload_Blueprint**: The Blueprint exposing file-upload endpoints (stub only in this phase).
- **dotenv**: The python-dotenv library used to load `.env` files into environment variables.

---

## Requirements

### Requirement 1: Application Factory

**User Story:** As a backend developer, I want the Flask app to be initialized through an Application Factory, so that the app is configurable, testable, and reusable across environments.

#### Acceptance Criteria

1. THE Application_Factory SHALL expose a `create_app(config_name: str = "default")` function that returns a fully initialized Flask App instance.
2. WHEN `create_app()` is called, THE Application_Factory SHALL load the Config object matching the given `config_name`.
3. WHEN `create_app()` is called, THE Application_Factory SHALL register all Blueprints with the App before returning it.
4. WHEN `create_app()` is called, THE Application_Factory SHALL initialize the CORS_Handler on the App.
5. WHEN `create_app()` is called, THE Application_Factory SHALL configure the Logger on the App.
6. WHEN `create_app()` is called, THE Application_Factory SHALL register all global error handlers on the App.
7. THE Application_Factory SHALL NOT import or initialize any database, ORM, or authentication extension.

---

### Requirement 2: Centralized Configuration

**User Story:** As a backend developer, I want all configuration values to be defined in one place and driven by environment variables, so that the app behaves correctly across development, testing, and production environments without code changes.

#### Acceptance Criteria

1. THE Config SHALL define at minimum the following settings: `SECRET_KEY`, `DEBUG`, `TESTING`, `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH`, and `ALLOWED_EXTENSIONS`.
2. THE Config SHALL load `SECRET_KEY` from the `SECRET_KEY` environment variable with no hardcoded fallback value in non-development configurations.
3. WHEN the `FLASK_ENV` environment variable is set to `"development"`, THE Config SHALL enable `DEBUG` mode.
4. WHEN the `FLASK_ENV` environment variable is set to `"production"`, THE Config SHALL disable `DEBUG` mode and enforce stricter settings.
5. THE Config SHALL expose a `from_env()` or equivalent class method that returns the correct Config subclass based on the current environment.
6. THE Config SHALL define `UPLOAD_FOLDER` as a path pointing to the `uploads/` directory within the Backend folder.
7. WHERE `MAX_CONTENT_LENGTH` is configured, THE Config SHALL set a default maximum upload size of 50 MB.

---

### Requirement 3: Environment Variable Loading

**User Story:** As a backend developer, I want the application to load environment variables from a `.env` file, so that local development settings are isolated from the codebase and not committed to version control.

#### Acceptance Criteria

1. WHEN the App starts, THE Application_Factory SHALL invoke dotenv to load variables from a `.env` file located in the Backend root directory.
2. IF a `.env` file is not present, THEN THE Application_Factory SHALL continue initialization without error.
3. THE Config SHALL document all required and optional environment variables in a `.env.example` file.
4. THE Config SHALL read `FLASK_ENV`, `SECRET_KEY`, `CORS_ORIGINS`, and `UPLOAD_FOLDER` from environment variables.

---

### Requirement 4: CORS Configuration

**User Story:** As a backend developer, I want CORS to be configured centrally, so that the React frontend can make API calls to the Flask backend without browser security errors.

#### Acceptance Criteria

1. THE CORS_Handler SHALL be initialized with the Flask App via Flask-CORS.
2. THE CORS_Handler SHALL read allowed origins from the `CORS_ORIGINS` environment variable.
3. WHEN `CORS_ORIGINS` is not set, THE CORS_Handler SHALL default to allowing requests from `http://localhost:5173` (the default Vite dev server origin).
4. THE CORS_Handler SHALL support `GET`, `POST`, `PUT`, `DELETE`, and `OPTIONS` HTTP methods.
5. THE CORS_Handler SHALL allow the `Content-Type` and `Authorization` request headers.

---

### Requirement 5: Logging Setup

**User Story:** As a backend developer, I want structured, leveled logging configured at startup, so that I can observe application behavior and diagnose issues in all environments.

#### Acceptance Criteria

1. THE Logger SHALL be configured during App initialization before any request is handled.
2. WHEN `FLASK_ENV` is `"development"`, THE Logger SHALL output logs at `DEBUG` level to stdout.
3. WHEN `FLASK_ENV` is `"production"`, THE Logger SHALL output logs at `WARNING` level or above.
4. THE Logger SHALL use a log format that includes the timestamp, log level, module name, and message.
5. THE Application_Factory SHALL attach the Logger to the Flask App's `app.logger` so that all application code can use it uniformly.

---

### Requirement 6: Global Error Handling

**User Story:** As a backend developer, I want all unhandled errors to return structured JSON responses, so that the React frontend always receives a consistent, parseable error payload regardless of what went wrong.

#### Acceptance Criteria

1. THE Error_Handler SHALL intercept HTTP 400 (Bad Request) errors and return a JSON response with `status`, `error`, and `message` fields.
2. THE Error_Handler SHALL intercept HTTP 404 (Not Found) errors and return a JSON response with `status`, `error`, and `message` fields.
3. THE Error_Handler SHALL intercept HTTP 405 (Method Not Allowed) errors and return a JSON response with `status`, `error`, and `message` fields.
4. THE Error_Handler SHALL intercept HTTP 422 (Unprocessable Entity) errors and return a JSON response with `status`, `error`, and `message` fields.
5. THE Error_Handler SHALL intercept HTTP 500 (Internal Server Error) errors and return a JSON response with `status`, `error`, and `message` fields.
6. WHEN an unhandled Python exception reaches the Error_Handler, THE Error_Handler SHALL log the full stack trace using the Logger and return an HTTP 500 JSON response.
7. WHEN `FLASK_ENV` is `"production"`, THE Error_Handler SHALL return generic error messages that do not expose internal implementation details.
8. WHEN `FLASK_ENV` is `"development"`, THE Error_Handler SHALL include the exception message in the JSON response to aid debugging.

---

### Requirement 7: Standardized JSON Response Utility

**User Story:** As a backend developer, I want a reusable function for building JSON API responses, so that all endpoints return data in a consistent structure that the frontend can reliably parse.

#### Acceptance Criteria

1. THE Response_Formatter SHALL expose a `success_response(data, status_code=200)` function that returns a Flask `Response` object with a JSON body containing `status`, `data`, and `message` fields.
2. THE Response_Formatter SHALL expose an `error_response(message, status_code, errors=None)` function that returns a Flask `Response` object with a JSON body containing `status`, `error`, and `message` fields.
3. THE Response_Formatter SHALL set the `Content-Type` header to `application/json` on all responses it produces.
4. WHEN `errors` is provided to `error_response`, THE Response_Formatter SHALL include the `errors` field in the JSON body.

---

### Requirement 8: Blueprint-Based Routing Structure

**User Story:** As a backend developer, I want routes organized into Flask Blueprints, so that each feature area can be developed, tested, and maintained independently without polluting a single routes file.

#### Acceptance Criteria

1. THE App SHALL register each Blueprint under a versioned URL prefix of `/api/v1/<resource>`.
2. THE Health_Blueprint SHALL register a `GET /api/v1/health` endpoint that returns the App status, environment, and version as a JSON response using the Response_Formatter.
3. THE Upload_Blueprint SHALL register a stub `POST /api/v1/upload` endpoint that returns an HTTP 501 (Not Implemented) response using the Response_Formatter.
4. WHEN a Blueprint is registered, THE Application_Factory SHALL import it from its dedicated module within the `routes/` directory.
5. THE App SHALL support adding new Blueprints by creating a new module in `routes/` and registering it in the Application_Factory without modifying any existing route files.

---

### Requirement 9: REST API Folder Structure

**User Story:** As a backend developer, I want the project files organized into a clear, conventional folder structure, so that any developer can navigate the codebase and understand where to add new functionality.

#### Acceptance Criteria

1. THE App SHALL organize source code into the following top-level directories under `Backend/`: `routes/`, `services/`, `utils/`, `parsers/`, `models/`, `uploads/`, and `tests/`.
2. THE App SHALL place the Application_Factory in `Backend/app.py`.
3. THE App SHALL place the Config in `Backend/config.py`.
4. THE App SHALL place all Blueprint modules in `Backend/routes/`, one file per Blueprint.
5. THE App SHALL place all reusable utility functions, including the Response_Formatter, in `Backend/utils/`.
6. THE App SHALL provide a `Backend/run.py` entry point script that calls `create_app()` and starts the development server.
7. THE App SHALL provide a `Backend/.env.example` file listing all environment variables the application reads.

---

### Requirement 10: Entry Point and Startup

**User Story:** As a backend developer, I want a single entry point script to start the server, so that the startup process is explicit, reproducible, and does not rely on Flask's default discovery behavior.

#### Acceptance Criteria

1. THE App SHALL expose a `run.py` file at the Backend root that imports `create_app` and calls `app.run()` with host, port, and debug values read from Config.
2. WHEN `run.py` is executed directly, THE App SHALL start the Flask development server.
3. THE App SHALL support being started via `flask run` using the `FLASK_APP=run.py` environment variable as an alternative startup method.
