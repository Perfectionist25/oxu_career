from django import template

from core.system_notifications import get_visible_system_notifications


register = template.Library()


@register.inclusion_tag("_inc/system_notifications.html", takes_context=True)
def render_system_notifications(context):
    request = context.get("request")
    return {
        "request": request,
        "system_notifications": get_visible_system_notifications(request),
    }
