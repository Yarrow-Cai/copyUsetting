@echo off
chcp 65001 >nul
echo ========================================
echo      JSON文件复制工具
echo ========================================
echo.

if "%~1"=="" (
    echo 用法: run_copier.bat ^<json配置文件^> [输出目录]
    echo.
    echo 示例:
    echo   run_copier.bat example_config.json
    echo   run_copier.bat config.json D:\backup
    echo.
    pause
    exit /b 1
)

set JSON_FILE=%~1
set OUTPUT_DIR=%~2

echo 配置文件: %JSON_FILE%

if not exist "%JSON_FILE%" (
    echo [错误] 配置文件不存在: %JSON_FILE%
    pause
    exit /b 1
)

if not "%OUTPUT_DIR%"=="" (
    echo 输出目录: %OUTPUT_DIR%
    python file_copier.py "%JSON_FILE%" --output-dir "%OUTPUT_DIR%"
) else (
    python file_copier.py "%JSON_FILE%"
)

echo.
pause
