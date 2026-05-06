
"""Main FastAPI application"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.routes.agent import router as agent_router
from app.routes.tools import router as tools_router
from app.routes.documents import router as documents_router
from app.routes.query import router as query_router
from app.routes.workflow import router as workflow_router
from app.routes.session import router as session_router
from app.routes.trace import router as trace_router
from app.tools.tool_registry import tool_registry
from app.tools.example_tools import CalculatorTool, TextAnalyzerTool
from app.tools.api_caller_tool import ApiCallerTool
from app.tools.document_query_tool import DocumentQueryTool
from app.utils.error_handlers import (
    AppException,
    exception_to_response,
    create_error_response,
    ErrorCode,
    ErrorCategory,
    log_error
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Agent Backend",
    description="Backend service for AI agents with tool orchestration",
    version="1.0.0"
)


# Global exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Global handler for custom AppException errors
    
    Converts AppException to structured JSON response
    """
    log_error(exc, context={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors
    
    Converts validation errors to structured format
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            error_code=ErrorCode.INVALID_INPUT,
            message="Request validation failed",
            category=ErrorCategory.VALIDATION,
            details={
                "validation_errors": exc.errors(),
                "body": str(exc.body) if hasattr(exc, "body") else None
            }
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions
    
    Logs error and returns generic error response
    """
    log_error(exc, context={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=500,
        content=exception_to_response(exc)
    )


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AI Agent Backend...")
    
    # Register tools
    calculator = CalculatorTool()
    text_analyzer = TextAnalyzerTool()
    api_caller = ApiCallerTool()
    document_query = DocumentQueryTool()
    
    tool_registry.register(calculator)
    tool_registry.register(text_analyzer)
    tool_registry.register(api_caller)
    tool_registry.register(document_query)
    
    logger.info(f"Registered {len(tool_registry.list_tool_names())} tools")
    logger.info("AI Agent Backend started successfully")


# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(agent_router, tags=["Agent"])
app.include_router(tools_router, tags=["Tools"])
app.include_router(documents_router, tags=["Documents"])
app.include_router(query_router, tags=["Query"])
app.include_router(workflow_router, tags=["Workflow"])
app.include_router(session_router, tags=["Session"])
app.include_router(trace_router, tags=["Trace"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Agent Backend API", "version": "1.0.0"}
