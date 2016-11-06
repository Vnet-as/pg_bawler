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


# TODO: Maybe as a pytest fixtures?
connection_params = dict(
    dbname=os.environ.get('POSTGRES_DB', 'bawler_test'),
    user=os.environ.get('POSTGRES_USER', 'postgres'),
    host=os.environ.get('POSTGRES_HOST'),
    password=os.environ.get('POSTGRES_PASSWORD', ''))


def test_register_handlers():
    listener = pg_bawler.core.ListenerMixin()
    assert listener.register_handler(None) == 0
    assert listener.register_handler(True) == 1
    assert listener.unregister_handler(None)
    assert not listener.unregister_handler(None)


def test_default_cli_parser():
    parser = pg_bawler.listener.get_default_cli_args_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_resolve_handler():
    handler = pg_bawler.listener.resolve_handler(
        'pg_bawler.listener:default_handler')
    assert handler is pg_bawler.listener.default_handler


@pytest.mark.asyncio
async def test_simple_listen():
    connection_params = dict(
        dbname=os.environ.get('POSTGRES_DB', 'bawler_test'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        host=os.environ.get('POSTGRES_HOST'),
        password=os.environ.get('POSTGRES_PASSWORD', ''))

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
async def test_get_notification_timeout():
    nl = NotificationListener(connection_params=connection_params)
    nl.listen_timeout = 0
    await nl.register_channel(channel='pg_bawler_test')
    notification = await nl.get_notification()
    assert notification is None
