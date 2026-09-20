#!/usr/bin/env bash
echo "================================================================"
echo "          Aethelon SynthID & AI Watermark Remover"
echo "================================================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 could not be found. Please install Python 3.10+."
    exit 1
fi

echo "[1/2] Checking dependencies..."
pip install -r requirements.txt --quiet

echo "[2/2] Launching server on http://127.0.0.1:7860..."
python3 app.py
