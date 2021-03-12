
import operator
import functools

import json

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
def status_badge(text):
    status_to_badge_class = {
        "successful" : "text-success border-success",
        "unstable" :   "text-warning border-warning",
        "failed" :     "text-danger border-danger",
        "broken" :     "text-danger border-danger",
        "unknown" :    "text-secondary border-secondary",
        "skip" :       "text-info border-info"
    }
    status_to_icon_class = {
        "successful" : "bi-check-circle-fill",
        "unstable" :   "bi-exclamation-circle-fill",
        "failed" :     "bi-x-circle-fill",
        "broken" :     "bi-dash-circle-fill",
        "unknown" :    "bi-question-circle-fill",
        "skip" :       "bi-slash-circle-fill"
    }

    badge_class = status_to_badge_class.get(text, "text-secondary border-secondary")
    icon_class = status_to_icon_class.get(text, "bi-info-circle")

    safe_text = f'<span class="badge border {badge_class}"><i class="bi {icon_class}"></i> {text}</span>'
    return mark_safe(safe_text)

@register.filter
def create_html_representation(data, valuetype):
    if data is None:
        return "None"
    if valuetype == "string":
        return data
    if valuetype == "integer":
        return str(data)
    if valuetype == "float":
        return str(data)
    if valuetype == "list": # backward-compatibility
        out = " <br> ".join(str(data).strip("[]").split(","))
        return mark_safe(out)
    if valuetype == "ndarray":
        shape = data['shape']
        entries = [str(create_html_representation(entry['data'], entry['type'])) for entry in data['entries']]

        tensor_order = len(shape)
        total_count = functools.reduce(operator.mul, shape, 1)

        inconsistent = total_count != len(entries)

        if inconsistent or tensor_order > 3:
            # Just print a 1D list of all available values
            size_0 = len(entries)
            size_1 = 1
            size_2 = 1
            out = f"Tensor-{tensor_order} {shape}:"
        else:
            size_0 = shape[0] if tensor_order >= 1 else 1
            size_1 = shape[1] if tensor_order >= 2 else 1
            size_2 = shape[2] if tensor_order >= 3 else 1
            out = ""

        for k in range(size_2):
            out += '<table class="ndarray-value">'
            for i in range(size_0):
                out += "<tr>"
                for j in range(size_1):
                    index = k*(size_0*size_1)+i*size_1+j
                    out += f"<td>{entries[index]}</td>"
                out += "</tr>"
            out += "</table>"

        return mark_safe(out)
    if valuetype == "image":
        out = f"<img src='data:image/png;base64, {data}' />"
        return mark_safe(out)
    return str(data)

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
        replaced_value = prop.display_replace.replace("{VALUE}", str(value))
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
def as_dynamic_bootstrap_field(field):
    if not isinstance(field, forms.BoundField):
        return field
    attributes = {'field': field}
    template = get_template("dtf/bootstrap/field_dynamic.html")
    context = Context(attributes).flatten()
    return template.render(context)

@register.filter
def add_bootstrap_class(field, add_class=""):
    if not isinstance(field, forms.BoundField):
        return field

    bootstrap_classes_per_widget = {
        "text": "form-control",
        "checkbox" : "form-check-input",
        "url" : "form-control",
        "textarea" : "form-control",
    }

    current_class = field.field.widget.attrs.get('class', None)
    bootstrap_class = bootstrap_classes_per_widget.get(field.widget_type, None)
    new_class = ' '.join(filter(None, [current_class, bootstrap_class, add_class]))
    return field.as_widget(attrs={'class' : new_class})

@register.filter
def format_json(data):
    return json.dumps(data, indent=2)

@register.filter
def print_webhook_log_response(log_entry):
    lower_case_header = dict((k.lower(),v) for k,v in log_entry.response_headers.items())
    if 'content-type' in lower_case_header and lower_case_header['content-type'].lower() == "application/json":
        try:
            return format_json(json.loads(log_entry.response_data))
        except:
            return log_entry.response_data
    return log_entry.response_data

@register.filter(is_safe=True)
def to_js_dict(data):
    return mark_safe(json.dumps(data))