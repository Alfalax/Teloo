@echo off
echo ============================================================
echo   INICIANDO BOT DE TELEGRAM - TeLOO
echo ============================================================
echo.
echo Configuracion:
echo - OpenAI: gpt-4o-mini + whisper-1
echo - Gemini: gemini-2.0-flash (respaldo)
echo - Telegram: Modo Polling
echo.
echo ============================================================
echo.

cd services\agent-ia
python start_polling.py

pause
