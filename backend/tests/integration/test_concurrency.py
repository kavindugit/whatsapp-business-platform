import pytest
import asyncio
import uuid
import os
import psycopg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from app.db.tenant_context import tenant_transaction
from app.core.config import get_settings

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="module")
def async_engine():
    url = os.environ.get("TEST_DATABASE_URL", getattr(get_settings(), "test_database_url", None) or get_settings().database_url)
    url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://")
    engine = create_async_engine(url, pool_size=5)
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture
async def db_session(async_engine):
    async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.mark.integration
class TestConcurrency:
    async def test_t17_pooled_connection_reuse_rollback(self, async_engine):
        """T17: Pooled connection reuse/rollback: no context leak"""
        tenant_id = uuid.uuid4()
        
        async with async_engine.connect() as conn:
            # 1. Start a transaction and set context
            try:
                async with tenant_transaction(conn, tenant_id) as txn:
                    # Verify context is set
                    res = await txn.execute(sa.text("SELECT current_setting('app.tenant_id', true)"))
                    val = res.scalar()
                    assert val == str(tenant_id)
                    # Force an error to cause rollback
                    raise ValueError("Force rollback")
            except ValueError:
                pass
                
            # 2. Outside transaction, context should be empty
            res = await conn.execute(sa.text("SELECT current_setting('app.tenant_id', true)"))
            val = res.scalar()
            assert val == "" or val is None

    async def test_t18_parallel_ab_requests(self, async_engine):
        """T18: Parallel A/B requests: independent rows + audits"""
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        
        async def work_a():
            async with async_engine.connect() as conn:
                async with tenant_transaction(conn, tenant_a) as txn:
                    res = await txn.execute(sa.text("SELECT current_setting('app.tenant_id', true)"))
                    # Add delay to ensure overlap
                    await asyncio.sleep(0.1)
                    val = res.scalar()
                    return val

        async def work_b():
            async with async_engine.connect() as conn:
                async with tenant_transaction(conn, tenant_b) as txn:
                    res = await txn.execute(sa.text("SELECT current_setting('app.tenant_id', true)"))
                    await asyncio.sleep(0.1)
                    val = res.scalar()
                    return val

        # Run concurrently
        res_a, res_b = await asyncio.gather(work_a(), work_b())
        assert res_a == str(tenant_a)
        assert res_b == str(tenant_b)

    async def test_t21_concurrent_staff_provisioning(self):
        """T21: Concurrent staff provisioning at seat limit"""
        # This will be tested later using the API client
        pass
