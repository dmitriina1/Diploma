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

    def _build_base_ydl_opts(self, video_id: str) -> Dict[str, Any]:
        """Базовые настройки yt-dlp для всех платформ."""
        opts = {
            'outtmpl': str(self.temp_dir / f'{video_id}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'writesubtitles': True,
            'writeautomaticsub': True,
            # EN часто отдает 429 и может уронить задачу, поэтому загружаем только RU
            'subtitleslangs': ['ru'],
            'subtitlesformat': 'vtt',
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'socket_timeout': 90,
            'retries': 15,
            'fragment_retries': 15,
            'skip_unavailable_fragments': True,
            'http_chunk_size': 10485760,
            'concurrent_fragment_downloads': 1,
            'geo_bypass': True,
            'noprogress': False,
        }

        cookie_file = os.getenv('YTDLP_COOKIE_FILE', '').strip()
        if cookie_file:
            cookie_path = Path(cookie_file)
            if cookie_path.exists():
                opts['cookiefile'] = str(cookie_path)
                logger.info(f"🍪 Using yt-dlp cookies from: {cookie_path}")
            else:
                logger.warning(f"⚠️ YTDLP_COOKIE_FILE is set but file does not exist: {cookie_path}")

        return opts

    def _get_format_strategies(self, platform: str) -> List[str]:
        """Стратегии выбора форматов по платформам (по приоритету)."""
        if platform == 'youtube':
            return [
                # Базовый режим: отдельно аудио, если доступно
                'bestaudio/best',
                # Если отдельных аудиодорожек нет, берём прогрессивный контейнер
                'best[acodec!=none][height<=720]/best[acodec!=none]/best',
                # Последняя попытка
                'worstaudio/worst',
            ]

        if platform == 'vk':
            return [
                'worst[ext=m4a]/worstaudio/bestaudio[filesize<50M]/hls-240/hls-360/worst',
            ]

        return [
            'bestaudio/best',
            'best',
            'worstaudio/worst',
        ]

    def _is_retryable_download_error(self, error_msg: str) -> bool:
        """Определить, стоит ли пробовать следующую стратегию формата."""
        msg = error_msg.lower()
        retry_markers = [
            'requested format is not available',
            'no video formats found',
            'http error 403',
            'precondition check failed',
            'temporarily unavailable',
            'failed to extract',
            'unable to download',
        ]
        return any(marker in msg for marker in retry_markers)

    def _build_download_error(self, platform: str, raw_error: str) -> str:
        """Собрать читаемую ошибку для UI и логов."""
        msg = raw_error.lower()

        if 'requested format is not available' in msg or 'no video formats found' in msg:
            return (
                f"Failed to download video from {platform}: подходящий формат недоступен "
                "(видео может быть ограничено по возрасту/региону или временно недоступно)."
            )

        if "sign in to confirm you're not a bot" in msg or 'captcha' in msg:
            return (
                f"Failed to download video from {platform}: YouTube запросил anti-bot проверку. "
                "Повторите позже или используйте cookies для авторизованной сессии."
            )

        if 'video unavailable' in msg or 'this video is private' in msg:
            return f"Failed to download video from {platform}: видео недоступно или приватное."

        return f"Failed to download video from {platform}: {raw_error}"
    
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
        
        # Базовые настройки yt-dlp + платформа-специфичные стратегии форматов
        ydl_opts = self._build_base_ydl_opts(video_id)
        format_strategies = self._get_format_strategies(platform)

        # Специальные настройки для VK
        if platform == 'vk':
            logger.info("🔧 Applying VK-specific download settings...")
            ydl_opts.update({
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

        video_title = 'Unknown'
        duration = 0
        thumbnail = ''
        last_error = ''
        downloaded = False

        for attempt_idx, format_selector in enumerate(format_strategies, start=1):
            attempt_opts = dict(ydl_opts)
            attempt_opts['format'] = format_selector

            logger.info(
                f"🎯 Download strategy {attempt_idx}/{len(format_strategies)} for {platform}: {format_selector}"
            )

            try:
                with yt_dlp.YoutubeDL(attempt_opts) as ydl:
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
                    logger.info("⬇️ Downloading...")

                    info = ydl.extract_info(url, download=True)
                    video_title = info.get('title', video_title)
                    duration = info.get('duration', duration)
                    thumbnail = info.get('thumbnail', thumbnail)

                    downloaded = True
                    logger.info(f"✅ Downloaded: {video_title}")
                    break

            except yt_dlp.utils.DownloadError as err:
                last_error = str(err)
                logger.warning(
                    f"⚠️ Download strategy {attempt_idx} failed for {platform}: {last_error}"
                )

                if attempt_idx < len(format_strategies):
                    continue

                raise Exception(self._build_download_error(platform, last_error))

            except Exception as err:
                last_error = str(err)
                logger.warning(
                    f"⚠️ Download strategy {attempt_idx} failed for {platform}: {last_error}"
                )

                if attempt_idx < len(format_strategies) and self._is_retryable_download_error(last_error):
                    continue

                raise Exception(self._build_download_error(platform, last_error))

        if not downloaded:
            raise Exception(self._build_download_error(platform, last_error or "Unknown download error"))
        
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
