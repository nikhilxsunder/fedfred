{{ name | underline }}

{% if "." not in objname %}
.. currentmodule:: {{ module }}

.. autofunction:: {{ objname }}
{% else %}
.. autofunction:: {{ module }}.{{ objname }}
{% endif %}