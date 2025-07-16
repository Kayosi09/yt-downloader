from fastapi import FastAPI, Request, HTTPException, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from uuid import uuid4
from pydantic import BaseModel, HttpUrl
import subprocess
import shutil
import os

app = FastAPI(title="1Downloader API")

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Rate Limiter ===
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)


# === Data Model ===
class DownloadRequest(BaseModel):
    url: HttpUrl
    format: str = "best"

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# === API Routes ===

@app.post("/api/download")
@limiter.limit("5/minute")
async def download_video(request: Request, data: DownloadRequest):
    file_id = str(uuid4())
    output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    try:
        cmd = [
            "yt-dlp",
            "-f", data.format,
            "-o", output_path,
            data.url
        ]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Download failed.")

    # Find the actual downloaded file
    for file in os.listdir(DOWNLOAD_DIR):
        if file.startswith(file_id):
            return {"file": file}
    
    raise HTTPException(status_code=404, detail="File not found.")


@app.get("/api/download/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found.")


@app.get("/api/status")
def status():
    return {"status": "Server running"}


# === Cleanup Function (for cron job) ===
@app.get("/api/cleanup")
def cleanup():
    removed = 0
    for file in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, file)
        try:
            os.remove(file_path)
            removed += 1
        except Exception:
            continue
    return {"removed_files": removed}
