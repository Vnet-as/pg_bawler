import pytest

import pg_bawler.core


@pytest.mark.asyncio
async def test_drop_connection_has_cache_attr():
    base = pg_bawler.core.BawlerBase(None)
    await base.drop_connection()
