@echo off
title Launcher Analisa Saham Smart

echo ===================================================
echo      ANALISA SAHAM SMART - DASHBOARD
echo ===================================================

set PROJECT_DIR=d:\LOCAL DISK D\MY PROJECT\ai_saham_bot
set WEB_DIR=%PROJECT_DIR%\web

echo.
echo [1/3] Menjalankan Backend Flask Web Server...
start "Flask Server" cmd /k "cd /d %WEB_DIR% && python server.py" && timeout /t 1 /nobreak >nul && powershell -Command "Add-Type -AssemblyName System.Windows.Forms; (New-Object System.Windows.Forms.SendKeys)::SendWait('%n')" 2>nul

echo.
echo [2/3] Menjalankan Aplikasi Analisis...
start "Analysis" cmd /k "cd /d %PROJECT_DIR% && python app.py" && timeout /t 1 /nobreak >nul && powershell -Command "Add-Type -AssemblyName System.Windows.Forms; (New-Object System.Windows.Forms.SendKeys)::SendWait('%n')" 2>nul

echo.
echo Menunggu 5 detik agar server siap...
ping -n 6 127.0.0.1 >nul 2>&1

echo.
echo [3/3] Membuka Dashboard Saham di browser...
start http://localhost:5000

echo.
echo ===================================================
echo      ANALISA SAHAM SMART BERHASIL DIHIDUPKAN!
echo ===================================================
echo.
echo Flask Server + Analysis berjalan di background.
echo Untuk stop: tutup window Flask Server atau Analysis.
pause