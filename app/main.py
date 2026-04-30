
"""Main FastAPI application"""
from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.chat import router as chat_router
from app.routes.agent import router as agent_router
from app.routes.tools import router as tools_router
from app.routes.documents import router as documents_router
from app.routes.query import router as query_router
from app.routes.workflow import router as workflow_router
from app.routes.session import router as session_router
from app.tools.tool_registry import tool_registry
from app.tools.example_tools import CalculatorTool, TextAnalyzerTool
from app.tools.api_caller_tool import ApiCallerTool
from app.tools.document_query_tool import DocumentQueryTool
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Agent Backend API", "version": "1.0.0"}
