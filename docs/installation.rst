Installation
============

htcie requires Python 3.12+.

Using uv (recommended)
-----------------------

.. code-block:: bash

   uv add htcie

Development install
-------------------

.. code-block:: bash

   git clone <repo>
   cd htcie
   uv sync --extra dev

Running tests
^^^^^^^^^^^^^

.. code-block:: bash

   uv run pytest

Building docs
^^^^^^^^^^^^^

.. code-block:: bash

   uv run python docs/build_docs.py
