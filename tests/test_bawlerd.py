import io
import os
from textwrap import dedent

from pg_bawler import bawlerd


class TestBawlerdConfig:

    def test_build_config_location_list(self):
        assert not bawlerd.conf.build_config_location_list(locations=())

        user_conf = os.path.join(
            os.path.expanduser('~'),
            bawlerd.conf.DEFAULT_CONFIG_FILENAME)

        system_conf = os.path.join(
            '/etc/pg_bawler',
            bawlerd.conf.DEFAULT_CONFIG_FILENAME)

        assert user_conf in bawlerd.conf.build_config_location_list()
        assert system_conf in bawlerd.conf.build_config_location_list()

    def test__load_file(self):
        config = bawlerd.conf._load_file(io.StringIO(dedent("""\
            logging:
              formatters:
                standard:
                  format: \"%(asctime)s %(levelname)s] %(name)s: %(message)s\"
              handlers:
                default:
                  level: "INFO"
                  formatter: standard
                  class: logging.StreamHandler
              loggers:
                "":
                  handlers: ["default"]
                  level: INFO
                  propagate: True
        """)))
        assert 'logging' in config
