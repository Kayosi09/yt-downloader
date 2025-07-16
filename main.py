from fastapi import FastAPI, UploadFile, File, Form, WebSocket, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_login import LoginManager
import subprocess, asyncio, os, re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET = "super-secret"
manager = LoginManager(SECRET, token_url="/auth/login", use_cookie=True)
manager.cookie_name = "auth_token"

users = {"admin": {"password": "1234"}}

@manager.user_loader
def load_user(username: str):
    return users.get(username)

@app.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = load_user(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = manager.create_access_token(data={"sub": username})
    response = JSONResponse({"msg": "✅ Login successful"})
    manager.set_cookie(response, access_token)
    return response

@app.post("/api/upload-cookies")
async def upload_cookies(cookieFile: UploadFile = File(...), user=Depends(manager)):
    os.makedirs("cookies", exist_ok=True)
    path = f"cookies/{user['username']}_cookies.txt"
    with open(path, "wb") as f:
        f.write(await cookieFile.read())
    return {"message": "✅ Cookies uploaded"}

@app.post("/api/get-formats")
def get_formats(url: str = Form(...), user=Depends(manager)):
    cookie_path = f"cookies/{user['username']}_cookies.txt"
    cmd = ["yt-dlp", "--cookies", cookie_path, "-F", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=400, detail="Format fetch failed.")
    formats = []
    for line in result.stdout.splitlines():
        if re.match(r"^\d+", line):
            parts = line.split(None, 2)
            formats.append({
                "format_id": parts[0],
                "ext": parts[1],
                "note": parts[2] if len(parts) > 2 else ""
            })
    return {"formats": formats}

@app.websocket("/ws/download")
async def websocket_download(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        url = data["url"]
        fmt = data["format"]
        user = data["user"]

        cookie_path = f"cookies/{user}_cookies.txt"
        os.makedirs("downloads", exist_ok=True)

        cmd = [
            "yt-dlp",
            "--cookies", cookie_path,
            "-f", fmt,
            "-o", "downloads/%(title)s.%(ext)s",
            url
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        async for line in process.stdout:
            await websocket.send_text(line.decode().strip())

        await websocket.send_text("✅ Download Completed.")
        await websocket.close()

    except Exception as e:
        await websocket.send_text(f"❌ Error: {e}")
        await websocket.close()

@app.get("/api/download-file/{filename}")
def download_file(filename: str, user=Depends(manager)):
    filepath = f"downloads/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, filename=filename)
