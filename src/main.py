"""MiMo Recruitment Engine — FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from .database import init_db
from .kernel import AgentKernel
from .agents.parse_agent import ParseAgent
from .agents.match_agent import MatchAgent
from .agents.score_agent import ScoreAgent
from .agents.question_agent import QuestionAgent
from .agents.evaluate_agent import EvaluateAgent
from .agents.compare_agent import CompareAgent
from .agents.report_agent import ReportAgent
from .api.routes import router, set_kernel
from .api.websocket import websocket_endpoint
from .mimo.client import close_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("mimo")

kernel = AgentKernel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info("Starting MiMo Recruitment Engine...")
    await init_db()

    # Register all agents
    kernel.register(ParseAgent())
    kernel.register(MatchAgent())
    kernel.register(ScoreAgent())
    kernel.register(QuestionAgent())
    kernel.register(EvaluateAgent())
    kernel.register(CompareAgent())
    kernel.register(ReportAgent())

    await kernel.start()
    set_kernel(kernel)
    logger.info(f"Kernel ready with {len(kernel._agents)} agents")

    yield

    logger.info("Shutting down MiMo Recruitment Engine...")
    await kernel.shutdown()
    await close_client()


app = FastAPI(
    title="MiMo Recruitment Engine",
    description="AI-Powered Recruitment Pipeline with 7 Coordinated Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Routes
app.include_router(router)
app.add_api_websocket_route("/ws", websocket_endpoint)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard."""
    template_path = Path(__file__).parent.parent / "templates" / "dashboard.html"
    return template_path.read_text(encoding="utf-8")
