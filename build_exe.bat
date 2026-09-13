@echo off
echo ===================================================
echo   Bubble Arena - Standalone Windows EXE Builder
echo ===================================================
echo.

python -m pip install pyinstaller pygame
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [1/2] Building standalone BubbleArena.exe...
pyinstaller --noconfirm --clean --onefile --name "BubbleArena" --add-data "assets;assets" --add-data "Animation;Animation" --collect-all pygame main.py

if %ERRORLEVEL% EQU 0 (
    if not exist "Releases" mkdir "Releases"
    copy /y "dist\BubbleArena.exe" "Releases\BubbleArena.exe" >nul
    echo.
    echo ===================================================
    echo   [SUCCESS] Standalone EXE created successfully!
    echo   Output: Releases\BubbleArena.exe
    echo ===================================================
) else (
    echo.
    echo [ERROR] PyInstaller build failed with error code %ERRORLEVEL%.
)

pause
