@echo off
echo ========================================
echo    Baixador de Videos Universal
echo ========================================
echo.
echo Instalando dependencias...
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior
    echo Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python encontrado!
echo.

REM Instalar dependências
echo Instalando bibliotecas Python...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Instalacao concluida!
echo ========================================
echo.
echo Para executar o baixador:
echo    python video_downloader.py
echo.
echo IMPORTANTE: Instale o FFmpeg para conversao de audio
echo Baixe em: https://ffmpeg.org/download.html
echo.
pause 