{{ name | underline }}

{% if "." not in objname %}
.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :no-members:
{% else %}
.. autoclass:: {{ module }}.{{ objname }}
   :no-members:
{% endif %}

{% if methods %}
Methods
-------

.. autosummary::
   :toctree:
   :template: autosummary/method.rst
   :nosignatures:
   {% for item in methods %}
   {{ objname }}.{{ item }}
   {% endfor %}
{% endif %}

{% if attributes %}
Attributes
----------

.. autosummary::
   :toctree:
   :template: autosummary/attribute.rst
   :nosignatures:
   {% for item in attributes %}
   {{ objname }}.{{ item }}
   {% endfor %}
{% endif %}
