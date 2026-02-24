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
            'skip_unavailable_fragments': True,  # Пропускать недоступные фрагменты
            'http_chunk_size': 10485760,  # 10 МБ чанки
            'concurrent_fragment_downloads': 1,  # По одному фрагменту для VK
            'noprogress': False,
            # Для VK.video нужны куки (если видео приватное)
            # 'cookiefile': 'cookies.txt',
        }
        
        # Специальные настройки для VK
        if platform == 'vk':
            logger.info("🔧 Applying VK-specific download settings...")
            ydl_opts.update({
                # Приоритет: низкое качество = быстрая загрузка
                'format': 'worst[ext=m4a]/worstaudio/bestaudio[filesize<50M]/hls-240/hls-360/worst',
                'extractor_args': {'vk': {'no_fragment_concatenation': True}},
                'http_chunk_size': 0,  # Отключить chunked download
                'concurrent_fragment_downloads': 1,
                'socket_timeout': 60,  # Уменьшенный таймаут
                'retries': 3,  # Меньше попыток
                'fragment_retries': 3,
                'skip_unavailable_fragments': True,
                'ignoreerrors': True,
                'noprogress': True,
                'keepvideo': False,
                'prefer_free_formats': True,
                'max_filesize': 100 * 1024 * 1024,  # Макс 100MB
                'abort_on_error': False,
                'continue_dl': True,  # Продолжить прерванную загрузку
            })
            logger.warning("⚠️ VK downloads may be slow. Consider using YouTube for better performance.")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"🔍 Extracting info from {platform}...")
                
                # Сначала получаем инфо БЕЗ загрузки для проверки длительности
                info = ydl.extract_info(url, download=False)
                
                video_title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')
                
                # Предупреждение для длинных VK видео
                if platform == 'vk' and duration > 1800:  # > 30 минут
                    logger.warning(f"⚠️ VK video is {duration//60} minutes long. This may take a VERY long time to download.")
                    logger.warning(f"⚠️ Consider using shorter videos or YouTube for faster processing.")
                
                # Ограничение на макс длительность для VK
                if platform == 'vk' and duration > 3600:  # > 60 минут
                    raise Exception(f"VK videos longer than 60 minutes are not supported due to slow download speeds. Video duration: {duration//60} min. Please use YouTube instead.")
                
                logger.info(f"📹 Video: {video_title} ({duration}s)")
                
                # Теперь скачиваем
                logger.info(f"⬇️ Downloading...")
                info = ydl.extract_info(url, download=True)
                
                logger.info(f"✅ Downloaded: {video_title}")
        
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
