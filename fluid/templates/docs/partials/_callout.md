{% macro callout(msg) %}> {{ msg.split() | join(' ') }}{% endmacro %}

{% macro success(msg) %}> **OK** — {{ msg.split() | join(' ') }}{% endmacro %}

{% macro warning(msg) %}> **WARNING** — {{ msg.split() | join(' ') }}{% endmacro %}

{% macro danger(msg) %}> **DANGER** — {{ msg.split() | join(' ') }}{% endmacro %}

{% macro info(msg) %}> **NOTE** — {{ msg.split() | join(' ') }}{% endmacro %}

{% macro rule(msg) %}> **RULE** — {{ msg.split() | join(' ') }}{% endmacro %}

{% macro bug(msg) %}> **KNOWN BUG** — {{ msg.split() | join(' ') }}{% endmacro %}
