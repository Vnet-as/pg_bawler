import os

#: Default name for bawlerd configuration file
DEFAULT_CONFIG_FILENAME = 'pg_bawler.yml'

#: List of location where bawlerd searches for configuration
#: Order matters. Configuration in current working directory takes precedence
#: over configuration from users directory, which takes precedence over system
#: wide configuration.
DEFAULT_CONFIG_LOCATIONS = (
    '/etc/pg_bawler',
    '~',
    os.getcwd(),
)


def build_config_location_list(
    locations=DEFAULT_CONFIG_LOCATIONS,
    filename=DEFAULT_CONFIG_FILENAME
):
    return [
        os.path.join(os.path.expanduser(location), filename)
        for location in locations
    ]


def read_configuration(*filenames):
    pass