CREATE OR REPLACE FUNCTION {{ trigger_fn_name }}() RETURNS TRIGGER AS $$
    DECLARE
	row RECORD;
    BEGIN
        IF (TG_OP = 'DELETE')
	THEN
		row := OLD;
	ELSE
		row := NEW;
        END IF;
        PERFORM pg_notify('{{ channel }}', TG_OP || ' ' || to_json(row)::text);
	RETURN row;
    END;
$$ LANGUAGE plpgsql;


