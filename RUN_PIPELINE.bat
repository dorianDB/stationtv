@echo off
REM ========================================
REM Station TV - Pipeline Automatique
REM Script de lancement pour Windows
REM ========================================

echo ================================================================================
echo STATION TV - PIPELINE AUTOMATIQUE COMPLET
echo ================================================================================
echo.

REM Activer l'environnement virtuel si présent
if exist venv\Scripts\activate.bat (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
) else (
    echo Pas d'environnement virtuel détecté, utilisation de Python global
)

REM Lancer le pipeline Python
echo.
echo Lancement du pipeline...
echo.

python scripts\RunPipeline.py

REM Code de sortie
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo Pipeline terminé avec succès!
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo Pipeline terminé avec des erreurs (code: %ERRORLEVEL%)
    echo ================================================================================
)

echo.
pause
