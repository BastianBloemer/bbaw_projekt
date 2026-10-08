**Autor:** {% for c in creators -%}{{c.firstName}} {{c.lastName}}{% if not loop.last %}, {% endif %}{%- endfor %}
**Datum:** {{date | format("YYYY-MM-DD")}}

**Zusammenfassung**

{% if abstractNote -%}
{{abstractNote}}
{%- else -%}
*Kein Abstract vorhanden.*
{%- endif %}