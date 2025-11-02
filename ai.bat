@echo off
chcp 850 >nul
setlocal enabledelayedexpansion

rem ===== CONFIG =====
set "FULL_URL=https://raw.githubusercontent.com/Indifferenzah/AiDetector/main/aidetector.py"
set "LIGHT_URL=https://raw.githubusercontent.com/Indifferenzah/AiDetector/main/aidetector_Light.py"
rem ==================

:MENU
cls
color 04
echo ===============================
echo  AI Detector — Menu principale
echo ===============================
echo.
echo 1) Versione completa
echo 2) Versione leggera
echo 3) Scarica o Aggiorna script
echo 4) Esegui script
echo 5) Esci
echo.
set /p choice=">> "

if "%choice%"=="1" goto FULL
if "%choice%"=="2" goto LIGHT
if "%choice%"=="3" goto UPDATE
if "%choice%"=="4" goto RUN_ONLY
if "%choice%"=="5" goto END

echo Scelta non valida. Premi un tasto...
pause >nul
goto MENU

:FULL
color 0A
echo Scaricamento versione COMPLETA da GitHub...
powershell -Command "Invoke-WebRequest -Uri '%FULL_URL%' -OutFile 'detector_full.py' -UseBasicParsing"
if errorlevel 1 (
    color 0C
    echo Errore: impossibile scaricare detector_full.py. Controlla l'URL.
    pause
    goto MENU
)
echo Modifica script per input manuale multi-linea...
powershell -Command "$content = Get-Content 'detector_full.py' -Raw; $content = $content -replace 'pyperclip\.paste\(\)[:0-9]*', 'print(\"Incolla il testo da analizzare (premi Ctrl+Z + Enter per finire):\"); sys.stdin.read()'; Set-Content 'detector_full.py' $content"
echo Creazione virtualenv (venv_full)...
python -m venv venv_full
call venv_full\Scripts\activate.bat
echo Installazione moduli richiesti (torch, transformers, ecc)...
python -m pip install --upgrade pip
python -m pip install torch transformers pyperclip regex sentencepiece
echo Avvio AI Detector COMPLETO...
python detector_full.py
call venv_full\Scripts\deactivate.bat
pause
goto MENU

:LIGHT
color 0A
echo Scaricamento versione LEGGERA da GitHub...
powershell -Command "Invoke-WebRequest -Uri '%LIGHT_URL%' -OutFile 'detector_light.py' -UseBasicParsing"
if errorlevel 1 (
    color 0C
    echo Errore: impossibile scaricare detector_light.py. Controlla l'URL.
    pause
    goto MENU
)
echo Modifica script per input manuale multi-linea...
powershell -Command "$content = Get-Content 'detector_light.py' -Raw; $content = $content -replace 'pyperclip\.paste\(\)[:0-9]*', 'print(\"Incolla il testo da analizzare (premi Ctrl+Z + Enter per finire):\"); sys.stdin.read()'; Set-Content 'detector_light.py' $content"
echo Creazione virtualenv (venv_light)...
python -m venv venv_light
call venv_light\Scripts\activate.bat
echo Avvio AI Detector LEGGERO...
python detector_light.py
call venv_light\Scripts\deactivate.bat
pause
goto MENU

:UPDATE
echo Aggiornamento versioni da GitHub...
powershell -Command "Invoke-WebRequest -Uri '%FULL_URL%' -OutFile 'detector_full.py' -UseBasicParsing"
powershell -Command "Invoke-WebRequest -Uri '%LIGHT_URL%' -OutFile 'detector_light.py' -UseBasicParsing"
echo Script aggiornati con successo.
pause
goto MENU

:RUN_ONLY
echo.
echo 1) Esegui versione COMPLETA
echo 2) Esegui versione LEGGERA
set /p subchoice="Scelta: "
if "%subchoice%"=="1" (
    if not exist detector_full.py (
        echo detector_full.py non trovato.
        pause
        goto MENU
    )
    call venv_full\Scripts\activate.bat
    python detector_full.py
    call venv_full\Scripts\deactivate.bat
    pause
    goto MENU
)
if "%subchoice%"=="2" (
    if not exist detector_light.py (
        echo detector_light.py non trovato.
        pause
        goto MENU
    )
    call venv_light\Scripts\activate.bat
    python detector_light.py
    call venv_light\Scripts\deactivate.bat
    pause
    goto MENU
)
goto MENU

:END
echo Bye!
echo Pulizia file scaricati...
if exist detector_full.py del detector_full.py
if exist detector_light.py del detector_light.py
if exist venv_full rmdir /s /q venv_full
if exist venv_light rmdir /s /q venv_light
endlocal
exit /b 0

