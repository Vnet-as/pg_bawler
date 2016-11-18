'''
================
pg_bawler.sender
================

'''
import pg_bawler.core


class SenderMixin:

    NOTIFY_SEND_TPL = 'SELECT pg_notify(\'{channel}\', \'{payload}\')'

    def get_notify_statement(self, *, channel, payload):
        return self.NOTIFY_SEND_TPL.format(channel=channel, payload=payload)

    async def send(self, *, channel, payload):
        async with (await self.pg_connection()).cursor() as pg_cursor:
            await pg_cursor.execute(
                self.get_notify_statement(channel=channel, payload=payload))


class NotificationSender(pg_bawler.core.BawlerBase, SenderMixin):
    pass
