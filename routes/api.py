from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from services.project_service import start_generation, get_status, get_files

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_project(req: PromptRequest):
    run_id = await start_generation(req.prompt)
    return {"run_id": run_id, "message": "Generation started"}

@router.get("/status/{run_id}")
async def get_project_status(run_id: str):
    state = get_status(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "status": state["status"],
        "logs": state["logs"]
    }

@router.get("/files/{run_id}")
async def get_project_files(run_id: str):
    files = get_files(run_id)
    if not files:
        raise HTTPException(status_code=404, detail="Files not found")
    return {"files": files}

@router.get("/download/{run_id}")
async def download_project(run_id: str):
    zip_path = f"generated_projects/{run_id}.zip"
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP not found or generation incomplete")
    return FileResponse(zip_path, media_type="application/zip", filename=f"devteam_project_{run_id}.zip")

@router.get("/preview/{run_id}")
async def preview_code(run_id: str):
    files = get_files(run_id)
    if not files:
        raise HTTPException(status_code=404, detail="Files not found")
    # Return html preview or just list for frontend
    return {"files": files}
