@echo off
chcp 65001 > nul
title Aethelon SynthID Remover
color 0A

echo ================================================================
echo           Aethelon SynthID & AI Watermark Remover
echo ================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.10+ yukleyin ve PATH'e ekleyin.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt --quiet

echo.
echo [2/2] Arayuz baslatiliyor...
echo.
echo Tarayici otomatik acilacak: http://127.0.0.1:7860
echo Kapatmak icin bu pencereyi kapatin veya Ctrl+C yapin.
echo.

python app.py

pause
