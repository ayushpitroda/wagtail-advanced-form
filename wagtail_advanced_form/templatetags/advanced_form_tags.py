from django import template
from django.template import Template, Context
from django.utils.safestring import mark_safe
register = template.Library()

from wagtail.contrib.forms.utils import get_field_clean_name


@register.filter
def clean_label(value):
    return get_field_clean_name(value)


@register.simple_tag(takes_context=True)
def get_form_context(context, form_page):
    request = context['request']

    if request.method == "POST" and request.POST.get("form_id") == str(form_page.id):
        form = form_page.get_form(request.POST, request.FILES)

        if form.is_valid():
            form_page.process_form_submission(form)

            return {
                "form": None,
                "success": True,
                "thank_you_text": form_page.thank_you_text,
            }
    else:
        form = form_page.get_form()

    conditional_rules = form_page.get_context(request=request).get('conditional_rules')

    return {
        "form": form,
        "success": False,
        "thank_you_text": None,
        "conditional_rules": conditional_rules,
    }
