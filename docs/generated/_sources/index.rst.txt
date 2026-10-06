News 4 U documentation
======================

News 4 U is a Django application for readers, journalists, editors, and
curated publishers. This reference describes its role permissions, approval
services, and core data models.

For step-by-step workflows, see the `user guide <../USER_GUIDE.md>`_.
Development setup and operations are covered in `the development guide
<../DEVELOPMENT.md>`_, and the available endpoints are listed in `the API
reference <../API_REFERENCE.md>`_.

Build this documentation from the project root after installing
``docs/requirements.txt``:

.. code-block:: console

   python -m sphinx -b html docs/source docs/generated

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference

