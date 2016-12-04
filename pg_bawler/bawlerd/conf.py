import os

import yaml

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
    '''
    Builds list of absolute paths to configuration files defined by list of
    ``locations`` and ``filename``. You may use `~` for root of user directory.
    '''
    return [
        os.path.abspath(os.path.join(os.path.expanduser(location), filename))
        for location in locations
    ]


def _load_file(_file):
    '''
    Parse file into a python object (mapping).

    TODO: Only yaml for now, maybe more formats later.
    '''
    return yaml.load(_file)


def _merge_configs(base, precede):
    '''
    Merges configurations.

    TODO: Merge different nested sections in different fashion.
    '''
    return {**base, **precede}


def read_config_files(config_locations):
    '''
    Reads config files at ``locations`` and merge values.
    '''
    config = {}
    for config_location in config_locations:
        with open(config_location) as config_file:
            config = _merge_configs(config, _load_file(config_file))
    return config
