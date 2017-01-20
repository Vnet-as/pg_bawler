
============
Walk–through
============


Prepare `PostgreSQL <https://www.postgresql.org/>`_ database
============================================================

In this tutorial we will use `Docker <http://www.docker.com/>`_ for running
fresh PostgreSQL instance and so that we can throw it away once we are done.


To run dockerized PostgreSQL:

.. code-block:: bash

        $ docker run --name bawler-tutorial -d postgres


Let's get the container's IP address so we can connect to it.


.. code-block:: bash

        $ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' bawler-tutorial
        172.18.0.4


Now let's ensure that PostgreSQL is running and we can connect to it. For this
we need ``psql``. Install it using your system package manger.

.. code-block:: bash

    $ apt-get install postgresql-client


Prepare environment variables so we don't need to repeat connection CLI args
with every ``psql`` call


.. code-block:: bash

        $ export PGUSER=postgres
        $ export PGHOST=172.18.0.4


Check out that it's working


.. code-block:: bash

        $ psql -c 'SELECT 1'
         ?column?
        ----------
                1
        (1 row)


Create tutorial table ``foo``:


.. code-block:: bash

        $ cat <<EOF | psql
        CREATE TABLE foo (
          id serial primary key,
          name text,
          number integer,
          created timestamp
        )
        EOF
        CREATE TABLE



Trigger installation
====================

You can always write your own trigger or procedure which will either use the
`NOTIFY <https://www.postgresql.org/docs/current/static/sql-notify.html>`_
command or the ``pg_notify`` function to send an event to all the listeners.

Or you can generate one by using ``pg_bawler.gen_sql``:


.. code-block:: bash

        $ python -m pg_bawler.gen_sql foo


This command will generate function and trigger code like:


.. code-block:: plpgsql

        CREATE OR REPLACE FUNCTION bawler_trigger_fn_foo() RETURNS TRIGGER AS $$
            DECLARE
                row RECORD;
            BEGIN
                IF (TG_OP = 'DELETE')
                THEN
                        row := OLD;
                ELSE
                        row := NEW;
                END IF;
                PERFORM pg_notify('foo', TG_OP || ' ' || to_json(row)::text);
                RETURN row;
            END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS bawler_trigger_foo ON foo;

        CREATE TRIGGER bawler_trigger_foo
            AFTER INSERT OR UPDATE OR DELETE ON foo
            FOR EACH ROW EXECUTE PROCEDURE bawler_trigger_fn_foo();


To install this trigger just pipe generated code to ``psql``:

.. code-block:: bash

        $ python -m pg_bawler.gen_sql foo | psql


Running pg_bawler listener
==========================

Now we are running containered PostgreSQL in container named
``bawler-tutorial``.
Let's start ``pg_bawler.listener`` in one terminal and insert a row into the ``foo`` table from another terminal.

To start ``pg_bawler.listener`` we'll use IP address of ``bawler-tutorial``
container and default PostgreSQL username and database name.


.. code-block:: bash

        $ python -m pg_bawler.listener --dsn "dbname=postgres user=postgres host=172.18.0.2" foo



Now to insert row to table ``foo`` execute:

.. code-block:: bash

        $ cat <<EOF | psql
        INSERT INTO foo (name, number, created) values ('Michal Kuffa', '1', '2016-10-01'::timestamp);
        EOF


If everything's working, you should see in ``pg_bawler.listener``'s terminal something like::

        [2016-11-02 21:52:42,266][pg_bawler.listener][INFO]: Received notification #1 pid 2964 from channel foo: INSERT {"id":3,"name":"Michal","number":1,"created":"2016-10-01T00:00:00"}


This is behaviour of default handler, just log the notification.


More information
================

* `PostgreSQL docker image <https://hub.docker.com/_/postgres/>`_
