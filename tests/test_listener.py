#!/usr/bin/env python
import pytest

import pg_bawler.core


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
        dbname='pg_bawler_test',
        user='pg_bawler_test',
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
