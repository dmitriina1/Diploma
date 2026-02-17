"""
Универсальный загрузчик видео с разных платформ
================================================

Поддерживаемые платформы:
- YouTube
- VK.video
- Rutube
- OK.ru (Одноклассники)
- Dailymotion
- Любые другие платформы, поддерживаемые yt-dlp

Используется yt-dlp - универсальный загрузчик видео
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yt_dlp
import logging

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Универсальный загрузчик видео с разных платформ"""
    
    PLATFORM_PATTERNS = {
        'youtube': [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)',
            r'youtube\.com/watch\?v=[\w-]+',
            r'youtu\.be/[\w-]+',
            r'youtube\.com/shorts/[\w-]+'
        ],
        'vk': [
            r'(https?://)?(www\.)?(vk\.com|vkvideo\.ru)',
            r'vk\.com/video',
            r'vkvideo\.ru'
        ],
        'rutube': [
            r'(https?://)?(www\.)?rutube\.ru',
        ],
        'ok': [
            r'(https?://)?(www\.)?ok\.ru/video',
        ],
        'dailymotion': [
            r'(https?://)?(www\.)?dailymotion\.com',
        ],
        'vimeo': [
            r'(https?://)?(www\.)?vimeo\.com',
        ]
    }
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def detect_platform(self, url: str) -> str:
        """Определить платформу по URL"""
        url_lower = url.lower()
        
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform
        
        return 'unknown'
    
    def is_valid_url(self, url: str) -> bool:
        """Проверка валидности URL"""
        # Базовая проверка URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        if not re.match(url_pattern, url):
            return False
        
        # Проверяем, что это поддерживаемая платформа
        platform = self.detect_platform(url)
        return platform != 'unknown'
    
    def extract_video_id(self, url: str, platform: str) -> str:
        """Извлечение ID видео из URL"""
        if platform == 'youtube':
            patterns = [
                r'(?:v=|/)([a-zA-Z0-9_-]{11})',
                r'youtu\.be/([a-zA-Z0-9_-]{11})',
                r'shorts/([a-zA-Z0-9_-]{11})'
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
        
        elif platform == 'vk':
            # vk.com/video-123456_789012
            match = re.search(r'video(-?\d+_\d+)', url)
            if match:
                return match.group(1)
        
        elif platform == 'rutube':
            # rutube.ru/video/abc123def456/
            match = re.search(r'video/([a-f0-9]+)', url)
            if match:
                return match.group(1)
        
        elif platform == 'ok':
            # ok.ru/video/123456789
            match = re.search(r'video/(\d+)', url)
            if match:
                return match.group(1)
        
        # Fallback - хеш URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    async def download_video_audio(
        self,
        url: str,
        video_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Скачать аудио и субтитры с видео
        
        Returns:
            {
                'audio_path': str,
                'video_title': str,
                'video_id': str,
                'platform': str,
                'subtitles': List[Dict],
                'has_subtitles': bool,
                'duration': int,
                'thumbnail': str
            }
        """
        platform = self.detect_platform(url)
        
        if not video_id:
            video_id = self.extract_video_id(url, platform)
        
        logger.info(f"📥 Downloading from {platform}: {url}")
        
        audio_path = self.temp_dir / f"{video_id}.mp3"
        subs_path = self.temp_dir / f"{video_id}.ru.vtt"
        
        # Настройки yt-dlp для универсальной загрузки
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.temp_dir / f'{video_id}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ru'],  # Только русские субтитры
            'subtitlesformat': 'vtt',
            'quiet': False,  # Показываем прогресс
            'no_warnings': False,
            'ignoreerrors': False,
            'nocheckcertificate': True,  # Игнорировать SSL проблемы
            'socket_timeout': 60,  # Увеличенный таймаут 60 сек
            'retries': 10,  # Количество попыток при ошибке
            'fragment_retries': 10,  # Попытки для фрагментов
            'http_chunk_size': 10485760,  # 10 МБ чанки
            # Для VK.video нужны куки (если видео приватное)
            # 'cookiefile': 'cookies.txt',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"🔍 Extracting info from {platform}...")
                info = ydl.extract_info(url, download=True)
                
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')
                
                logger.info(f"✅ Downloaded: {video_title} ({duration}s)")
        
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            raise Exception(f"Failed to download video from {platform}: {str(e)}")
        
        # Парсим субтитры
        subtitles = []
        has_subtitles = False
        
        # Проверяем разные варианты файлов субтитров
        subtitle_files = [
            subs_path,
            self.temp_dir / f"{video_id}.en.vtt",
            self.temp_dir / f"{video_id}.vtt"
        ]
        
        for sub_file in subtitle_files:
            if sub_file.exists():
                subtitles = self._parse_vtt_subtitles(sub_file)
                has_subtitles = len(subtitles) > 0
                if has_subtitles:
                    logger.info(f"📝 Loaded {len(subtitles)} subtitle segments")
                    break
        
        if not has_subtitles:
            logger.warning("⚠️ No subtitles found for this video")
        
        return {
            'audio_path': str(audio_path),
            'video_title': video_title,
            'video_id': video_id,
            'platform': platform,
            'url': url,
            'subtitles': subtitles,
            'has_subtitles': has_subtitles,
            'duration': duration,
            'thumbnail': thumbnail
        }
    
    def _parse_vtt_subtitles(self, vtt_path: Path) -> List[Dict[str, Any]]:
        """Парсинг VTT субтитров"""
        subtitles = []
        
        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Простой парсинг VTT
            lines = content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Ищем таймкод
                if '-->' in line:
                    times = line.split('-->')
                    start_time = times[0].strip()
                    end_time = times[1].strip() if len(times) > 1 else start_time
                    
                    # Следующая строка - текст
                    i += 1
                    text_parts = []
                    
                    while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                        text_parts.append(lines[i].strip())
                        i += 1
                    
                    text = ' '.join(text_parts)
                    if text:
                        subtitles.append({
                            'start': start_time,
                            'end': end_time,
                            'text': text
                        })
                
                i += 1
        
        except Exception as e:
            logger.warning(f"⚠️ VTT parsing error: {e}")
        
        return subtitles
    
    def get_platform_info(self, url: str) -> Dict[str, str]:
        """Получить информацию о платформе"""
        platform = self.detect_platform(url)
        
        platform_names = {
            'youtube': 'YouTube',
            'vk': 'VK Video',
            'rutube': 'Rutube',
            'ok': 'OK.ru',
            'dailymotion': 'Dailymotion',
            'vimeo': 'Vimeo',
            'unknown': 'Unknown Platform'
        }
        
        platform_icons = {
            'youtube': '🎬',
            'vk': '🔵',
            'rutube': '🎥',
            'ok': '🟠',
            'dailymotion': '🎞️',
            'vimeo': '💙',
            'unknown': '📹'
        }
        
        return {
            'platform': platform,
            'platform_name': platform_names.get(platform, 'Unknown'),
            'platform_icon': platform_icons.get(platform, '📹')
        }


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    async def test():
        downloader = VideoDownloader(Path("/tmp/test"))
        
        # Тест YouTube
        result = await downloader.download_video_audio(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        print(result)
    
    asyncio.run(test())
