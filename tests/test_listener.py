#!/usr/bin/env python
import argparse
import os

import pytest

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
def connection_params():
    return dict(
        dbname=os.environ.get('POSTGRES_DB', 'bawler_test'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        host=os.environ.get('POSTGRES_HOST'),
        password=os.environ.get('POSTGRES_PASSWORD', ''))


def test_register_handlers():
    listener = pg_bawler.core.ListenerMixin()
    assert listener.register_handler('channel', 'handler') is None
    assert listener.registered_channels['channel'] == ['handler']

    listener.unregister_handler('channel', 'handler')
    assert listener.registered_channels['channel'] == []
    listener.unregister_handler('channel', 'handler')


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
    nl = NotificationListener(connection_params=connection_params)
    await nl.stop()
    await nl.listen()


def test_listener_main(connection_params, event_loop):
    # ns = NotificationSender(connection_params=connection_params)
    payload = 'pg_bawler_test'

    async def handler(notification, listener):
        assert notification.payload == payload
        listener.stop()

    pg_bawler.listener._main(
        connection_params=connection_params,
        channel='pg_bawler_test',
        handler=handler,
        timeout=0,
        stop_on_timeout=True,
        loop=event_loop,
    )


# @pytest.mark.asyncio
# async def test_listener_main(event_loop):
#     ns = NotificationSender(connection_params=connection_params)
#     nl = NotificationListener(connection_params=connection_params)
#     payload = 'pg_bawler_test'
#
#     async def handler(notification, listener):
#         assert notification.payload == payload
#         await listener.stop()
#
#     nl.timeout = 5
#     nl.register_handler('channel', handler)
#     await nl.register_channel('channel')
#     event_loop.create_task(ns.send(channel='channel', payload=payload))
#     await nl.listen()
