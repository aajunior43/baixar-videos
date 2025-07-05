# 🎬 Baixador de Vídeos Universal - Versão Avançada

Um baixador de vídeos completo e avançado com interface web usando Gradio, capaz de baixar vídeos de praticamente qualquer site suportado pelo yt-dlp.

## ✨ Funcionalidades Avançadas

- 📹 **Download de vídeos** de centenas de sites (YouTube, Vimeo, TikTok, Instagram, etc.)
- 📦 **Download em lote** (múltiplos vídeos de uma vez)
- 📚 **Download de playlists** completas
- 🍪 **Suporte a cookies** para sites com login/restrições
- 🌐 **User agents personalizados** para evitar bloqueios
- 🎯 **Múltiplas qualidades** de download (até 4K)
- 🎵 **Extração de áudio** em MP3 e M4A
- 📋 **Informações detalhadas** dos vídeos
- 📊 **Lista de formatos** disponíveis
- 🌐 **Lista de sites suportados** organizada por categoria
- 🎨 **Interface moderna** e intuitiva
- 📱 **Responsivo** para diferentes dispositivos
- 📊 **Relatórios de progresso** aprimorados para downloads
- 🔄 **Atualização automática** do yt-dlp
- 🧹 **Código mais limpo** e legível com type hints e docstrings

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- FFmpeg (para conversão de áudio)

### Instalar FFmpeg

**Windows:**
1. Baixe o FFmpeg de: https://ffmpeg.org/download.html
2. Extraia e adicione ao PATH do sistema

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Instalar dependências Python

```bash
pip install -r requirements.txt
```

## 🎯 Como usar

### 1. Executar o aplicativo

```bash
python video_downloader.py
```

### 2. Acessar a interface

Abra seu navegador e acesse: `http://localhost:7860`

### 3. Usar as funcionalidades

#### 📋 Informações do Vídeo
- Cole a URL do vídeo
- Opcional: Adicione arquivo de cookies para vídeos privados
- Clique em "Obter Informações"
- Veja título, duração, canal, visualizações, descrição, tags, etc.

#### ⬇️ Download Simples
- Cole a URL do vídeo
- Escolha a qualidade desejada:
  - **Melhor qualidade**: Máxima qualidade disponível
  - **4K ou menor**: Qualidade limitada a 4K
  - **1080p ou menor**: Qualidade limitada a 1080p
  - **720p ou menor**: Qualidade limitada a 720p
  - **Pior qualidade**: Menor tamanho de arquivo
  - **Apenas áudio (MP3)**: Extrai apenas o áudio em MP3
  - **Apenas áudio (M4A)**: Extrai apenas o áudio em M4A
- Opcional: Adicione cookies e user agent personalizado
- Clique em "Baixar Vídeo"

#### 📦 Download em Lote
- Cole múltiplas URLs (uma por linha)
- Escolha a qualidade desejada
- Opcional: Adicione cookies e user agent personalizado
- Clique em "Baixar em Lote"
- Veja o progresso e resultados de cada download

#### 📚 Playlists
- Cole a URL da playlist
- Escolha a qualidade desejada
- Opcional: Adicione cookies e user agent personalizado
- Clique em "Baixar Playlist"
- Todos os vídeos serão organizados em uma pasta

#### 📋 Formatos Disponíveis
- Cole a URL do vídeo
- Opcional: Adicione arquivo de cookies
- Clique em "Listar Formatos"
- Veja todas as qualidades e formatos disponíveis

#### 🌐 Sites Suportados
- Clique em "Mostrar Sites Suportados"
- Veja a lista completa organizada por categoria

## 📁 Estrutura de arquivos

```
projeto/
├── video_downloader.py    # Script principal
├── requirements.txt       # Dependências Python
├── README.md             # Este arquivo
├── install.bat           # Script de instalação Windows
├── install.sh            # Script de instalação Linux/macOS
└── downloads/            # Pasta onde os vídeos são salvos (criada automaticamente)
    ├── video1.mp4
    ├── video2.mp3
    └── playlist_name/    # Playlists são organizadas em pastas
        ├── video1.mp4
        └── video2.mp4
```

## 🎨 Sites suportados

O yt-dlp suporta centenas de sites, incluindo:

### Redes Sociais
- YouTube
- TikTok
- Instagram
- Facebook
- Twitter/X
- Reddit

### Plataformas de Vídeo
- Vimeo
- Dailymotion
- Twitch
- Bilibili
- Niconico

### Streaming
- Netflix (com cookies)
- Disney+
- Hulu
- Amazon Prime
- Crunchyroll

### E muitos outros!

## ⚙️ Configurações avançadas

### Cookies
Para baixar vídeos privados ou com restrições:
1. Use uma extensão do navegador para exportar cookies
2. Salve como arquivo .txt ou .cookies
3. Carregue o arquivo na interface

### User Agents
Para sites que bloqueiam downloads:
1. Use user agents diferentes
2. Exemplo: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`

### Alterar porta do servidor

Edite a linha no final do `video_downloader.py`:

```python
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,  # Altere esta porta
    share=False,
    show_error=True
)
```

### Alterar pasta de downloads

Edite a linha no início da classe `VideoDownloader`:

```python
def __init__(self):
    self.download_path = "downloads"  # Altere este caminho
    self.ensure_download_dir()
```

## 🔧 Solução de problemas

### Erro: "FFmpeg not found"
- Instale o FFmpeg seguindo as instruções acima
- Certifique-se de que está no PATH do sistema

### Erro: "Video unavailable"
- Verifique se a URL está correta
- Alguns vídeos podem ter restrições de região
- Tente usar cookies se o vídeo for privado
- Tente com um user agent diferente

### Download lento
- Escolha uma qualidade menor
- Verifique sua conexão com a internet
- Alguns sites podem limitar a velocidade

### Erro de permissão
- Certifique-se de que tem permissão para escrever na pasta do projeto
- Execute como administrador se necessário

### Site não suportado
- Verifique a lista de sites suportados na interface
- O yt-dlp é atualizado frequentemente, tente atualizar
- Alguns sites podem ter mudado e não serem mais suportados

## 📝 Licença

Este projeto é de código aberto e pode ser usado livremente.

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests

## ⚠️ Aviso legal

Este software é apenas para uso pessoal e educacional. Respeite os direitos autorais e termos de serviço dos sites de onde você baixa conteúdo. O desenvolvedor não se responsabiliza pelo uso inadequado do software. 