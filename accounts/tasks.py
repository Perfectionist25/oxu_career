import io
import uuid
import logging

from celery import shared_task
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def compress_avatar_task(self, user_id):
    User = apps.get_model("accounts", "CustomUser")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("compress_avatar_task: user %s does not exist", user_id)
        return False

    if not user.avatar:
        logger.warning("compress_avatar_task: user %s has no avatar to compress", user_id)
        return False

    avatar_name = user.avatar.name
    if avatar_name.lower().endswith(".webp"):
        logger.info("compress_avatar_task: user %s avatar already in WebP", user_id)
        return True

    try:
        with default_storage.open(avatar_name, "rb") as source_file:
            image = Image.open(source_file)
            image = ImageOps.exif_transpose(image)

            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")

            target_size = (512, 512)
            image = ImageOps.fit(image, target_size, method=Image.LANCZOS, centering=(0.5, 0.5))

            buffer = io.BytesIO()
            save_kwargs = {"format": "WEBP", "quality": 75, "method": 6}
            if image.mode == "RGBA":
                save_kwargs["lossless"] = False

            image.save(buffer, **save_kwargs)
            buffer.seek(0)

            new_name = f"{uuid.uuid4().hex}.webp"
            user.avatar.save(new_name, ContentFile(buffer.read()), save=False)
            user.save(update_fields=["avatar"])

        logger.info("compress_avatar_task: user %s avatar compressed into %s", user_id, new_name)
        return True
    except Exception as exc:
        logger.exception("compress_avatar_task: failed to compress avatar for user %s", user_id)
        raise self.retry(exc=exc, countdown=30, max_retries=3)
