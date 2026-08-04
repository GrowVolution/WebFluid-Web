{% macro code(label, lang, content) %}`{{ label }}`

```{{ lang }}
{{ content }}
```
{% endmacro %}

{% macro file(label) %}`{{ label }}`
{% endmacro %}
