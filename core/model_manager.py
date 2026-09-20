import os
import threading
from typing import Dict, Any, Callable, Optional

# Default models directory relative to project root
DEFAULT_MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

MODELS_INFO = {
    "fourier_math": {
        "id": "fourier_math",
        "name": "Fourier Frekans Faz Bozucu (FFT)",
        "size_mb": 0,
        "requires_download": False,
        "description_tr": "Saf matematiksel 2D Hızlı Fourier Dönüşümü. 16-32 px dalga boyundaki faz uyumunu bozar. Sıfır MB indirme, 0.1 sn işlem süresi.",
        "description_en": "Pure mathematical 2D FFT phase decorrelation. Scrambles 16-32 px annular phase coherence. 0 MB download, ~0.1s execution.",
        "recommended": False,
        "speed": "Çok Hızlı / Instant",
        "quality_score": "22-25 dB PSNR"
    },
    "vae_latent": {
        "id": "vae_latent",
        "name": "Stability AI SD-VAE-FT-MSE",
        "size_mb": 335,
        "requires_download": True,
        "repo_id": "stabilityai/sd-vae-ft-mse",
        "description_tr": "En yüksek görsel kaliteyi korur (29+ dB PSNR). Görseli 8x latent uzayına aktarıp kontrollü pertürbasyon uygular, pikselleri sıfırdan oluşturarak SynthID'yi tamamen düşürür.",
        "description_en": "Highest visual fidelity (29+ dB PSNR). Encodes into 8x latent space, applies calibrated perturbation, and reconstructs pixels to eliminate SynthID.",
        "recommended": True,
        "speed": "Hızlı (GPU: ~1s, CPU: ~5s)",
        "quality_score": "29-33 dB PSNR (Maksimum Netlik)"
    },
    "sparkle_reverse": {
        "id": "sparkle_reverse",
        "name": "Gemini Sparkle Ters Alpha Motoru",
        "size_mb": 0,
        "requires_download": False,
        "description_tr": "Gemini'in sag alt koseye bastigi gorunur yildiz/parilti logosunu ters alpha formulu ve Telea inpainting ile piksel dokusuna zarar vermeden yok eder.",
        "description_en": "Removes visible Gemini sparkle watermark at the bottom right using reverse alpha blending and Telea inpainting.",
        "recommended": True,
        "speed": "Anlik / Instant",
        "quality_score": "Kayipsiz / Lossless"
    }
}

# Download progress state tracking
_download_state: Dict[str, Any] = {
    "is_downloading": False,
    "model_id": "",
    "progress_pct": 0.0,
    "status_message": "",
    "error": None
}
_lock = threading.Lock()

def get_models_directory(custom_path: Optional[str] = None) -> str:
    path = custom_path or DEFAULT_MODELS_DIR
    os.makedirs(path, exist_ok=True)
    return path

def is_vae_available(models_dir: Optional[str] = None) -> bool:
    target_dir = get_models_directory(models_dir)
    vae_path = os.path.join(target_dir, "sd-vae-ft-mse")
    
    # Check if local folder has model files
    if os.path.exists(vae_path):
        has_config = os.path.exists(os.path.join(vae_path, "config.json"))
        has_weights = (
            os.path.exists(os.path.join(vae_path, "diffusion_pytorch_model.safetensors")) or
            os.path.exists(os.path.join(vae_path, "diffusion_pytorch_model.bin"))
        )
        if has_config and has_weights:
            return True
            
    # Also check HuggingFace global cache
    try:
        from huggingface_hub import try_to_load_from_cache
        res = try_to_load_from_cache("stabilityai/sd-vae-ft-mse", "config.json")
        if isinstance(res, str) and os.path.exists(res):
            return True
    except Exception:
        pass
        
    return False

def get_models_status(models_dir: Optional[str] = None) -> Dict[str, Any]:
    vae_ready = is_vae_available(models_dir)
    
    models = []
    for mid, info in MODELS_INFO.items():
        m_copy = dict(info)
        if mid == "vae_latent":
            m_copy["ready"] = vae_ready
        else:
            m_copy["ready"] = True
        models.append(m_copy)
        
    with _lock:
        download_info = dict(_download_state)
        
    return {
        "models_dir": get_models_directory(models_dir),
        "models": models,
        "download_state": download_info
    }

def download_vae_model(models_dir: Optional[str] = None, callback: Optional[Callable[[float, str], None]] = None) -> bool:
    global _download_state
    
    with _lock:
        if _download_state["is_downloading"]:
            return False
        _download_state["is_downloading"] = True
        _download_state["model_id"] = "vae_latent"
        _download_state["progress_pct"] = 0.0
        _download_state["status_message"] = "İndirme başlatılıyor..."
        _download_state["error"] = None

    def _worker():
        global _download_state
        try:
            target_dir = get_models_directory(models_dir)
            vae_dest = os.path.join(target_dir, "sd-vae-ft-mse")
            os.makedirs(vae_dest, exist_ok=True)
            
            with _lock:
                _download_state["status_message"] = "HuggingFace üzerinden SD-VAE modeli indiriliyor (~335 MB)..."
                _download_state["progress_pct"] = 15.0
            
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id="stabilityai/sd-vae-ft-mse",
                local_dir=vae_dest,
                local_dir_use_symlinks=False,
                ignore_patterns=["*.msgpack", "*.h5"]
            )
            
            with _lock:
                _download_state["is_downloading"] = False
                _download_state["progress_pct"] = 100.0
                _download_state["status_message"] = "Model başarıyla indirildi ve hazır!"
                
            if callback:
                callback(100.0, "Tamamlandı")
                
        except Exception as e:
            with _lock:
                _download_state["is_downloading"] = False
                _download_state["error"] = str(e)
                _download_state["status_message"] = f"Hata: {str(e)}"
            if callback:
                callback(-1.0, str(e))

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return True
