@echo off
REM Cambiar al directorio donde está este archivo
cd /d "%~dp0"

REM Intentar ejecutar con python
python poker_probability_calculator.py

REM Si falla, intentar con python3
if errorlevel 1 (
    python3 poker_probability_calculator.py
)

REM Si aún falla, mostrar mensaje
if errorlevel 1 (
    echo.
    echo Error: No se pudo ejecutar Python.
    echo Por favor asegurate de tener Python instalado y en el PATH.
    echo.
    pause
)
