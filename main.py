from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import yt_dlp
import uuid
import os

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Config — Change '*' to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Pydantic model for input validation
class DownloadRequest(BaseModel):
    url: HttpUrl
    format_id: str = None
    cookies: str = None

@app.post("/api/download")
@limiter.limit("5/minute")  # 5 requests per minute per IP
async def download_video(data: DownloadRequest):
    temp_id = str(uuid.uuid4())
    output_template = f"{DOWNLOAD_DIR}/{temp_id}-%(title)s.%(ext)s"

    ydl_opts = {
        'outtmpl': output_template,
        'format': data.format_id if data.format_id else 'best',
        'noplaylist': True,
        'quiet': True,
    }

    if data.cookies:
        with open("cookies.txt", "w") as f:
            f.write(data.cookies)
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=True)
            filename = ydl.prepare_filename(info)
        clean_filename = filename.replace(DOWNLOAD_DIR + "/", "")
        return {"status": "success", "file": clean_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
@limiter.limit("20/minute")  # Higher limit for file download
async def get_download(filename: str):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found.")
