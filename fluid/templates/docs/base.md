---
title: "{% block doc_title %}{% endblock %}"
section: "{% block doc_section %}{% endblock %}"
framework: WebFluid
package: webfluid
version: "{{ version }}"
stage: "{{ stage }}"
released: "{{ date }}"
canonical: "{{ canonical }}"
html: "{{ html_url }}"
audience: ai-agent
format: markdown
---

# {% block heading %}{{ self.doc_title() }}{% endblock %}

{% block summary %}{% endblock %}
{% block body %}{% endblock %}

---

## Navigation

{{ nav }}
