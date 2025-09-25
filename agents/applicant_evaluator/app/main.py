from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from app.api.routes.applicant_eval import router as applicant_eval_router
from .api.routes.applicant_eval import router as applicant_eval_router
from .config import settings  

app = FastAPI(title="Applicant Evaluator (NLP + Rules)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applicant_eval_router)

@app.get("/api/v1/health/live")
def live():
    return {
        "status": "ok",
        "score_agent_url": settings().SCORE_AGENT_URL,
        "storage_dir": settings().STORAGE_DIR,
    }
