import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import NotFoundError
from app.db.models.plans import Package, PackageVersion, Subscription
from app.modules.plans.schemas import PackageDTO, SubscriptionDetailDTO, SubscriptionDTO


async def get_packages(db: AsyncSession) -> list[Package]:
    from sqlalchemy.orm import selectinload

    # Returns all packages
    stmt = select(Package).options(selectinload(Package.versions)).order_by(Package.created_at)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tenant_subscription(db: AsyncSession, tenant_id: uuid.UUID) -> SubscriptionDetailDTO:
    stmt = (
        select(Subscription, PackageVersion, Package)
        .join(PackageVersion, PackageVersion.id == Subscription.package_version_id)
        .join(Package, Package.code == PackageVersion.package_code)
        .where(Subscription.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise NotFoundError("Subscription not found.")

    subscription, pv, package = row

    return SubscriptionDetailDTO(
        subscription=SubscriptionDTO.model_validate(subscription),
        package=PackageDTO.model_validate(package),
        version=pv.version,
        monthly_price=pv.monthly_price,
        setup_price=pv.setup_price,
        staff_limit=pv.staff_limit,
        number_limit=pv.number_limit,
        feature_permissions=pv.feature_permissions,
        metric_limits=pv.metric_limits,
        usage="N/A",
    )
