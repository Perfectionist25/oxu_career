import mimetypes
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


CERTIFICATE_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
CERTIFICATE_ALLOWED_EXTENSIONS = CERTIFICATE_IMAGE_EXTENSIONS | {"pdf"}
CERTIFICATE_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}
CERTIFICATE_CONTENT_TYPE_BY_EXTENSION = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
}


def get_student_certificate_max_upload_size():
    return int(
        getattr(settings, "STUDENT_CERTIFICATE_MAX_UPLOAD_SIZE", 8 * 1024 * 1024)
    )


@deconstructible
class StudentCertificateStorage(FileSystemStorage):
    @property
    def base_location(self):
        return getattr(
            settings,
            "PROTECTED_MEDIA_ROOT",
            Path(settings.BASE_DIR) / "protected_media",
        )

    @property
    def base_url(self):
        return None


def student_certificate_upload_to(instance, filename):
    extension = Path(filename).suffix.lower().lstrip(".")
    safe_extension = extension if extension in CERTIFICATE_ALLOWED_EXTENSIONS else "bin"
    timestamp = timezone.now()
    student_pk = getattr(instance.student, "pk", None) or getattr(instance.student, "id", None)
    return (
        f"student_certificates/student_{student_pk}/"
        f"{timestamp:%Y/%m}/{uuid.uuid4().hex}.{safe_extension}"
    )


def get_certificate_content_type(file_name):
    extension = Path(file_name).suffix.lower().lstrip(".")
    if extension in CERTIFICATE_CONTENT_TYPE_BY_EXTENSION:
        return CERTIFICATE_CONTENT_TYPE_BY_EXTENSION[extension]
    guessed_type, _encoding = mimetypes.guess_type(file_name)
    return guessed_type or "application/octet-stream"


def _preserve_position(uploaded_file):
    if not hasattr(uploaded_file, "tell"):
        return None
    try:
        return uploaded_file.tell()
    except (AttributeError, OSError, ValueError):
        return None


def _seek(uploaded_file, position):
    if not hasattr(uploaded_file, "seek"):
        return
    try:
        uploaded_file.seek(position)
    except (AttributeError, OSError, ValueError):
        pass


def _validate_pdf_signature(uploaded_file):
    original_position = _preserve_position(uploaded_file)
    _seek(uploaded_file, 0)
    header = uploaded_file.read(4)
    _seek(uploaded_file, 0 if original_position is None else original_position)

    if header != b"%PDF":
        raise ValidationError(_("Upload a valid PDF file."))


def _validate_image_file(uploaded_file):
    original_position = _preserve_position(uploaded_file)
    _seek(uploaded_file, 0)

    try:
        image = Image.open(uploaded_file)
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError(_("Upload a valid image file."))
    finally:
        _seek(uploaded_file, 0 if original_position is None else original_position)


def validate_student_certificate_file(uploaded_file):
    if not uploaded_file:
        return

    extension = Path(uploaded_file.name).suffix.lower().lstrip(".")
    if extension not in CERTIFICATE_ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(CERTIFICATE_ALLOWED_EXTENSIONS))
        raise ValidationError(
            _("Unsupported file format. Allowed formats: %(formats)s.")
            % {"formats": allowed}
        )

    max_size = get_student_certificate_max_upload_size()
    if uploaded_file.size and uploaded_file.size > max_size:
        raise ValidationError(
            _("File size must not exceed %(size)s MB.")
            % {"size": int(max_size / (1024 * 1024))}
        )

    content_type = (
        getattr(uploaded_file, "content_type", None)
        or get_certificate_content_type(uploaded_file.name)
    )
    if content_type and content_type.lower() not in CERTIFICATE_ALLOWED_CONTENT_TYPES:
        raise ValidationError(_("Unsupported file content type."))

    if extension == "pdf":
        _validate_pdf_signature(uploaded_file)
        return

    _validate_image_file(uploaded_file)


def can_employer_view_student_certificates(employer_user, student_user):
    if not getattr(employer_user, "is_authenticated", False):
        return False

    if getattr(employer_user, "is_staff", False) or getattr(employer_user, "is_superuser", False):
        return True

    if getattr(employer_user, "is_admin", False):
        return True

    if employer_user == student_user:
        return True

    if not getattr(employer_user, "is_employer", False):
        return False

    from jobs.models import JobApplication

    return JobApplication.objects.filter(
        user=student_user,
        job__company__owner=employer_user,
    ).exists()


def can_user_view_student_certificate(user, certificate):
    if not getattr(user, "is_authenticated", False):
        return False

    if not certificate.student:
        return False

    if certificate.student.id == user.id:
        return True

    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True

    if getattr(user, "is_admin", False):
        return True

    if not certificate.is_active:
        return False

    return can_employer_view_student_certificates(user, certificate.student.user)


def get_viewable_student_certificates_queryset(user, student_user):
    queryset = student_user.certificates.order_by("-uploaded_at")

    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if student_user.id == user.id:
        return queryset

    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return queryset

    if getattr(user, "is_admin", False):
        return queryset

    if can_employer_view_student_certificates(user, student_user):
        return queryset.filter(is_active=True)

    return queryset.none()
