#!/bin/bash

echo "========================================"
echo "    Baixador de Videos Universal"
echo "========================================"
echo

echo "Instalando dependencias..."
echo

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 nao encontrado!"
    echo "Por favor, instale o Python 3.8 ou superior"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "Python encontrado!"
echo

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "ERRO: pip3 nao encontrado!"
    echo "Por favor, instale o pip3"
    echo "Ubuntu/Debian: sudo apt install python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

echo "pip encontrado!"
echo

# Instalar dependências
echo "Instalando bibliotecas Python..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar dependencias!"
    exit 1
fi

echo
echo "========================================"
echo "    Instalacao concluida!"
echo "========================================"
echo
echo "Para executar o baixador:"
echo "    python3 video_downloader.py"
echo
echo "IMPORTANTE: Instale o FFmpeg para conversao de audio"
echo "Ubuntu/Debian: sudo apt install ffmpeg"
echo "macOS: brew install ffmpeg"
echo 