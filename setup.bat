@echo off
setlocal enabledelayedexpansion

set "PYTHON_DIR=%~dp0spyder-runtime"
set "MINICONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Windows-x86_64.exe"
set "INSTALLER_NAME=%~dp0miniconda_installer.exe"

echo =======================================================
echo      Portable Python Environment Setup (spyder-runtime)
echo =======================================================
echo.

rem Check if spyder-runtime directory already exists and is not empty
if exist "%PYTHON_DIR%\python.exe" (
    echo Python environment already seems to be installed in:
    echo %PYTHON_DIR%
    echo.
    echo If you want to reinstall, please delete this folder and run this script again.
    echo.
    echo Setup skipped.
    goto :end
)

echo Target installation directory:
echo %PYTHON_DIR%
echo.

rem Check for PowerShell
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: PowerShell is required to download the installer.
    echo Please install PowerShell and try again.
    goto :end
)

echo Downloading Miniconda installer...
powershell -Command "Write-Host 'Downloading from %MINICONDA_URL%...'; Invoke-WebRequest -Uri '%MINICONDA_URL%' -OutFile '%INSTALLER_NAME%'"

if not exist "%INSTALLER_NAME%" (
    echo.
    echo ERROR: Failed to download Miniconda installer.
    echo Please check your internet connection or the URL:
    echo %MINICONDA_URL%
    goto :end
)

echo.
echo Installing Miniconda (this may take a few minutes)...
echo Please wait, the installer is running silently in the background.
start /wait "" "%INSTALLER_NAME%" /InstallationType=JustMe /RegisterPython=0 /S /D="%PYTHON_DIR%"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Miniconda installation failed.
    echo The installer exited with an error.
    goto :cleanup
)

rem Verify installation
if not exist "%PYTHON_DIR%\python.exe" (
    echo.
    echo ERROR: Installation seems to have failed. python.exe not found.
    echo Please check for any error messages and try again.
    goto :cleanup
)

echo.
echo Installation successful!
echo.
echo =======================================================
echo      Setup Complete!
echo =======================================================
echo The portable Python environment is ready in the 'spyder-runtime' folder.

:cleanup
if exist "%INSTALLER_NAME%" (
    echo.
    echo Cleaning up installer file...
    del "%INSTALLER_NAME%"
)

:end
echo.
pause
endlocal
