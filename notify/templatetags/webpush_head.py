from django import template
from webpush.utils import get_templatetag_context

register = template.Library()


@register.filter
@register.inclusion_tag('notify/webpush_head_script.html', takes_context=True)
def webpush_head_script(context):
    template_context = get_templatetag_context(context)
    return template_context


@register.filter
@register.inclusion_tag('notify/webpush_head_worker.html', takes_context=True)
def webpush_head_worker(context):
    template_context = get_templatetag_context(context)
    return template_context


@register.filter
@register.inclusion_tag('notify/webpush_head_vapid.html', takes_context=True)
def webpush_head_vapid(context):
    template_context = get_templatetag_context(context)
    return template_context
