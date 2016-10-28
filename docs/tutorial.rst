
========
Tutorial
========


Prepare `PostgreSQL <https://www.postgresql.org/>`_ database
============================================================

In this tutorial we will use `Docker <http://www.docker.com/>`_ for running
funky fresh PostgreSQL instance and so that we can throw it away after we are
done.


To run dockerized PostgreSQL::

        $ docker run --name bawler-tutorial -d postgres

Now we are running containered PostgreSQL in container named
``bawler-tutorial``. Let's get it's IP address so we are able to connect to it.

::

         $ docker inspect --format '{{ .NetworkSettings.IPAddress }}' bawler-tutorial
         172.18.0.2

Or newer syntax

::

        $ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' bawler-tutorial
        172.18.0.2



* More information about `PostgreSQL docker image <https://hub.docker.com/_/postgres/>`_
