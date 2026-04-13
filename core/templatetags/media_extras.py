from pathlib import Path
from urllib.parse import quote

from django import template
from django.conf import settings

from PIL import Image

register = template.Library()


@register.filter(name="optimized_media")
def optimized_media(file_field, size="640x360"):
    """Return a resized media URL for list previews, preserving full quality elsewhere."""
    if not file_field:
        return ""

    file_url = getattr(file_field, "url", None)
    file_path = getattr(file_field, "path", None)
    if not file_url or not file_path:
        return file_url or ""

    try:
        width, height = [int(value) for value in str(size).lower().split("x", 1)]
    except (ValueError, TypeError):
        return file_url

    source_path = Path(file_path)
    if not source_path.exists() or source_path.stat().st_size == 0:
        return file_url

    optimized_root = Path(settings.MEDIA_ROOT) / "_optimized"
    optimized_rel_dir = source_path.parent.relative_to(settings.MEDIA_ROOT)
    optimized_dir = optimized_root / optimized_rel_dir
    optimized_dir.mkdir(parents=True, exist_ok=True)

    optimized_name = f"{source_path.stem}_{width}x{height}{source_path.suffix.lower()}"
    optimized_path = optimized_dir / optimized_name

    if not optimized_path.exists() or optimized_path.stat().st_mtime < source_path.stat().st_mtime:
        try:
            with Image.open(source_path) as img:
                img = img.convert("RGB")
                img.thumbnail((width, height), Image.LANCZOS)
                img.save(optimized_path, optimize=True, quality=85)
        except Exception:
            return file_url

    optimized_url = Path(settings.MEDIA_URL) / optimized_path.relative_to(settings.MEDIA_ROOT)
    return quote(str(optimized_url).replace("\\", "/"))
