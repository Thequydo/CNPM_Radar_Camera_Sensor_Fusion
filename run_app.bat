@echo off
title He Thong Giam Sat Giao Thong va Canh Bao Va Cham
chcp 65001 >nul
cd /d "%~dp0"

echo =====================================================================
echo   HE THONG GIAM SAT GIAO THONG VA CANH BAO VA CHAM (RADAR + CAMERA)
echo   Khoa Cong nghe Thong tin va Truyen thong - Nganh KTMT
echo =====================================================================
echo [INFO] Dang khoi dong giao dien giam sat thoi gian thuc...

if exist "C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" (
    "C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" main.py
) else (
    python main.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Chuong trinh bi dung hoac xay ra su co ngoai y muon!
    pause
)
