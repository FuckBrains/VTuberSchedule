from django import template

from webpush.utils import get_templatetag_context

register = template.Library()


@register.filter
@register.inclusion_tag('notify/webpush_switch.html', takes_context=True)
def webpush_switch(context):
    template_context = get_templatetag_context(context)
    return template_context
