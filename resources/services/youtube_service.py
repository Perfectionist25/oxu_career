
import requests
import re
from urllib.parse import urlparse

class YouTubeService:

    @staticmethod
    def extract_video_id(url):
        """Extract YouTube video ID from URL with improved patterns"""
        if not url:
            return None


        url = url.strip()


        patterns = [

            r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',

            r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',

            r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',

            r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',

            r'(?:v=)([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)

                if len(video_id) == 11:
                    return video_id

        return None

    @staticmethod
    def get_video_info(video_id):
        """
        Get video information using YouTube oEmbed API
        No API key required for basic embed check
        """
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"YouTube oEmbed API returned status: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print("YouTube oEmbed API timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"YouTube oEmbed API request error: {e}")
            return None
        except Exception as e:
            print(f"YouTube oEmbed API unexpected error: {e}")
            return None

    @staticmethod
    def get_embed_url(video_id):
        """Generate embed URL with proper parameters"""
        if not video_id:
            return None

        params = [
            'rel=0',
            'modestbranding=1',
            'playsinline=1',
            'enablejsapi=1',
        ]

        return f"https://www.youtube.com/embed/{video_id}?{'&'.join(params)}"

    @staticmethod
    def validate_youtube_url(url):
        """Validate if URL is a proper YouTube URL"""
        if not url:
            return False

        parsed_url = urlparse(url)
        valid_domains = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']

        if parsed_url.netloc.replace('www.', '') not in [domain.replace('www.', '') for domain in valid_domains]:
            return False

        video_id = YouTubeService.extract_video_id(url)
        return video_id is not None