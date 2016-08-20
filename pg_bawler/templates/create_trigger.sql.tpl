CREATE TRIGGER {{ trigger_name }}
    AFTER INSERT OR UPDATE OR DELETE ON {{ table_name }}
    FOR EACH ROW EXECUTE PROCEDURE {{ trigger_fn_name }}();


