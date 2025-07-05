import gradio as gr
import yt_dlp
import os
import re
from pathlib import Path
import threading
import time
import subprocess
import json
import random
import webbrowser

class VideoDownloader:
    def __init__(self) -> None:
        """Inicializa a classe VideoDownloader e configura o diretório de downloads e user agents."""
        self.download_path: str = "downloads"
        self.ensure_download_dir()
        
        # User agents para evitar bloqueios
        self.user_agents: list[str] = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def ensure_download_dir(self) -> None:
        """Cria o diretório de downloads se não existir."""
        Path(self.download_path).mkdir(exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """Remove caracteres inválidos do nome do arquivo para garantir compatibilidade com o sistema de arquivos."""
        return re.sub(r'[<>:"/\\|?*]', '', filename)
    
    def get_random_user_agent(self) -> str:
        """Retorna um user agent aleatório da lista predefinida para evitar bloqueios."""
        return random.choice(self.user_agents)
    
    def _create_progress_hook(self, progress: gr.Progress, description_prefix: str = "", total_items: int = 1, current_item_index: int = 0):
        """Cria um hook de progresso para yt-dlp que atualiza a barra de progresso do Gradio."""
        def _progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                if total_bytes:
                    percent = downloaded_bytes / total_bytes
                    # Ajustar o progresso para downloads em lote
                    overall_percent = (current_item_index + percent) / total_items
                    progress(overall_percent, desc=f"{description_prefix}Baixando: {d['_percent_str']} de {d['_total_bytes_str']}")
                else:
                    progress(0, desc=f"{description_prefix}Baixando: {d['_percent_str']}")
            elif d['status'] == 'finished':
                overall_percent = (current_item_index + 1) / total_items
                progress(overall_percent, desc=f"{description_prefix}Processando: {d['filename']}")
            elif d['status'] == 'error':
                progress(0, desc=f"{description_prefix}Erro no download.")
        return _progress_hook

    def get_advanced_ydl_opts(self, quality: str = "best", cookies_file: str = None, user_agent: str = None, output_path: str = None) -> dict:
        """Configura as opções avançadas do yt-dlp com base na qualidade e outros parâmetros.

        Args:
            quality (str, optional): Qualidade desejada do vídeo. Defaults to "best".
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
            user_agent (str, optional): User agent a ser usado. Defaults to None.
            output_path (str, optional): Caminho para o diretório de saída. Defaults to None.

        Returns:
            dict: Dicionário de opções para o yt-dlp.
        """
        current_download_path = output_path if output_path else self.download_path
        Path(current_download_path).mkdir(exist_ok=True) # Garante que o diretório de destino exista

        ydl_opts: dict = {
            'outtmpl': os.path.join(current_download_path, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': False,
            'extract_flat': False,
            'user_agent': user_agent or self.get_random_user_agent(),
            'http_headers': {
                'User-Agent': user_agent or self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Keep-Alive': '115',
                'Connection': 'keep-alive',
            }
        }
        
        # Adicionar cookies se especificado
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        
        # Configurar qualidade
        if quality == "Melhor qualidade":
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        elif quality == "Pior qualidade":
            ydl_opts['format'] = 'worst'
        elif quality == "Apenas áudio (MP3)":
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality == "Apenas áudio (M4A)":
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]
        elif quality == "720p ou menor":
            ydl_opts['format'] = 'best[height<=720]/best'
        elif quality == "1080p ou menor":
            ydl_opts['format'] = 'best[height<=1080]/best'
        elif quality == "4K ou menor":
            ydl_opts['format'] = 'best[height<=2160]/best'
        else:
            ydl_opts['format'] = 'best'
        
        return ydl_opts
    
    def get_video_info(self, url: str, cookies_file: str = None) -> dict:
        """Obtém informações detalhadas de um vídeo sem realizar o download.

        Args:
            url (str): URL do vídeo.
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.

        Returns:
            dict: Dicionário contendo informações do vídeo ou um erro.
        """
        try:
            ydl_opts = self.get_advanced_ydl_opts(cookies_file=cookies_file)
            ydl_opts['quiet'] = True
            ydl_opts['no_warnings'] = True
            ydl_opts['extract_flat'] = True
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {'error': 'Não foi possível extrair informações do vídeo.'}
                return {
                    'title': info.get('title', 'Vídeo sem título'),
                    'duration': info.get('duration', 0),
                    'formats': info.get('formats', []),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Desconhecido'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')[:500] + '...' if info.get('description') else '',
                    'upload_date': info.get('upload_date', ''),
                    'tags': info.get('tags', [])[:10] if info.get('tags') else []
                }
        except Exception as e:
            return {'error': str(e)}
    
    def download_video(self, url: str, quality: str, progress_callback=None, cookies_file: str = None, user_agent: str = None, output_path: str = None) -> dict:
        """Baixa um vídeo com a qualidade especificada.

        Args:
            url (str): URL do vídeo a ser baixado.
            quality (str): Qualidade desejada do vídeo.
            progress_callback (callable, optional): Função de callback para o progresso do download. Defaults to None.
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
            user_agent (str, optional): User agent a ser usado. Defaults to None.
            output_path (str, optional): Caminho para o diretório de saída. Defaults to None.

        Returns:
            dict: Dicionário com o status do download (sucesso/erro) e informações do vídeo.
        """
        try:
            ydl_opts = self.get_advanced_ydl_opts(quality, cookies_file, user_agent, output_path)
            
            if progress_callback:
                ydl_opts['progress_hooks'] = [progress_callback]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return {'success': False, 'error': 'Não foi possível extrair informações do vídeo.'}
                return {
                    'success': True,
                    'title': info.get('title', 'Vídeo baixado'),
                    'filename': info.get('_filename', 'arquivo_desconhecido'),
                    'duration': info.get('duration', 0),
                    'filesize': info.get('filesize', 0)
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def download_playlist(self, url: str, quality: str, progress_callback=None, cookies_file: str = None, user_agent: str = None, output_path: str = None) -> dict:
        """Baixa uma playlist inteira com a qualidade especificada.

        Args:
            url (str): URL da playlist a ser baixada.
            quality (str): Qualidade desejada para os vídeos da playlist.
            progress_callback (callable, optional): Função de callback para o progresso do download. Defaults to None.
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
            user_agent (str, optional): User agent a ser usado. Defaults to None.
            output_path (str, optional): Caminho para o diretório de saída. Defaults to None.

        Returns:
            dict: Dicionário com o status do download (sucesso/erro) e informações da playlist.
        """
        try:
            ydl_opts = self.get_advanced_ydl_opts(quality, cookies_file, user_agent, output_path)
            ydl_opts['outtmpl'] = os.path.join(output_path if output_path else self.download_path, '%(playlist_title)s/%(title)s.%(ext)s')
            
            if progress_callback:
                ydl_opts['progress_hooks'] = [progress_callback]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return {'success': False, 'error': 'Não foi possível extrair informações da playlist.'}
                return {
                    'success': True,
                    'title': info.get('title', 'Playlist baixada'),
                    'entries': len(info.get('entries', [])),
                    'playlist_title': info.get('title', 'Playlist')
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_formats(self, url: str, cookies_file: str = None) -> list[str]:
        """Obtém uma lista de formatos de vídeo e áudio disponíveis para download.

        Args:
            url (str): URL do vídeo.
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.

        Returns:
            list[str]: Lista de strings descrevendo os formatos disponíveis ou uma mensagem de erro.
        """
        try:
            ydl_opts = self.get_advanced_ydl_opts(cookies_file=cookies_file)
            ydl_opts['quiet'] = True
            ydl_opts['no_warnings'] = True
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return ["Erro ao obter formatos: Não foi possível extrair informações do vídeo."]
                formats = info.get('formats', [])
                
                format_list = []
                for f in formats:
                    if f.get('height') and f.get('ext'):
                        filesize = f.get('filesize', 'N/A')
                        if filesize != 'N/A':
                            filesize = format_file_size(filesize)
                        format_list.append(f"{f['height']}p - {f['ext']} - {filesize}")
                
                return format_list
        except Exception as e:
            return [f"Erro ao obter formatos: {str(e)}"]
    
    def get_supported_sites(self) -> list[str]:
        """Obtém uma lista de sites suportados pelo yt-dlp.

        Returns:
            list[str]: Lista de nomes de extratores suportados ou uma mensagem de erro.
        """
        try:
            # Usar a função correta do yt-dlp para listar extractors
            from yt_dlp.extractor import list_extractors
            extractors = list_extractors()
            # Converter para strings e ordenar
            extractor_names = [str(extractor) for extractor in extractors]
            return sorted(extractor_names)
        except Exception as e:
            return [f"Erro ao obter sites suportados: {str(e)}"]
    
    def batch_download(self, urls: str, quality: str, progress_callback=None, cookies_file: str = None, user_agent: str = None) -> list[dict]:
        """Baixa múltiplos vídeos de uma lista de URLs.

        Args:
            urls (str): String contendo URLs separadas por quebra de linha.
            quality (str): Qualidade desejada para os vídeos.
            progress_callback (callable, optional): Função de callback para o progresso do download. Defaults to None.
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
            user_agent (str): User agent a ser usado. Defaults to None.

        Returns:
            list[dict]: Lista de dicionários com o status e informações de cada download.
        """
        results: list[dict] = []
        urls_list: list[str] = [url.strip() for url in urls.split('\n') if url.strip()]
        
        for i, url in enumerate(urls_list):
            # O progress_callback aqui é mais para o progresso geral do lote, não do vídeo individual
            if progress_callback:
                progress_callback({'status': 'downloading', 'downloaded_bytes': i, 'total_bytes': len(urls_list)})
            
            result = self.download_video(url, quality, None, cookies_file, user_agent) # Passa None para o progress_hook interno
            results.append({
                'url': url,
                'success': result['success'],
                'title': result.get('title', ''),
                'error': result.get('error', '')
            })
        
        return results

    def get_available_qualities(self, url: str, cookies_file: str = None) -> dict:
        """Obtém e organiza as qualidades de vídeo disponíveis para download.

        Args:
            url (str): URL do vídeo.
            cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.

        Returns:
            dict: Dicionário com informações do vídeo e qualidades organizadas ou um erro.
        """
        try:
            ydl_opts = self.get_advanced_ydl_opts(cookies_file=cookies_file)
            ydl_opts['quiet'] = True
            ydl_opts['no_warnings'] = True
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {"error": "Não foi possível extrair informações do vídeo."}
                
                formats = info.get('formats', [])
                qualities: dict[int, list[dict]] = {}
                
                for f in formats:
                    if f.get('height') and f.get('ext'):
                        height: int = f['height']
                        ext: str = f['ext']
                        filesize: int = f.get('filesize', 0)
                        format_id: str = f.get('format_id', 'N/A')
                        fps: float = f.get('fps', 'N/A')
                        
                        # Organizar por qualidade
                        if height not in qualities:
                            qualities[height] = []
                        
                        quality_info: dict = {
                            'format_id': format_id,
                            'ext': ext,
                            'filesize': filesize,
                            'fps': fps,
                            'format_note': f.get('format_note', ''),
                            'url': f.get('url', ''),
                            'format': f.get('format', '')
                        }
                        
                        qualities[height].append(quality_info)
                
                # Ordenar qualidades por altura
                sorted_qualities = dict(sorted(qualities.items(), reverse=True))
                
                return {
                    'title': info.get('title', 'Vídeo sem título'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Desconhecido'),
                    'qualities': sorted_qualities
                }
                
        except Exception as e:
            return {"error": f"Erro ao obter qualidades: {str(e)}"}

def format_duration(seconds):
    """Converte uma duração em segundos para um formato de tempo legível (HH:MM:SS ou MM:SS)."""
    if not seconds:
        return "Desconhecido"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_file_size(bytes_size: int) -> str:
    """Converte bytes em formato legível"""
    if not bytes_size:
        return "Desconhecido"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

# Instância global do downloader
downloader = VideoDownloader()



def download_video_ui(url: str, quality: str, cookies_file: str = None, user_agent: str = None, output_path: str = None, progress=gr.Progress()) -> str:
    """
    Interface para download de vídeo individual.
    Args:
        url (str): URL do vídeo a ser baixado.
        quality (str): Qualidade desejada para o download.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
        user_agent (str, optional): User agent personalizado. Defaults to None.
        output_path (str, optional): Caminho para o diretório de saída. Defaults to None.
        progress (gr.Progress, optional): Objeto de progresso do Gradio. Defaults to gr.Progress().
    Returns:
        str: Mensagem de status do download.
    """
    if not url.strip():
        return "❌ Por favor, insira uma URL válida."
    
    progress(0, desc="Iniciando download...")
    
    # Usar o novo método para criar o progress hook
    progress_hook = downloader._create_progress_hook(progress)
    
    result = downloader.download_video(url, quality, progress_hook, cookies_file, user_agent, output_path)
    
    if result['success']:
        filename = os.path.basename(result['filename'])
        filesize = format_file_size(result.get('filesize', 0)) if result.get('filesize') else "Desconhecido"
        final_download_path = output_path if output_path else downloader.download_path
        return f"✅ **Download concluído com sucesso!**\n\n📁 **Arquivo:** {filename}\n📹 **Título:** {result['title']}\n💾 **Tamanho:** {filesize}\n📂 **Localização:** {final_download_path}"
    else:
        return f"❌ **Erro no download:** {result['error']}"

def download_playlist_ui(url: str, quality: str, cookies_file: str = None, user_agent: str = None, output_path: str = None, progress=gr.Progress()) -> str:
    """
    Interface para download de playlist.
    Args:
        url (str): URL da playlist a ser baixada.
        quality (str): Qualidade desejada para o download.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
        user_agent (str, optional): User agent personalizado. Defaults to None.
        output_path (str, optional): Caminho para o diretório de saída. Defaults to None.
        progress (gr.Progress, optional): Objeto de progresso do Gradio. Defaults to gr.Progress().
    Returns:
        str: Mensagem de status do download da playlist.
    """
    if not url.strip():
        return "❌ Por favor, insira uma URL válida."
    
    progress(0, desc="Iniciando download da playlist...")
    
    # Usar o novo método para criar o progress hook
    progress_hook = downloader._create_progress_hook(progress, description_prefix="Baixando playlist...")
    
    result = downloader.download_playlist(url, quality, progress_hook, cookies_file, user_agent, output_path)
    
    if result['success']:
        final_download_path = output_path if output_path else downloader.download_path
        return f"✅ **Playlist baixada com sucesso!**\n\n📁 **Título:** {result['title']}\n📊 **Vídeos:** {result['entries']}\n📂 **Localização:** {final_download_path}/{result['playlist_title']}"
    else:
        return f"❌ **Erro no download da playlist:** {result['error']}"

def batch_download_ui(urls: str, quality: str, cookies_file: str = None, user_agent: str = None, output_path: str = None, progress=gr.Progress()) -> str:
    """
    Interface para download em lote de vídeos.
    Args:
        urls (str): URLs dos vídeos, uma por linha.
        quality (str): Qualidade desejada para o download.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
        user_agent (str, optional): User agent personalizado. Defaults to None.
        output_path (str, optional): Caminho para o diretório de saída. Defaults to None.
        progress (gr.Progress, optional): Objeto de progresso do Gradio. Defaults to gr.Progress().
    Returns:
        str: Mensagem de status do download em lote.
    """
    if not urls.strip():
        return "❌ Por favor, insira URLs válidas."
    
    urls_list = [url.strip() for url in urls.split('\n') if url.strip()]
    if not urls_list:
        return "❌ Nenhuma URL válida encontrada."
    
    total_videos = len(urls_list)
    results = []
    
    for i, url in enumerate(urls_list):
        progress(i / total_videos, desc=f"Iniciando download do vídeo {i+1}/{total_videos}: {url[:50]}...")
        
        # Criar um progress hook para cada vídeo, com o progresso geral do lote
        video_progress_hook = downloader._create_progress_hook(
            progress,
            total_items=total_videos,
            current_item_index=i,
            description_prefix=f"Vídeo {i+1}/{total_videos}: "
        )
        
        result = downloader.download_video(url, quality, video_progress_hook, cookies_file, user_agent, output_path)
        results.append({
            'url': url,
            'success': result['success'],
            'title': result.get('title', ''),
            'error': result.get('error', '')
        })
    
    success_count = sum(1 for r in results if r['success'])
    error_count = total_videos - success_count
    
    final_download_path = output_path if output_path else downloader.download_path
    result_text = f"📊 **Download em lote concluído!**\n\n✅ **Sucessos:** {success_count}\n❌ **Erros:** {error_count}\n📂 **Localização:** {final_download_path}\n\n"
    
    for result in results:
        if result['success']:
            result_text += f"✅ {result['title']}\n"
        else:
            result_text += f"❌ {result['url']}: {result['error']}\n"
    
    return result_text

def get_formats_ui(url: str, cookies_file: str = None) -> str:
    """Interface para listar formatos disponíveis de um vídeo.

    Args:
        url (str): URL do vídeo.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.

    Returns:
        str: String formatada com os formatos disponíveis ou uma mensagem de erro.
    """
    if not url.strip():
        return "Por favor, insira uma URL válida."
    
    formats: list[str] = downloader.get_available_formats(url, cookies_file)
    
    if not formats:
        return "Nenhum formato disponível encontrado."
    
    formats_text: str = "📋 **Formatos disponíveis:**\n\n"
    for i, fmt in enumerate(formats[:20], 1):  # Limita a 20 formatos
        formats_text += f"{i}. {fmt}\n"
    
    if len(formats) > 20:
        formats_text += f"\n... e mais {len(formats) - 20} formatos"
    
    return formats_text

def get_supported_sites_ui() -> str:
    """Interface para exibir a lista de sites suportados pelo yt-dlp, categorizados.

    Returns:
        str: String formatada com a lista de sites suportados ou uma mensagem de erro.
    """
    sites: list[str] = downloader.get_supported_sites()
    
    if not sites or len(sites) == 1 and 'Erro' in sites[0]:
        return sites[0] if sites else "Erro ao obter sites suportados."
    
    # Agrupar sites por categoria
    categories: dict[str, list[str]] = {
        'Redes Sociais': ['youtube', 'facebook', 'instagram', 'tiktok', 'twitter', 'reddit'],
        'Plataformas de Vídeo': ['vimeo', 'dailymotion', 'twitch', 'bilibili', 'niconico'],
        'Streaming': ['netflix', 'disney', 'hulu', 'amazon', 'crunchyroll'],
        'Outros': []
    }
    
    sites_text: str = "🌐 **Sites Suportados pelo yt-dlp:**\n\n"
    sites_text += f"📊 **Total de sites:** {len(sites)}\n\n"
    
    for category, keywords in categories.items():
        category_sites: list[str] = [site for site in sites if any(keyword in site.lower() for keyword in keywords)]
        if category_sites:
            sites_text += f"**{category}:**\n"
            for site in sorted(category_sites)[:10]:  # Limita a 10 por categoria
                sites_text += f"• {site}\n"
            if len(category_sites) > 10:
                sites_text += f"  ... e mais {len(category_sites) - 10}\n"
            sites_text += "\n"
    
    # Mostrar alguns sites aleatórios da categoria "Outros"
    other_sites: list[str] = [site for site in sites if not any(keyword in site.lower() for keywords in categories.values() for keyword in keywords)]
    if other_sites:
        sites_text += f"**Outros sites ({len(other_sites)}):**\n"
        for site in sorted(other_sites)[:20]:  # Limita a 20
            sites_text += f"• {site}\n"
        if len(other_sites) > 20:
            sites_text += f"  ... e mais {len(other_sites) - 20}\n"
    
    return sites_text

def auto_update_ytdlp() -> None:
    """Tenta atualizar o yt-dlp automaticamente usando pip."""
    try:
        subprocess.run(["python", "-m", "pip", "install", "--upgrade", "yt-dlp"], check=True)
    except Exception as e:
        print(f"[Aviso] Não foi possível atualizar yt-dlp automaticamente: {e}")

def open_browser() -> None:
    """Abre o navegador automaticamente após um pequeno delay para dar tempo ao servidor inicializar."""
    time.sleep(2)  # Aguarda 2 segundos para o servidor inicializar
    try:
        webbrowser.open('http://localhost:7860')
        print("🌐 Navegador aberto automaticamente!")
    except Exception as e:
        print(f"❌ Não foi possível abrir o navegador automaticamente: {e}")
        print("💡 Acesse manualmente: http://localhost:7860")

# Atualizar yt-dlp ao iniciar
auto_update_ytdlp()

# Iniciar thread para abrir o navegador
browser_thread = threading.Thread(target=open_browser, daemon=True)
browser_thread.start()

def get_qualities_ui(url: str, cookies_file: str = None) -> str:
    """Interface para mostrar qualidades disponíveis organizadas para download.

    Args:
        url (str): URL do vídeo.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.

    Returns:
        str: String formatada com as qualidades disponíveis ou uma mensagem de erro.
    """
    if not url.strip():
        return "Por favor, insira uma URL válida."
    
    result: dict = downloader.get_available_qualities(url, cookies_file)
    
    if 'error' in result:
        return f"❌ {result['error']}"
    
    title: str = result['title']
    duration: str = format_duration(result['duration'])
    uploader: str = result['uploader']
    qualities: dict = result.get('qualities', {})
    
    if not qualities:
        return "❌ Nenhuma qualidade disponível encontrada."
    
    qualities_text: str = f"""
    📹 **{title}**
    
    👤 **Canal:** {uploader}
    ⏱️ **Duração:** {duration}
    
    🎯 **Qualidades Disponíveis:**
    """
    
    if isinstance(qualities, dict):
        for height, formats in qualities.items():
            qualities_text += f"\n**{height}p:**\n"
            
            if isinstance(formats, list):
                for fmt in formats:
                    if isinstance(fmt, dict):
                        filesize: str = format_file_size(fmt.get('filesize', 0)) if fmt.get('filesize') else "Desconhecido"
                        fps_info: str = f" ({fmt.get('fps', 'N/A')}fps)" if fmt.get('fps') != 'N/A' else ""
                        format_note: str = f" - {fmt.get('format_note', '')}" if fmt.get('format_note') else ""
                        
                        qualities_text += f"  • {fmt.get('ext', 'N/A').upper()} - {filesize}{fps_info}{format_note}\n"
    else:
        qualities_text += "\n❌ Erro ao processar qualidades disponíveis."
    
    return qualities_text

def get_video_info_ui(url: str, cookies_file: str = None) -> str:
    """Interface para obter e exibir informações detalhadas de um vídeo.

    Args:
        url (str): URL do vídeo.
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.

    Returns:
        str: String formatada com as informações do vídeo ou uma mensagem de erro.
    """
    if not url.strip():
        return "❌ Por favor, insira uma URL válida."

    info = downloader.get_video_info(url, cookies_file)

    if 'error' in info:
        return f"❌ Erro ao obter informações: {info['error']}"

    title = info.get('title', 'N/A')
    uploader = info.get('uploader', 'N/A')
    duration = format_duration(info.get('duration', 0))
    views = f"{info.get('view_count', 0):,}" if info.get('view_count') else 'N/A'
    upload_date = info.get('upload_date', 'N/A')
    description = info.get('description', 'N/A')
    tags = ', '.join(info.get('tags', [])) if info.get('tags') else 'N/A'
    thumbnail = info.get('thumbnail', '')

    output = f"""
    ### ℹ️ Informações do Vídeo

    **Título:** {title}
    **Canal:** {uploader}
    **Duração:** {duration}
    **Visualizações:** {views}
    **Data de Upload:** {upload_date}
    **Descrição:**
    ```
    {description}
    ```
    **Tags:** {tags}
    """
    # Return both the markdown output and the thumbnail URL
    return output, gr.update(value=thumbnail, visible=bool(thumbnail))

def download_specific_quality_ui(url: str, quality_choice: str, cookies_file: str = None, user_agent: str = None, output_path: str = None, progress=gr.Progress()) -> str:

    """
    Interface para download de vídeo com qualidade específica.
    Args:
        url (str): URL do vídeo a ser baixado.
        quality_choice (str): ID da qualidade específica a ser baixada (ex: '137').
        cookies_file (str, optional): Caminho para o arquivo de cookies. Defaults to None.
        user_agent (str, optional): User agent personalizado. Defaults to None.
        output_path (str, optional): Caminho para o diretório de saída. Defaults to None.
        progress (gr.Progress, optional): Objeto de progresso do Gradio. Defaults to gr.Progress().
    Returns:
        str: Mensagem de status do download.
    """
    if not url.strip():
        return "❌ Por favor, insira uma URL válida."
    
    if not quality_choice or quality_choice == "Selecione uma qualidade":
        return "❌ Por favor, selecione uma qualidade."
    
    progress(0, desc="Iniciando download...")
    
    # Usar o novo método para criar o progress hook
    progress_hook = downloader._create_progress_hook(progress)
    
    # Chamar a função de download principal com a qualidade específica
    result = downloader.download_video(url, quality_choice, progress_hook, cookies_file, user_agent, output_path)
    
    if result['success']:
        filename = os.path.basename(result['filename'])
        filesize = format_file_size(result.get('filesize', 0)) if result.get('filesize') else "Desconhecido"
        final_download_path = output_path if output_path else downloader.download_path
        return f"✅ **Download concluído com sucesso!**\n\n📁 **Arquivo:** {filename}\n📹 **Título:** {result['title']}\n💾 **Tamanho:** {filesize}\n🎯 **Qualidade:** {quality_choice}\n📂 **Localização:** {final_download_path}"
    else:
        return f"❌ **Erro no download:** {result['error']}"

# Interface Gradio
with gr.Blocks(
    title="🎬 Baixador de Vídeos Universal - Versão Avançada",
    css="file=style.css"
) as demo:
    
    gr.HTML("""
    <div class="main-header">
        <h1>🎬 Baixador de Vídeos Universal - Versão Avançada</h1>
        <p>Baixe vídeos de qualquer site com funcionalidades avançadas!</p>
    </div>
    """)

    # Configurações Globais
    with gr.Group(elem_classes="global-settings"):
        gr.Markdown("### ⚙️ Configurações Globais")
        with gr.Row():
            global_cookies = gr.File(
                label="🍪 Cookies (opcional)",
                file_types=[".txt", ".cookies"],
                elem_id="global_cookies_input"
            )
            global_user_agent = gr.Textbox(
                label="🌐 User Agent (opcional)",
                placeholder="Deixe vazio para usar automático",
                lines=1,
                elem_id="global_user_agent_input"
            )
            global_output_path = gr.Textbox(
                label="📁 Pasta de Destino",
                placeholder=f"Padrão: {downloader.download_path}",
                lines=1,
                value=downloader.download_path,
                elem_id="global_output_path_input"
            )
    
    with gr.Tabs():
        # Aba de Informações do Vídeo
        with gr.TabItem("ℹ️ Informações do Vídeo"):
            gr.Markdown("### Obtenha detalhes sobre qualquer vídeo antes de baixar")
            
            with gr.Row():
                info_url = gr.Textbox(
                    label="🔗 URL do Vídeo",
                    placeholder="Cole a URL do vídeo aqui...",
                    lines=1
                )
            
            info_btn = gr.Button("🔍 Obter Informações", variant="primary")
            info_output = gr.Markdown(label="📊 Detalhes do Vídeo")
            info_thumbnail = gr.Image(label="Miniatura", show_label=True, visible=False, interactive=False)
            
            info_btn.click(
                fn=get_video_info_ui,
                inputs=[info_url, global_cookies],
                outputs=[info_output, info_thumbnail]
            )

        # Aba de Download Simples
        with gr.TabItem("⬇️ Download Simples"):
            gr.Markdown("### Baixe vídeos individuais com opções de qualidade")
            
            with gr.Row():
                download_url = gr.Textbox(
                    label="🔗 URL do Vídeo",
                    placeholder="Cole a URL do vídeo aqui...",
                    lines=1
                )
                quality_select = gr.Dropdown(
                    choices=[
                        "Melhor qualidade",
                        "4K ou menor",
                        "1080p ou menor",
                        "720p ou menor",
                        "Pior qualidade",
                        "Apenas áudio (MP3)",
                        "Apenas áudio (M4A)"
                    ],
                    value="Melhor qualidade",
                    label="🎯 Qualidade"
                )
            
            download_btn = gr.Button("⬇️ Baixar Vídeo", variant="primary")
            download_output = gr.Markdown(label="📥 Status do Download")
            
            # Barra de progresso visual
            download_progress = gr.Progress()
            
            download_btn.click(
                fn=download_video_ui,
                inputs=[download_url, quality_select, global_cookies, global_user_agent, global_output_path],
                outputs=[download_output]
            )
        
        # Aba de Download em Lote
        with gr.TabItem("📦 Download em Lote"):
            gr.Markdown("### Baixe múltiplos vídeos de uma vez, colando uma URL por linha")
            
            with gr.Row():
                batch_urls = gr.Textbox(
                    label="🔗 URLs dos Vídeos",
                    placeholder="Cole uma URL por linha aqui...",
                    lines=5
                )
            
            with gr.Row():
                batch_quality = gr.Dropdown(
                    choices=[
                        "Melhor qualidade",
                        "4K ou menor",
                        "1080p ou menor",
                        "720p ou menor",
                        "Pior qualidade",
                        "Apenas áudio (MP3)",
                        "Apenas áudio (M4A)"
                    ],
                    value="Melhor qualidade",
                    label="🎯 Qualidade"
                )
            
            batch_btn = gr.Button("📦 Baixar em Lote", variant="primary")
            batch_output = gr.Markdown(label="📥 Status do Download em Lote")
            
            # Barra de progresso visual
            batch_progress = gr.Progress()
            
            batch_btn.click(
                fn=batch_download_ui,
                inputs=[batch_urls, batch_quality, global_cookies, global_user_agent, global_output_path],
                outputs=[batch_output]
            )
        
        # Aba de Playlists
        with gr.TabItem("📚 Playlists"):
            gr.Markdown("### Baixe playlists inteiras com facilidade")
            
            with gr.Row():
                playlist_url = gr.Textbox(
                    label="🔗 URL da Playlist",
                    placeholder="Cole a URL da playlist aqui...",
                    lines=1
                )
                playlist_quality = gr.Dropdown(
                    choices=[
                        "Melhor qualidade",
                        "4K ou menor",
                        "1080p ou menor",
                        "720p ou menor",
                        "Pior qualidade",
                        "Apenas áudio (MP3)",
                        "Apenas áudio (M4A)"
                    ],
                    value="Melhor qualidade",
                    label="🎯 Qualidade"
                )
            
            playlist_btn = gr.Button("📚 Baixar Playlist", variant="primary")
            playlist_output = gr.Markdown(label="📥 Status do Download da Playlist")
            
            # Barra de progresso visual
            playlist_progress = gr.Progress()
            
            playlist_btn.click(
                fn=download_playlist_ui,
                inputs=[playlist_url, playlist_quality, global_cookies, global_user_agent, global_output_path],
                outputs=[playlist_output]
            )
        
        # Aba de Formatos Disponíveis
        with gr.TabItem("📋 Formatos Disponíveis"):
            gr.Markdown("### Veja todos os formatos de vídeo e áudio disponíveis para download")
            
            with gr.Row():
                formats_url = gr.Textbox(
                    label="🔗 URL do Vídeo",
                    placeholder="Cole a URL do vídeo aqui...",
                    lines=1
                )
            
            formats_btn = gr.Button("📋 Listar Formatos", variant="primary")
            formats_output = gr.Markdown(label="📊 Formatos Disponíveis")
            
            formats_btn.click(
                fn=get_formats_ui,
                inputs=[formats_url, global_cookies],
                outputs=[formats_output]
            )
        
        # Aba de Qualidades Disponíveis
        with gr.TabItem("🎯 Qualidades Disponíveis"):
            gr.Markdown("### Veja e escolha qualidades específicas para download")
            
            with gr.Row():
                qualities_url = gr.Textbox(
                    label="🔗 URL do Vídeo",
                    placeholder="Cole a URL do vídeo aqui...",
                    lines=1
                )
            
            qualities_btn = gr.Button("🎯 Mostrar Qualidades", variant="primary")
            qualities_output = gr.Markdown(label="📊 Qualidades Disponíveis")
            
            qualities_btn.click(
                fn=get_qualities_ui,
                inputs=[qualities_url, global_cookies],
                outputs=[qualities_output]
            )
            
            gr.Markdown("---")
            gr.Markdown("### Download com Qualidade Específica")
            
            with gr.Row():
                specific_url = gr.Textbox(
                    label="🔗 URL do Vídeo",
                    placeholder="Cole a URL do vídeo aqui...",
                    lines=1
                )
                specific_quality = gr.Textbox(
                    label="🎯 ID da Qualidade",
                    placeholder="Ex: 137, 136, 135... (veja acima)",
                    lines=1
                )
            
            specific_btn = gr.Button("⬇️ Baixar Qualidade Específica", variant="primary")
            specific_output = gr.Markdown(label="📥 Status do Download")
            
            # Barra de progresso visual
            specific_progress = gr.Progress()
            
            specific_btn.click(
                fn=download_specific_quality_ui,
                inputs=[specific_url, specific_quality, global_cookies, global_user_agent, global_output_path],
                outputs=[specific_output]
            )
        
        # Aba de Sites Suportados
        with gr.TabItem("🌐 Sites Suportados"):
            gr.Markdown("### Lista de sites suportados pelo yt-dlp (atualizada automaticamente)")
            
            sites_btn = gr.Button("🌐 Mostrar Sites Suportados", variant="primary")
            sites_output = gr.Markdown(label="📊 Sites Suportados")
            
            sites_btn.click(
                fn=get_supported_sites_ui,
                inputs=[],
                outputs=[sites_output]
            )
    

if __name__ == "__main__":
    print("🚀 Iniciando Baixador de Vídeos Universal - Versão Avançada")
    print("📡 Servidor iniciando em: http://localhost:7860")
    print("🌐 O navegador será aberto automaticamente em alguns segundos...")
    print("⏹️  Pressione Ctrl+C para parar o servidor")
    print("-" * 60)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    ) 