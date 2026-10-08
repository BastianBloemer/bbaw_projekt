
{% for annotation in annotations -%}
{% if annotation.annotatedText or annotation.comment -%}
{% if annotation.annotatedText -%}
> {{annotation.annotatedText}}
>
{% endif -%}
> S. {{annotation.pageLabel}} ^{{annotation.id}}
{%- if annotation.tags.length %}

{% for t in annotation.tags %}#{{ t.tag | replace(" ", "-") }} {% endfor %}
{%- endif %}
{%- if annotation.comment %}

**Kommentar:** {{annotation.comment}}
{%- endif %}

---

{% endif -%}
{% endfor %}