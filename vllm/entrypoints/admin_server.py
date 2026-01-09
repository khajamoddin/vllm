import asyncio
from typing import Optional
from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from vllm.engine.protocol import EngineClient
from vllm.entrypoints.openai.serving_models import OpenAIServingModels

def build_admin_app(args) -> FastAPI:
    app = FastAPI(
        title="vLLM Admin API",
        description="Admin control plane for vLLM",
        version="0.1.0",
        docs_url="/docs" if not args.disable_fastapi_docs else None,
        redoc_url="/redoc" if not args.disable_fastapi_docs else None,
    )

    @app.get("/v1/admin/health")
    async def health(request: Request):
        """Health check endpoint."""
        engine_client: EngineClient = request.app.state.engine_client
        try:
            await engine_client.check_health()
            return JSONResponse(status_code=HTTPStatus.OK, content={"status": "healthy"})
        except Exception as e:
             return JSONResponse(status_code=HTTPStatus.SERVICE_UNAVAILABLE, content={"status": "unhealthy", "detail": str(e)})

    @app.get("/v1/admin/models")
    async def show_available_models(request: Request):
        """Show available models."""
        # reusing the existing model handler if available in state, 
        # otherwise we might need to inspect engine_client.
        # Ideally, we share the OpenAIServingModels instance.
        if hasattr(request.app.state, "openai_serving_models"):
             models_handler: OpenAIServingModels = request.app.state.openai_serving_models
             models = await models_handler.show_available_models()
             return JSONResponse(content=models.model_dump())
        else:
             # Fallback if we cannot access high-level serving model logic
             # But the admin server is launched alongside the openAI server usually
             return JSONResponse(status_code=HTTPStatus.NOT_IMPLEMENTED, content={"detail": "Model information not available"})

    @app.get("/v1/admin/queue")
    async def queue_stats(request: Request):
        """Get queue stats."""
        # Try to retrieve server load metrics if available
        if hasattr(request.app.state, "server_load_metrics"):
             return JSONResponse(content={"server_load": request.app.state.server_load_metrics})
        
        # Fallback or empty if not tracking
        return JSONResponse(status_code=HTTPStatus.OK, content={"detail": "Queue stats not currently tracked if server_load_metrics is disabled"})

    @app.post("/v1/admin/drain")
    async def drain(request: Request):
        """Drain the server (pause generation)."""
        engine_client: EngineClient = request.app.state.engine_client
        try:
            # We wait for inflight requests to finish for a graceful drain
            await engine_client.pause_generation(wait_for_inflight_requests=True)
            return JSONResponse(status_code=HTTPStatus.OK, content={"status": "draining"})
        except NotImplementedError:
             return JSONResponse(status_code=HTTPStatus.NOT_IMPLEMENTED, content={"detail": "Drain not supported by this engine"})
        except Exception as e:
             return JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content={"detail": str(e)})

    @app.post("/v1/admin/reload_model")
    async def reload_model(request: Request):
        """Reload the model."""
        # Not fully supported in EngineClient protocol for full model reload without restart
        # We can implement a limited version or return Not Implemented.
        # Given the FR says "optional / gated", we adhere to the contract by exposing it.
        return JSONResponse(status_code=HTTPStatus.NOT_IMPLEMENTED, content={"detail": "Model reload not yet implemented"})
        
    return app
