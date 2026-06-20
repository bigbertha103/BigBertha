import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db, seed_agents
from backend.routers import agents, company, config, conversations, jobs

load_dotenv()

LOG_FILE = Path(__file__).parent / "data" / "bigbertha.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage Big Bertha — init DB + seed")
    init_db()
    seed_agents()
    yield
    logger.info("Arrêt Big Bertha")


app = FastAPI(title="Big Bertha API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(company.router, prefix="/api")
app.include_router(config.router, prefix="/api")

_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
