import os
import sys
import io
import cv2
import numpy as np
from datetime import datetime
import webbrowser
from threading import Timer

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.synthid_cleaner import SynthIDCleaner
from core.visible_remover import VisibleWatermarkRemover
from core.exif_injector import ExifInjector
from core.model_manager import (
    get_models_status,
    download_vae_model,
    is_vae_available,
    get_models_directory
)

app = FastAPI(title="Aethelon SynthID Remover", version="1.0.0")

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Shared cleaner instance
cleaner = SynthIDCleaner()

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Aethelon SynthID Remover</h1><p>static/index.html not found.</p>"

@app.get("/api/models/status")
async def api_models_status():
    return get_models_status()

class DownloadRequest(BaseModel):
    model_id: str

@app.post("/api/models/download")
async def api_download_model(req: DownloadRequest):
    if req.model_id == "vae_latent":
        success = download_vae_model()
        if not success:
            raise HTTPException(status_code=400, detail="Model indirme işlemi zaten devam ediyor.")
        return {"status": "started", "message": "İndirme arka planda başlatıldı."}
    return {"status": "skipped", "message": "Bu model indirme gerektirmez."}

@app.post("/api/clean")
async def api_clean_image(
    file: UploadFile = File(...),
    method: str = Form("vae"),
    noise_std: float = Form(0.15),
    remove_sparkle: bool = Form(True),
    exif_preset: str = Form("iphone12pro")
):
    try:
        # Read file bytes
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Geçersiz görsel formatı.")

        # 1. Step: Visible Watermark Removal (Sparkle)
        if remove_sparkle:
            img_bgr = VisibleWatermarkRemover.remove_corner_sparkle(img_bgr, corner="bottom-right")

        # 2. Step: SynthID Invisible Watermark Cleaning
        if method == "vae":
            # If VAE is not available, check or fallback
            if not is_vae_available():
                # Attempt to run via HuggingFace or fallback to Fourier
                try:
                    cleaned_bgr = cleaner.clean_vae_latent(img_bgr, noise_std=noise_std)
                except Exception as e:
                    print(f"VAE error, falling back to Fourier: {e}")
                    cleaned_bgr = cleaner.clean_fourier_annular(img_bgr)
            else:
                cleaned_bgr = cleaner.clean_vae_latent(img_bgr, noise_std=noise_std)
        elif method == "fourier":
            cleaned_bgr = cleaner.clean_fourier_annular(img_bgr)
        elif method == "hybrid":
            cleaned_bgr = cleaner.clean_hybrid_filter(img_bgr)
        else:
            cleaned_bgr = img_bgr

        # 3. Step: BGR -> RGB & Camera EXIF Injection
        img_rgb = cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_filename = f"clean_{timestamp}.jpg"
        out_filepath = os.path.join(OUTPUT_DIR, out_filename)

        ExifInjector.save_with_exif(
            img_rgb=img_rgb,
            output_path=out_filepath,
            preset=exif_preset,
            quality=95
        )

        return FileResponse(
            path=out_filepath,
            media_type="image/jpeg",
            filename=out_filename
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def open_browser():
    webbrowser.open("http://127.0.0.1:7860")

if __name__ == "__main__":
    port = 7860
    print("=" * 60)
    print("   Aethelon SynthID Remover Web Sunucusu Başlatılıyor...")
    print(f"   Arayüz Adresi: http://127.0.0.1:{port}")
    print("=" * 60)
    
    # Auto-open browser after 1.5 seconds
    Timer(1.5, open_browser).start()
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
