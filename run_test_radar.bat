@echo off
title Kiem Tra Radar HLK-LD2450 - Giai Doan 1
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON_EXE=C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe

if "%~1"=="" (
    echo [INFO] Dang chay kiem tra Radar Pipeline Giai doan 1 tren cong COM5...
    "%PYTHON_EXE%" test_radar.py COM5
) else (
    echo [INFO] Dang chay kiem tra Radar voi tham so: %*
    "%PYTHON_EXE%" test_radar.py %*
)

pause
