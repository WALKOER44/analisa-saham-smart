@echo off
title Launcher Analisa Saham Smart

echo ===================================================
echo      ANALISA SAHAM SMART - DASHBOARD
echo ===================================================

echo.
echo [1/2] Menjalankan Backend Flask Web Server...
start "Flask Server" cmd /k "cd /d C:\ai_saham_bot\web && python server.py"

echo [2/2] Menjalankan MCP Server...
start "MCP Server" cmd /k "cd /d C:\ai_saham_bot && python mcp_server.py"

echo.
echo Menunggu 3 detik agar server siap...
timeout /t 3 /nobreak >nul

echo.
echo Memicu analisis data saham awal...
powershell -Command "Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/analyze' -Method Get" >nul 2>&1

echo.
echo Membuka Dashboard Saham di browser...
start http://localhost:5000

echo.
echo ===================================================
echo      ANALISA SAHAM SMART BERHASIL DIHIDUPKAN!
echo ===================================================
pause