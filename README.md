# Aethelon SynthID Remover (Release v1.0.0)

<p align="center">
  <img src="https://img.shields.io/badge/Status-Release_v1.0-brightgreen.svg" alt="Status">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Framework-FastAPI_%26_PyTorch-orange.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Hardware-CUDA_or_CPU-purple.svg" alt="Hardware">
</p>

A powerful, high-fidelity desktop & web tool designed to remove Google DeepMind's invisible **SynthID** watermarks, visible AI marks (e.g. Gemini Sparkle), and synthetic C2PA/JUMBF provenance metadata from AI-generated or AI-edited images.

---

## Features
- **One-Click Launcher (`start.bat` / `start.sh`):** Launches a sleek, modern, dark-themed dashboard on `http://127.0.0.1:7860`.
- **In-App Model Manager:** Models are decoupled from the git repo. Download the lightweight VAE (~335 MB) directly from the UI or use the zero-download Fourier mode.
- **Multiple Sanitization Engines:**
  - **VAE Latent Space Reconstruction:** Encodes into 8x latent space, injects calibrated noise, and reconstructs pixels via VAE decoder to completely destroy the SynthID frequency carrier wave while preserving facial/texture details (29+ dB PSNR).
  - **Fourier Annular Phase Scrambling (0 MB):** Randomizes the phase in the 16-32 px wavelength band using 2D FFT, defeating the neural detector's frequency correlation.
  - **Hybrid Filter:** Bilateral edge-preserving filtering + camera sensor grain injection.
- **Visible Watermark Removal:** Inpaints the Gemini sparkle logo at the bottom-right corner.
- **EXIF Camera Presets:** Injects authentic iPhone 12/15 Pro, Samsung S24, or Sony Alpha camera metadata while scrubbing C2PA/JUMBF provenance.

Distributed under the MIT License.
