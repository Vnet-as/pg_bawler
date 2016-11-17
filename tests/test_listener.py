#!/usr/bin/env python
import time
import argparse

import pytest
import psycopg2

import pg_bawler.core
import pg_bawler.listener


class NotificationListener(
    pg_bawler.core.BawlerBase,
    pg_bawler.core.ListenerMixin
):
    pass


class NotificationSender(
    pg_bawler.core.BawlerBase,
    pg_bawler.core.SenderMixin
):
    pass


@pytest.fixture
def connection_params(pg_server):
    return pg_server['pg_params']


@pytest.fixture
def connection_dsn(connection_params):
    return ' '.join([
        '{}={}'.format(*kv)
        for kv in connection_params.items() if kv[1]
    ])


def test_register_handlers():
    listener = pg_bawler.core.ListenerMixin()
    assert listener.register_handler('channel', 'handler') is None
    assert listener.registered_channels['channel'] == ['handler']

    listener.unregister_handler('channel', 'handler')
    assert listener.registered_channels['channel'] == []
    listener.unregister_handler('channel', 'handler')

    listener.register_handler('channel', 'handler')
    assert listener.registered_channels['channel'] == ['handler']


def test_default_cli_parser():
    parser = pg_bawler.listener.get_default_cli_args_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_resolve_handler():
    handler = pg_bawler.listener.resolve_handler(
        'pg_bawler.listener:default_handler')
    assert handler is pg_bawler.listener.default_handler


@pytest.mark.asyncio
async def test_simple_listen(connection_params):
    nl = NotificationListener(connection_params=connection_params)
    ns = NotificationSender(connection_params=connection_params)

    payload = 'aaa'
    channel_name = 'pg_bawler_test'

    async with NotificationListener(connection_params) as nl:
        async with NotificationSender(connection_params) as ns:

            await nl.register_channel(channel='pg_bawler_test')
            await ns.send(channel=channel_name, payload=payload)
            notification = await nl.get_notification()
            assert notification.channel == channel_name
            assert notification.payload == payload


@pytest.mark.asyncio
async def test_get_notification_timeout(connection_params):
    nl = NotificationListener(connection_params=connection_params)
    nl.listen_timeout = 0
    await nl.register_channel(channel='pg_bawler_test')
    notification = await nl.get_notification()
    assert notification is None
    await nl.drop_connection()


@pytest.mark.asyncio
async def test_stop_on_timeout(connection_params):
    nl = NotificationListener(connection_params=connection_params)
    nl.listen_timeout = 0
    nl.stop_on_timeout = True
    await nl.register_channel(channel='pg_bawler_test')
    notification = await nl.get_notification()
    assert notification is None
    assert nl.is_stopped


@pytest.mark.asyncio
async def test_stop_listener(connection_params):
    async with NotificationListener(connection_params) as nl:
        await nl.stop()
        await nl.listen()


def test_listener_main(connection_params, event_loop):
    ns = NotificationSender(
        connection_params=connection_params,
        loop=event_loop,
    )
    payload = 'pg_bawler_test'

    async def handler(notification, listener):
        await pg_bawler.listener.default_handler(notification, listener)
        await ns.drop_connection()
        await listener.stop()

    channel = 'pg_bawler_test'
    listener, listen_task = pg_bawler.listener._main(
        connection_params=connection_params,
        channel=channel,
        handler=handler,
        timeout=0,
        stop_on_timeout=False,
        loop=event_loop,
    )

    event_loop.run_until_complete(ns.send(channel=channel, payload=payload))
    listen_task.add_done_callback(lambda fut: event_loop.stop())
    event_loop.run_forever()
    assert not listen_task.exception()
    event_loop.run_until_complete(listener.drop_connection())


@pytest.mark.asyncio
async def test_reconnect_after_restart(
    docker,
    pg_server,
    connection_params,
    event_loop
):
    payload = 'aaa'
    channel_name = 'pg_bawler_test'
    async with NotificationListener(connection_params) as nl:
            nl.listen_timeout = 1
            await nl.register_channel(channel='pg_bawler_test')

            async with NotificationSender(connection_params) as ns:
                await ns.send(channel=channel_name, payload=payload)

            notification = await nl.get_notification()
            assert notification.channel == channel_name
            assert notification.payload == payload
            docker.restart(pg_server['Id'])

            docker.restart(pg_server['Id'])

            delay = 0.001
            for i in range(100):
                try:
                    conn = psycopg2.connect(**connection_params)
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

            notification = await nl.get_notification()
            assert notification is None

            async with NotificationSender(connection_params) as ns:
                await ns.send(channel=channel_name, payload=payload)
            notification = await nl.get_notification()
            assert notification.channel == channel_name
            assert notification.payload == payload


def test_main_wrong_debug_level(connection_dsn, event_loop):
    with pytest.raises(SystemExit):
        pg_bawler.listener.main(
            '--stop-on-timeout',
            '--log-level', 'non-existent',
            '--timeout', '0',
            '--dsn', connection_dsn,
            'channel',
            loop=event_loop)


def test_listener_entrypoint(connection_dsn, event_loop):
    pg_bawler.listener.main(
        '--stop-on-timeout',
        '--timeout', '0',
        '--dsn', connection_dsn,
        'channel',
        loop=event_loop)
