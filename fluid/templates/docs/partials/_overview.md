{% macro feature(title, description) %}
### + {{ title }}

{{ description.split() | join(' ') }}
{% endmacro %}

{% macro fix(title, description) %}
### ✓ {{ title }}

{{ description.split() | join(' ') }}
{% endmacro %}

{% macro bug(title, description) %}
### ! {{ title }}

{{ description.split() | join(' ') }}
{% endmacro %}

{% macro break(title, description) %}
### ✕ {{ title }}

{{ description.split() | join(' ') }}
{% endmacro %}
