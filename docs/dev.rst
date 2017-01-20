
===========
Development
===========


With docker
===========


Build image


.. code-block:: bash

   docker build -t pg_bawler .


Run tests


.. code-block:: bash

   docker run \
      -u root \
      -v $(pwd):/opt/pg_bawler \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -t pg_bawler \
      /bin/sh runtests.sh



With local virtualenv
=====================


.. note:: Make sure that you are using python 3.5+

Create virtualenv for example with `venv <https://docs.python.org/3/library/venv.html>`_.

.. code-block:: bash

   python3 -m venv /path/to/new/virtual/environment


Activate created environment

.. code-block:: bash

   source /path/to/new/virtua/environment/bin/activate


With activated virtual environment, install dependencies

.. code-block:: bash

   pip install \
       -r requirements.txt \
       -r test-requirements.txt \
       -r dev-requirements.txt


To verify the installation run the tests

.. code-block:: bash

   ./runtests.sh
