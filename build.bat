@echo off
chcp 65001 >nul

echo ===================================
echo  DevTools Backup Tool Build Script
echo ===================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [Step 1/3] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo [Step 2/3] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist DevToolsBackup.spec del /f /q DevToolsBackup.spec

echo [Step 3/3] Building EXE...
set CONFIG_FILE=backup_config.example.json
if /I "%~1"=="--local-config" (
    if exist backup_config.json (
        set CONFIG_FILE=backup_config.json
    ) else (
        echo [WARN] backup_config.json not found, fallback to backup_config.example.json
    )
)
echo Using config file: %CONFIG_FILE%
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "DevToolsBackup" --add-data "%CONFIG_FILE%;." backup_tool.py

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ===================================
echo  Build Success!
echo ===================================
echo.
echo Output file: dist\DevToolsBackup.exe
echo.
pause
