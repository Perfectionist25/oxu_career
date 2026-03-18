import io
from urllib.parse import parse_qs, urlparse

from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def build_attendance_url(request, participation):
    path = reverse(
        "events:admin_event_check_in_token",
        kwargs={"pk": participation.event.pk, "token": participation.qr_token},
    )
    return request.build_absolute_uri(path)


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
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        path_bits = [bit for bit in parsed.path.split("/") if bit]
        if path_bits:
            candidate = path_bits[-1]
            if _looks_like_uuid(candidate):
                return candidate
        query_params = parse_qs(parsed.query)
        token_values = query_params.get("token", [])
        if token_values and _looks_like_uuid(token_values[0]):
            return token_values[0]
    if _looks_like_uuid(value):
        return value
    raise ValidationError(_("Invalid QR code payload."))


def get_check_in_participation_or_404(event, token):
    participation = event.participations.select_related("user", "checked_in_by").filter(
        qr_token=token
    ).first()
    if not participation:
        raise Http404(_("Participant not found for this QR code."))
    return participation


def _looks_like_uuid(value):
    try:
        import uuid

        uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return False
    return True
