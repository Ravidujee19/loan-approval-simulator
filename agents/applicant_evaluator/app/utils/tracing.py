 # OpenTelemetry (toggle via env)
 
def setup_tracing() -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from agents.applicant_evaluator.app.db.session import _engine

        FastAPIInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument(engine=_engine.sync_engine)  # type: ignore[attr-defined]
    except Exception:
        pass
