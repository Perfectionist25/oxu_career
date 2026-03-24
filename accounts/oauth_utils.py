from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.urls import NoReverseMatch, reverse


OAUTH_REDIRECT_SESSION_KEY = "oauth_redirect_uri"
LOCAL_CALLBACK_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}


def _normalize_uri(uri: str) -> str:
    return (uri or "").rstrip("/") + "/"


def _get_callback_path() -> str:
    try:
        return reverse("oauth_callback")
    except NoReverseMatch:
        return reverse("accounts:oauth_callback")


def _get_hostname(host: str) -> str:
    if not host:
        return ""
    return host.split(":", 1)[0].strip("[]").lower()


def _should_use_https(request) -> bool:
    host = request.get_host()
    hostname = _get_hostname(host)
    if hostname in LOCAL_CALLBACK_HOSTS:
        return request.is_secure()
    return True


def _get_public_host_from_settings() -> str:
    configured_site_url = (getattr(settings, "SITE_URL", "") or "").strip()
    if configured_site_url:
        parsed_site = urlsplit(configured_site_url)
        if parsed_site.netloc and _get_hostname(parsed_site.netloc) not in LOCAL_CALLBACK_HOSTS:
            return parsed_site.netloc
    return ""


def build_oauth_redirect_uri(request=None) -> str:
    if request is None:
        return _normalize_uri(getattr(settings, "OAUTH_REDIRECT_URI", ""))

    request_host = request.get_host()
    request_hostname = _get_hostname(request_host)
    if request_hostname in LOCAL_CALLBACK_HOSTS:
        host = request_host
    else:
        host = _get_public_host_from_settings() or request_host
    if not host:
        return _normalize_uri(getattr(settings, "OAUTH_REDIRECT_URI", ""))

    scheme = "https" if _should_use_https(request) else "http"
    return f"{scheme}://{host}{_get_callback_path()}"


def remember_oauth_redirect_uri(request) -> str:
    redirect_uri = build_oauth_redirect_uri(request)
    request.session[OAUTH_REDIRECT_SESSION_KEY] = redirect_uri
    return redirect_uri


def get_oauth_redirect_uri(request=None) -> str:
    if request is not None:
        stored_redirect = request.session.get(OAUTH_REDIRECT_SESSION_KEY)
        if stored_redirect:
            return _normalize_uri(stored_redirect)
    return build_oauth_redirect_uri(request)


def clear_oauth_redirect_uri(request) -> None:
    if request is not None:
        request.session.pop(OAUTH_REDIRECT_SESSION_KEY, None)


def force_https_uri(uri: str) -> str:
    parsed = urlsplit(_normalize_uri(uri))
    if parsed.scheme == "http":
        return urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, parsed.fragment))
    return urlunsplit(parsed)
