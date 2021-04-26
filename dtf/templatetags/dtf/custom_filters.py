from django import template
from django.template import Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django import forms

from dtf.settings import STATUS_TEXT_COLORS

register = template.Library()

@register.filter
def color_status_text(text):
    color = STATUS_TEXT_COLORS.get(text)
    safe_text = f'<span style="color:{color}">{text}</span>'
    return mark_safe(safe_text)

@register.filter
def create_html_representation(text, valuetype):
    if text is None:
        return "None"
    if valuetype in ["integer", "float", "string"]:
        return text
    if valuetype == "list":
        out = " <br> ".join(str(text).strip("[]").split(","))
        return mark_safe(out)
    if valuetype == "image":
        out = f"<img src='data:image/png;base64, {text}' />"
        return mark_safe(out)
    return str(valuetype) + " I DO NOT KNOW THIS VALUETYPE!"

@register.filter
def parse_json(text):
    if len(text) == 0:
        return ""
    out = ""
    sorted_text = {k:text[k] for k in sorted(text.keys())}
    for k,v in sorted_text.items():
        out += f"<span class='infospan'>{k}</span>"
        out += f"<span class='infospan'>{v}</span>"
    return mark_safe(out)

@register.filter
def parse_json_table(text):
    if len(text) == 0:
        return ""
    out = '<table class="infotable">'
    # out+='<tr><th>Key</th><th>Value</th></tr>'
    for k,v in text.items():
        out+="<tr>"
        out+=f"<td>{k}</td>"
        out+=f"<td>{v}</td>"
        out+="</tr>"
    out+="</table>"
    return mark_safe(out)

@register.filter
def submission_property(prop, submission):
    value = submission.info.get(prop.name, None)
    if value is None:
        return ""

    if len(prop.display_replace) > 0:
        replaced_value = prop.display_replace.replace("{VALUE}", value)
    else:
        replaced_value = value

    if prop.display_as_link:
        return mark_safe(f'<a href="{replaced_value}">{value}</a>')
    else:
        return replaced_value

@register.filter
def as_bootstrap_field(field):
    if not isinstance(field, forms.BoundField):
        return field
    attributes = {'field': field}
    template = get_template("dtf/bootstrap/field.html")
    context = Context(attributes).flatten()
    return template.render(context)

@register.filter
def add_bootstrap_class(field, add_class=""):
    if not isinstance(field, forms.BoundField):
        return field

    bootstrap_classes_per_widget = {
        "text": "form-control",
        "checkbox" : "form-check-input",
    }

    current_class = field.field.widget.attrs.get('class', None)
    bootstrap_class = bootstrap_classes_per_widget.get(field.widget_type, None)
    new_class = ' '.join(filter(None, [current_class, bootstrap_class, add_class]))
    return field.as_widget(attrs={'class' : new_class})
