#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import zmq.asyncio
import logging


LOGGER = logging.getLogger('zmq_listener')


class ZmqPgBawlerHandler:

    def __init__(self):
        self.zmq_ctx = zmq.asyncio.Context()
        self.zmq_pub = self.zmq_ctx.socket(zmq.PUB)
        self.zmq_pub.bind(b"tcp://127.0.0.1:7887")

    async def handle_notification(self, notification):
        LOGGER.info("Sending notification: %s", notification.payload)
        await self.zmq_pub.send_json(
            (notification.pid, notification.channel, notification.payload))


handler = ZmqPgBawlerHandler().handle_notification
