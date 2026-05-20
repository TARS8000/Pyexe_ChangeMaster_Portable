@echo off
setlocal enabledelayedexpansion

set "PYTHON_DIR_VALUE=%~dp0runtime"
set "PYTHON_VERSION=3.12.4"
set "PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"
set "INSTALLER_NAME=%~dp0python_installer.exe"

echo =================================================================
echo      Portable Python Setup (Targeted Install Method)
echo =================================================================
echo.

rem Check if runtime directory already exists
if exist "!PYTHON_DIR_VALUE!\python.exe" (
    echo Python environment already seems to be installed in:
    echo !PYTHON_DIR_VALUE!
    echo.
    echo If you want to reinstall, please DELETE the 'runtime' folder
    echo and run this script again.
    echo.
    echo Setup skipped.
    goto :end
)

echo Target installation directory: !PYTHON_DIR_VALUE!
echo.

rem Check for PowerShell
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell is required for this setup.
    goto :end
)

rem --- Download Python Installer ---
echo [1/3] Downloading Python %PYTHON_VERSION% installer...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_INSTALLER_URL%' -OutFile '%INSTALLER_NAME%'"
if not exist "%INSTALLER_NAME%" (
    echo.
    echo ERROR: Failed to download Python installer.
    goto :cleanup
)

rem --- Get short path name for PYTHON_DIR_VALUE if it contains spaces/special chars ---
for %%I in ("!PYTHON_DIR_VALUE!") do set "PYTHON_DIR_SHORT=%%~sI"

rem --- Perform targeted, isolated installation ---
echo [2/3] Installing Python to 'runtime' folder...
echo This may take a moment. A progress window may appear briefly.
rem Construct TargetDir argument with explicit quotes, using short path name
set "TARGET_DIR_ARG=TargetDir="!PYTHON_DIR_SHORT!""
set "INSTALL_ARGS=/quiet InstallAllUsers=0 !TARGET_DIR_ARG! PrependPath=0 AssociateFiles=0 Shortcuts=0 Include_pip=1 Include_tcltk=1"
echo Running: "%INSTALLER_NAME%" !INSTALL_ARGS!
start /wait "" "%INSTALLER_NAME%" !INSTALL_ARGS!

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python installation failed with error code: %errorlevel%.
    echo Please try running this script as an Administrator if the problem persists.
    goto :cleanup
)

if not exist "!PYTHON_DIR_VALUE!\python.exe" (
    echo.
    echo ERROR: Failed to install Python. python.exe not found.
    goto :cleanup
)

rem --- Install PyInstaller ---
echo [3/3] Installing PyInstaller...
"!PYTHON_DIR_VALUE!\python.exe" -m pip install pyinstaller
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PyInstaller installation failed.
    goto :cleanup
)

echo.
echo =======================================================
echo      Setup Complete!
echo =======================================================
echo A portable Python environment with the full standard library
echo is ready in the 'runtime' folder.

:cleanup
echo.
echo Cleaning up temporary files...
if exist "%INSTALLER_NAME%" del "%INSTALLER_NAME%"

:end
echo.
pause
endlocal
