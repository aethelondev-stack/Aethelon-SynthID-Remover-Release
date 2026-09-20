import cv2
import numpy as np
from PIL import Image
import os
from typing import Optional, Tuple

class SynthIDCleaner:
    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir
        self._vae = None
        self._device = None

    def _get_device(self):
        if self._device is None:
            import torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    def _load_vae(self):
        if self._vae is not None:
            return self._vae

        import torch
        from diffusers import AutoencoderKL
        from .model_manager import get_models_directory

        models_dir = get_models_directory(self.models_dir)
        local_vae_path = os.path.join(models_dir, "sd-vae-ft-mse")
        model_id = local_vae_path if os.path.exists(local_vae_path) else "stabilityai/sd-vae-ft-mse"

        device = self._get_device()
        dtype = torch.float16 if device == "cuda" else torch.float32

        self._vae = AutoencoderKL.from_pretrained(model_id, torch_dtype=dtype).to(device)
        self._vae.eval()
        return self._vae

    def clean_vae_latent(self, img_bgr: np.ndarray, noise_std: float = 0.15, seed: int = 42) -> np.ndarray:
        """
        Cleans SynthID by encoding into VAE latent space, applying calibrated 
        perturbation, and decoding back to pixel space.
        """
        import torch

        vae = self._load_vae()
        device = self._get_device()
        scaling_factor = float(vae.config.scaling_factor)

        orig_h, orig_w = img_bgr.shape[:2]

        # VAE requires dimensions to be multiples of 8
        h = (orig_h // 8) * 8
        w = (orig_w // 8) * 8
        img_resized = cv2.resize(img_bgr, (w, h), interpolation=cv2.INTER_LANCZOS4)

        # BGR -> RGB -> [-1, 1]
        rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).unsqueeze(0)
        tensor = tensor.to(device=device, dtype=vae.dtype) / 127.5 - 1.0

        with torch.inference_mode():
            latents = vae.encode(tensor).latent_dist.mode() * scaling_factor

            # Perturbation
            generator = torch.Generator(device=device).manual_seed(seed)
            noise = torch.randn(latents.shape, generator=generator, device=device, dtype=vae.dtype)
            perturbed = latents + noise_std * noise

            decoded = vae.decode(perturbed / scaling_factor).sample
            decoded = ((decoded / 2.0 + 0.5).clamp(0.0, 1.0) * 255.0).round().to(torch.uint8)
            decoded = decoded.squeeze(0).permute(1, 2, 0).cpu().numpy()

            out_bgr = cv2.cvtColor(decoded, cv2.COLOR_RGB2BGR)
            out_orig = cv2.resize(out_bgr, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)
            return out_orig

    def clean_fourier_annular(self, img_bgr: np.ndarray, seed: int = 42) -> np.ndarray:
        """
        Cleans SynthID by scrambling the phase in the 16-32 px wavelength band (annulus)
        of the luminance (Y) channel in the 2D FFT domain, preserving magnitude.
        """
        orig_h, orig_w = img_bgr.shape[:2]

        ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)

        # 2D FFT
        f = np.fft.fft2(y)
        fshift = np.fft.fftshift(f)

        rows, cols = y.shape
        crow, ccol = rows // 2, cols // 2

        y_coords, x_coords = np.ogrid[:rows, :cols]
        dist_from_center = np.sqrt((y_coords - crow)**2 + (x_coords - ccol)**2)

        # 16-32 px spatial wavelength
        diag = np.sqrt(rows**2 + cols**2)
        r_min = diag / 64.0
        r_max = diag / 16.0

        mask = (dist_from_center >= r_min) & (dist_from_center <= r_max)

        mag = np.abs(fshift)
        phase = np.angle(fshift)

        np.random.seed(seed)
        half_random = np.random.uniform(-np.pi, np.pi, phase.shape)
        # Symmetrical phase for real inverse FFT
        sym_random_phase = 0.5 * (half_random - np.roll(np.roll(np.flip(half_random), 1, axis=0), 1, axis=1))

        phase_mod = phase.copy()
        phase_mod[mask] = sym_random_phase[mask]

        fshift_mod = mag * np.exp(1j * phase_mod)
        f_ishift = np.fft.ifftshift(fshift_mod)
        img_back = np.real(np.fft.ifft2(f_ishift))
        y_clean = np.clip(img_back, 0, 255).astype(np.uint8)

        ycrcb_clean = cv2.merge([y_clean, cr, cb])
        return cv2.cvtColor(ycrcb_clean, cv2.COLOR_YCrCb2BGR)

    def clean_hybrid_filter(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Fast filter pipeline: Bilateral filter + subtle camera sensor grain + sub-pixel Lanczos.
        """
        h, w = img_bgr.shape[:2]
        denoised = cv2.bilateralFilter(img_bgr, d=5, sigmaColor=15, sigmaSpace=15)

        np.random.seed(42)
        noise = np.random.normal(0, 1.2, img_bgr.shape).astype(np.float32)
        grained = np.clip(denoised.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        scaled = cv2.resize(grained, (int(w * 1.004), int(h * 1.004)), interpolation=cv2.INTER_LANCZOS4)
        start_y = (scaled.shape[0] - h) // 2
        start_x = (scaled.shape[1] - w) // 2
        return scaled[start_y:start_y+h, start_x:start_x+w]
