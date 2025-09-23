from os import getenv, makedirs
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from agents.applicant_evaluator.app.core.config import settings
from agents.applicant_evaluator.app.core.logging import configure_logging, CorrelationIdMiddleware
from agents.applicant_evaluator.app.api.versioning import api_prefix
from agents.applicant_evaluator.app.api.routes import auth, applicants, loans, evaluations, health, stats
from agents.applicant_evaluator.app.db.session import init_db
from agents.applicant_evaluator.app.utils.tracing import setup_tracing

# ---- Environment
DEV = getenv("ENV", settings().ENV).lower() in {"dev", "local", "development"}

# ---- Logging & Tracing
configure_logging()
if settings().ENABLE_OTEL:
    setup_tracing()

# ---- FastAPI app
app = FastAPI(
    title=settings().API_TITLE,
    version=settings().API_VERSION,
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Location", "Idempotency-Key"],
)

# ---- Correlation ID logging middleware
app.add_middleware(CorrelationIdMiddleware)

# ---- Prometheus metrics (text exposition)
if settings().PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(
        app,
        include_in_schema=False,
        endpoint=f"{api_prefix()}/metrics",
    )

# ---- Startup
@app.on_event("startup")
def on_startup() -> None:
    init_db()
    # ensure score_store dir exists for JSON bundles written by save_bundle()
    try:
        makedirs(settings().SCORE_STORE_DIR, exist_ok=True)
    except Exception:
        # non-fatal; will surface on first write if path is bad
        pass

    if settings().SEED_ON_START:
        from agents.applicant_evaluator.app.seed_data import run_seed
        run_seed()

# ---- Security headers middleware
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data:"
    )
    return response

# ---- Routers
app.include_router(health.router,      prefix=api_prefix())
app.include_router(auth.router,        prefix=api_prefix())
app.include_router(applicants.router,  prefix=api_prefix())
app.include_router(loans.router,       prefix=api_prefix())
app.include_router(evaluations.router, prefix=api_prefix())
app.include_router(stats.router,       prefix=api_prefix())