@echo off
setlocal enabledelayedexpansion

:: --- Configuration ---
set "PYTHON_DIR=%~dp0runtime"
set "PYTHON_VERSION=3.12.4"
set "UV_URL=https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
set "UV_ZIP=%~dp0uv.zip"
set "UV_EXE=%~dp0uv.exe"
set "PYTHON_INSTALL_DIR=%~dp0.python"

echo =================================================================
echo      Portable Python 3.12 Setup (The uv-native Method - True Final)
echo =================================================================
echo.

:: --- Pre-flight checks ---
if exist "!PYTHON_DIR!\Scripts\python.exe" (
    echo Environment already installed. Skipping.
    goto end_script
)

:: --- [1/4] Downloading uv ---
if not exist "!UV_EXE!" (
    echo --- [1/4] Downloading uv...
    powershell -Command "Invoke-WebRequest -Uri '!UV_URL!' -OutFile '!UV_ZIP!'"
    if !errorlevel! neq 0 goto :error
    powershell -Command "Expand-Archive -Path '!UV_ZIP!' -DestinationPath '%~dp0' -Force"
    if !errorlevel! neq 0 goto :error
    if not exist "!UV_EXE!" (
        echo ERROR: uv.exe not found after extraction.
        goto :error
    )
)

:: --- [2/4] Installing tkinter-enabled Python via uv ---
echo --- [2/4] Installing Python %PYTHON_VERSION% (with tkinter) via uv...
"!UV_EXE!" python install !PYTHON_VERSION!
if !errorlevel! neq 0 goto :error

:: --- [3/4] Creating Virtual Environment with uv ---
echo --- [3/4] Creating virtual environment with uv...
echo Finding installed Python path...
set "BASE_PYTHON_PATH="
for /f "usebackq delims=" %%i in (`"!UV_EXE!" python find !PYTHON_VERSION!`) do set "BASE_PYTHON_PATH=%%i"

if not defined BASE_PYTHON_PATH (
    echo ERROR: Could not find the path for Python !PYTHON_VERSION! using 'uv python find'.
    goto :error
)
echo Found Python at: !BASE_PYTHON_PATH!

"!UV_EXE!" venv "!PYTHON_DIR!" --python "!BASE_PYTHON_PATH!" --seed
if !errorlevel! neq 0 goto :error

:: --- [4/4] Installing PyInstaller ---
echo --- [4/4] Installing PyInstaller with uv...
"!UV_EXE!" pip install pyinstaller --python "!PYTHON_DIR!\Scripts\python.exe"
if !errorlevel! neq 0 goto :error

echo.
echo =======================================================
echo      SETUP COMPLETE! (using the superior uv method)
echo =======================================================
goto end_script

:error
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo      AN ERROR OCCURRED! Please check the output above.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

:end_script
echo.
echo Cleaning up temporary files...
if exist "!UV_ZIP!" del "!UV_ZIP!"
if exist "uv*.exe" del "uv*.exe"
if exist "!PYTHON_INSTALL_DIR!" rmdir /s /q "!PYTHON_INSTALL_DIR!"

echo.
echo Process finished.
pause
endlocal
