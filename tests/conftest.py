import os
import time
import uuid

import psycopg2
import pytest
from docker import Client as DockerClient


def pytest_addoption(parser):
    parser.addoption(
        '--pg-tag',
        action='store',
        default=os.environ.get('PGTAG', '9.6'))


@pytest.fixture(scope='session')
def pg_tag(request):
    return request.config.getoption('--pg-tag')


@pytest.fixture(scope='session')
def session_id():
    return str(uuid.uuid4())


@pytest.fixture(scope='session')
def docker():
    return DockerClient(version='auto')


@pytest.yield_fixture(scope='session')
def pg_server(docker, pg_tag, session_id):
    docker.pull('postgres:{}'.format(pg_tag))
    container = docker.create_container(
        image='postgres:{}'.format(pg_tag),
        name='bawler-test-server-{}-{}'.format(pg_tag, session_id),
        detach=True,
    )
    docker.start(container=container['Id'])
    inspection = docker.inspect_container(container['Id'])
    host = inspection['NetworkSettings']['IPAddress']
    pg_params = dict(
        dbname='postgres',
        user='postgres',
        password='',
        host=host)

    delay = 0.001
    for i in range(100):
        try:
            conn = psycopg2.connect(**pg_params)
            cur = conn.cursor()
            cur.execute('SELECT 1;')
            cur.close()
            conn.close()
            break
        except psycopg2.Error as exc:
            time.sleep(delay)
            delay *= 2
    else:
        pytest.fail('Cannot start postgres server')

    container['host'] = host
    container['pg_params'] = pg_params

    yield container

    docker.kill(container=container['Id'])
    docker.remove_container(container['Id'])


@pytest.fixture(scope='session')
def pg_server_stop(docker, pg_server):
    def _stop():
        conn = psycopg2.connect(**pg_server['pg_params'])
        docker.stop(pg_server['Id'])
        delay = 0.001
        for i in range(100):
            try:
                cur = conn.cursor()
                cur.execute('SELECT 1;')
                cur.close()
            except psycopg2.Error as exc:
                conn.close()
                break
            else:
                time.sleep(delay)
                delay *= 2
        else:
            pytest.fail('Cannot stop the server')
    return _stop


@pytest.fixture(scope='session')
def pg_server_start(docker, pg_server):
    def _start():
        docker.start(pg_server['Id'])
        delay = 0.001
        for i in range(100):
            try:
                conn = psycopg2.connect(**pg_server['pg_params'])
                cur = conn.cursor()
                cur.execute('SELECT 1;')
                cur.close()
                conn.close()
                break
            except psycopg2.Error as exc:
                time.sleep(delay)
                delay *= 2
        else:
            pytest.fail('Cannot start postgres server')
    return _start


@pytest.fixture(scope='session')
def pg_server_restart(docker, pg_server):
    def _restart():
        docker.restart(pg_server['Id'])
        delay = 0.001
        for i in range(100):
            try:
                conn = psycopg2.connect(**pg_server['pg_params'])
                cur = conn.cursor()
                cur.execute('SELECT 1;')
                cur.close()
                conn.close()
                break
            except psycopg2.Error as exc:
                time.sleep(delay)
                delay *= 2
        else:
            pytest.fail('Cannot start postgres server')
    return _restart
