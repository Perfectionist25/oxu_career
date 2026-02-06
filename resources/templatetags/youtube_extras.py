from django import template
import re
import requests
from requests.exceptions import RequestException

register = template.Library()

@register.filter
def youtube_id(url):
    """
    Extracts the YouTube video ID from various YouTube URL formats.
    """
    if not url:
        return ""
    # Remove URL parameters
    url = url.split('?')[0]
    url = url.split('&')[0]
    # Match youtu.be/VIDEO_ID
    match = re.search(r"youtu\.be/([\w-]{11})", url)
    if match:
        return match.group(1)
    # Match youtube.com/watch?v=VIDEO_ID
    match = re.search(r"v=([\w-]{11})", url)
    if match:
        return match.group(1)
    # Match youtube.com/embed/VIDEO_ID
    match = re.search(r"embed/([\w-]{11})", url)
    if match:
        return match.group(1)
    # Match youtube.com/shorts/VIDEO_ID
    match = re.search(r"shorts/([\w-]{11})", url)
    if match:
        return match.group(1)
    return ""


@register.simple_tag
def youtube_embed_allowed(url):
    """Return True if YouTube oEmbed endpoint accepts the URL (embed allowed).

    This does a small network request to YouTube's oEmbed endpoint. It may
    fail due to network issues; in that case we conservatively return False.
    """
    if not url:
        return False
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"format": "json", "url": url},
            timeout=2,
            headers={"User-Agent": "oxu_career/1.0"},
        )
        return resp.status_code == 200
    except RequestException:
        return False
