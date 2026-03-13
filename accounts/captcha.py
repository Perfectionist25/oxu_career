import random

from django.utils.translation import gettext_lazy as _


LOGIN_CAPTCHA_OPERAND_A_KEY = "login_captcha_operand_a"
LOGIN_CAPTCHA_OPERAND_B_KEY = "login_captcha_operand_b"
LOGIN_CAPTCHA_RESULT_KEY = "login_captcha_result"


def _has_request_session(request):
    return bool(request and hasattr(request, "session"))


def build_login_captcha_question(request):
    if not _has_request_session(request):
        return _("Security question")

    operand_a = request.session.get(LOGIN_CAPTCHA_OPERAND_A_KEY)
    operand_b = request.session.get(LOGIN_CAPTCHA_OPERAND_B_KEY)
    if operand_a is None or operand_b is None:
        return _("Security question")
    return _("What is %(a)s + %(b)s?") % {"a": operand_a, "b": operand_b}


def rotate_login_captcha(request):
    if not _has_request_session(request):
        return _("Security question")

    operand_a = random.randint(1, 9)
    operand_b = random.randint(1, 9)
    request.session[LOGIN_CAPTCHA_OPERAND_A_KEY] = operand_a
    request.session[LOGIN_CAPTCHA_OPERAND_B_KEY] = operand_b
    request.session[LOGIN_CAPTCHA_RESULT_KEY] = operand_a + operand_b
    request.session.modified = True
    return build_login_captcha_question(request)


def ensure_login_captcha(request):
    if not _has_request_session(request):
        return _("Security question")

    if request.session.get(LOGIN_CAPTCHA_RESULT_KEY) is None:
        return rotate_login_captcha(request)
    return build_login_captcha_question(request)


def validate_login_captcha(request, answer):
    if not _has_request_session(request):
        return False

    expected = request.session.get(LOGIN_CAPTCHA_RESULT_KEY)
    if expected is None:
        return False

    try:
        return int(answer) == int(expected)
    except (TypeError, ValueError):
        return False
