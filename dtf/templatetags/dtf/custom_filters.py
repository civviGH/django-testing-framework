from django import template
from django.utils.safestring import mark_safe

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