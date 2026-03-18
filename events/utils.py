import io
import re

from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _


def generate_qr_png_bytes(payload):
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("qrcode package is required to generate attendance passes.") from exc

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def extract_token_from_payload(raw_value):
    if not raw_value:
        raise ValidationError(_("QR code payload is empty."))

    value = raw_value.strip()
    if _looks_like_attendance_code(value):
        return value.upper()
    raise ValidationError(_("Invalid QR code payload."))


def get_check_in_participation_or_404(event, token):
    participation = event.participations.select_related("user", "checked_in_by").filter(
        attendance_code=str(token).strip().upper()
    ).first()
    if not participation and _looks_like_uuid(token):
        participation = event.participations.select_related("user", "checked_in_by").filter(
            qr_token=token
        ).first()
    if not participation:
        raise Http404(_("Participant not found for this QR code."))
    return participation


def _looks_like_attendance_code(value):
    return bool(re.fullmatch(r"EVT-[A-Z0-9]{10}", str(value).strip().upper()))


def _looks_like_uuid(value):
    try:
        import uuid

        uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return False
    return True
