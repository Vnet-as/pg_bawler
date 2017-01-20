
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
