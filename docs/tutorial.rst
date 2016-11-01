
========
Tutorial
========


Prepare `PostgreSQL <https://www.postgresql.org/>`_ database
============================================================

In this tutorial we will use `Docker <http://www.docker.com/>`_ for running
funky fresh PostgreSQL instance and so that we can throw it away once we are
done.


To run dockerized PostgreSQL::

        $ docker run --name bawler-tutorial -d postgres


Now let's ensure that PostgreSQL is running and we can connect to it::

        $ echo "SELECT 1" | docker run -i --rm --link bawler-tutorial:postgres postgres psql -h postgres -U postgres
         ?column?
        ----------
                1
        (1 row)


Create tutorial table ``foo``::

	$ cat <<EOF | docker run -i --rm --link bawler-tutorial:postgres postgres psql -h postgres -U postgres
	CREATE TABLE foo (
	  id serial primary key,
	  name text,
	  number integer,
	  created timestamp
	)
	EOF
	CREATE TABLE



Trigger installation
--------------------

You can always write your own trigger or procedure which will either use the
`NOTIFY <https://www.postgresql.org/docs/current/static/sql-notify.html>`_
command or the ``pg_notify`` function to send and event to all the listeners.

``pg_bawler.gen_sql``

::

	$ python -m pg_bawler.gen_sql foo
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



Running pg_bawler listener
--------------------------

Now we are running containered PostgreSQL in container named
``bawler-tutorial``. Let's get it's IP address so we are able to connect to it also from local ``pg_bawler``.

::

         $ docker inspect --format '{{ .NetworkSettings.IPAddress }}' bawler-tutorial
         172.18.0.2

Or newer syntax

::

        $ docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' bawler-tutorial
        172.18.0.2


* More information about `PostgreSQL docker image <https://hub.docker.com/_/postgres/>`_
