from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from engine import EnsembleEngine
import uvicorn

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize engine with local model disabled by default (API first)
engine = EnsembleEngine(use_local_model=False)

# Global config for toggling mode
app_config = {
    "use_local_model": False,
    "auto_fallback": True  # Always fallback to local model if API fails
}

class AnalysisRequest(BaseModel):
    claim: str
    use_local: Optional[bool] = None  # Optional per-request override

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/analyze")
async def analyze_claim_endpoint(req: AnalysisRequest):
    """Analyze claim using configured engine (API or local model)."""
    # Use per-request override if provided, otherwise use global config
    use_local = req.use_local if req.use_local is not None else app_config["use_local_model"]
    print(f"[ANALYZE] Claim: '{req.claim}' | use_local param: {req.use_local} | Final use_local: {use_local}")
    result = await engine.analyze_claim(req.claim, use_local=use_local)
    print(f"[RESULT] Engine: {result.get('engine')} | Verdict: {result.get('verdict')}")
    return result

@app.get("/config")
async def get_config():
    """Get current engine configuration."""
    return {
        "use_local_model": app_config["use_local_model"],
        "auto_fallback": app_config["auto_fallback"],
        "local_model_available": engine.local_model is not None,
        "vectorizer_available": engine.vectorizer is not None
    }

@app.post("/config/toggle")
async def toggle_mode(use_local: bool = None):
    """Toggle between API and local model."""
    if use_local is not None:
        app_config["use_local_model"] = use_local
        engine.use_local_model = use_local
        mode = "Local Model" if use_local else "API (Gemini)"
        return {
            "status": "success",
            "message": f"Switched to {mode}",
            "use_local_model": app_config["use_local_model"]
        }
    return {
        "status": "error",
        "message": "use_local parameter required"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
