#!/usr/bin/env python
import pytest

import pg_bawler.core


def test_register_handlers():
    listener = pg_bawler.core.ListenerMixin()
    assert listener.register_handler(None) == 0
    assert listener.register_handler(True) == 1
    assert listener.unregister_handler(None)
    assert not listener.unregister_handler(None)


@pytest.mark.asyncio
async def test_simple_listen():

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

    connection_params = dict(
        dbname='bawler_test',
        user='bawler_test',
        host='postgres',
        password='postgres')

    nl = NotificationListener(connection_params=connection_params)
    ns = NotificationSender(connection_params=connection_params)

    payload = 'aaa'
    channel_name = 'pg_bawler_test'

    await nl.register_channel(channel='pg_bawler_test')
    await ns.send(channel=channel_name, payload=payload)
    notification = await nl.get_notification()
    assert notification.channel == channel_name
    assert notification.payload == payload
