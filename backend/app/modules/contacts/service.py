import json
import uuid

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.clock import system_clock
from app.core.errors import ConflictError, NotFoundError
from app.db.models.contacts import Contact
from app.db.models.users import User
from app.db.tenant_context import tenant_transaction
from app.modules.contacts.schemas import ContactCreate, ContactUpdate


async def create_contact(
    db: AsyncSession, actor_user: User, tenant_id: uuid.UUID, payload: ContactCreate
) -> Contact:
    now = system_clock.utcnow()
    new_id = uuid.uuid4()
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        # We can proactively check for phone conflicts to provide a nice error
        if payload.phone_e164:
            res = await txn.execute(
                select(Contact.id).where(
                    Contact.tenant_id == tenant_id,
                    Contact.phone_e164 == payload.phone_e164,
                    Contact.status == "active",
                )
            )
            if res.scalar_one_or_none():
                raise ConflictError("A contact with this phone number already exists.")

        try:
            await txn.execute(
                Contact.__table__.insert().values(  # type: ignore[attr-defined]
                    id=new_id,
                    tenant_id=tenant_id,
                    display_name=payload.display_name,
                    phone_e164=payload.phone_e164,
                    email=payload.email,
                    preferred_lang=payload.preferred_lang,
                    notes=payload.notes,
                    status="active",
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
            )
        except IntegrityError:
            raise ConflictError("A contact with this phone number already exists.")

        from app.db.models.audit import TenantAuditEvent

        await txn.execute(
            TenantAuditEvent.__table__.insert().values(  # type: ignore[attr-defined]
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor_user.id,
                action="create_contact",
                target_type="contact",
                target_id=new_id,
                created_at=now,
            )
        )

    # Return the newly created contact
    async with tenant_transaction(await db.connection(), tenant_id) as txn:
        res = await txn.execute(select(Contact).where(Contact.id == new_id))
        return res.scalar_one()


async def get_contacts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    limit: int = 25,
    offset: int = 0,
    search: str | None = None,
    status_filter: str | None = None,
) -> list[Contact]:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        stmt = select(Contact).where(Contact.tenant_id == tenant_id)
        if status_filter:
            stmt = stmt.where(Contact.status == status_filter)

        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Contact.display_name.ilike(search_term),
                    Contact.phone_e164.ilike(search_term),
                    Contact.email.ilike(search_term),
                )
            )

        stmt = stmt.order_by(Contact.created_at.desc(), Contact.id).limit(limit).offset(offset)
        result = await txn.execute(stmt)
        return list(result.scalars().all())


async def count_contacts(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    search: str | None = None,
    status_filter: str | None = None,
) -> int:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        stmt = select(func.count(Contact.id)).where(Contact.tenant_id == tenant_id)
        if status_filter:
            stmt = stmt.where(Contact.status == status_filter)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Contact.display_name.ilike(search_term),
                    Contact.phone_e164.ilike(search_term),
                    Contact.email.ilike(search_term),
                )
            )
        result = await txn.execute(stmt)
        return result.scalar_one() or 0


async def get_contact(db: AsyncSession, tenant_id: uuid.UUID, contact_id: uuid.UUID) -> Contact:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        result = await txn.execute(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.id == contact_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            raise NotFoundError("Contact not found.")
        return row


async def update_contact(
    db: AsyncSession,
    actor_user: User,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    payload: ContactUpdate,
) -> Contact:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        res = await txn.execute(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.id == contact_id)
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found.")

        if contact.version != payload.expected_version:
            raise ConflictError("This record changed. Refresh and try again.")

        # Check phone conflict if phone is being changed to something new
        if payload.phone_e164 is not None and payload.phone_e164 != contact.phone_e164:
            conflict_res = await txn.execute(
                select(Contact.id).where(
                    Contact.tenant_id == tenant_id,
                    Contact.phone_e164 == payload.phone_e164,
                    Contact.status == "active",
                    Contact.id != contact_id,
                )
            )
            if conflict_res.scalar_one_or_none():
                raise ConflictError("A contact with this phone number already exists.")

        now = system_clock.utcnow()
        update_values = {"version": contact.version + 1, "updated_at": now}

        # Only update fields that were provided
        if payload.display_name is not None:
            update_values["display_name"] = payload.display_name
        if payload.phone_e164 is not None:
            update_values["phone_e164"] = payload.phone_e164
        if payload.email is not None:
            update_values["email"] = payload.email
        if payload.preferred_lang is not None:
            update_values["preferred_lang"] = payload.preferred_lang
        if payload.notes is not None:
            update_values["notes"] = payload.notes

        try:
            await txn.execute(
                Contact.__table__.update()  # type: ignore[attr-defined]
                .where(Contact.id == contact_id, Contact.tenant_id == tenant_id)
                .values(**update_values)
            )
        except IntegrityError:
            raise ConflictError("A contact with this phone number already exists.")

        from app.db.models.audit import TenantAuditEvent

        await txn.execute(
            TenantAuditEvent.__table__.insert().values(  # type: ignore[attr-defined]
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor_user.id,
                action="update_contact",
                target_type="contact",
                target_id=contact_id,
                metadata=json.dumps({"version": contact.version + 1}),
                created_at=now,
            )
        )

    async with tenant_transaction(await db.connection(), tenant_id) as txn:
        res = await txn.execute(select(Contact).where(Contact.id == contact_id))
        return res.scalar_one()


async def archive_contact(
    db: AsyncSession,
    actor_user: User,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    expected_version: int,
) -> Contact:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        res = await txn.execute(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.id == contact_id)
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found.")

        if contact.version != expected_version:
            raise ConflictError("This record changed. Refresh and try again.")

        now = system_clock.utcnow()

        if contact.status == "archived":
            # Safe repeat state
            return contact

        await txn.execute(
            Contact.__table__.update()  # type: ignore[attr-defined]
            .where(Contact.id == contact_id, Contact.tenant_id == tenant_id)
            .values(status="archived", version=contact.version + 1, updated_at=now)
        )

        from app.db.models.audit import TenantAuditEvent

        await txn.execute(
            TenantAuditEvent.__table__.insert().values(  # type: ignore[attr-defined]
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor_user.id,
                action="archive_contact",
                target_type="contact",
                target_id=contact_id,
                metadata=json.dumps({"version": contact.version + 1}),
                created_at=now,
            )
        )

    async with tenant_transaction(await db.connection(), tenant_id) as txn:
        res = await txn.execute(select(Contact).where(Contact.id == contact_id))
        return res.scalar_one()


async def restore_contact(
    db: AsyncSession,
    actor_user: User,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
    expected_version: int,
) -> Contact:
    conn = await db.connection()
    async with tenant_transaction(conn, tenant_id) as txn:
        res = await txn.execute(
            select(Contact).where(Contact.tenant_id == tenant_id, Contact.id == contact_id)
        )
        contact = res.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found.")

        if contact.version != expected_version:
            raise ConflictError("This record changed. Refresh and try again.")

        if contact.status == "active":
            return contact

        # Check if restoring would cause a phone conflict
        if contact.phone_e164:
            conflict_res = await txn.execute(
                select(Contact.id).where(
                    Contact.tenant_id == tenant_id,
                    Contact.phone_e164 == contact.phone_e164,
                    Contact.status == "active",
                    Contact.id != contact_id,
                )
            )
            if conflict_res.scalar_one_or_none():
                raise ConflictError(
                    "Cannot restore: an active contact with this phone number already exists."
                )

        now = system_clock.utcnow()
        await txn.execute(
            Contact.__table__.update()  # type: ignore[attr-defined]
            .where(Contact.id == contact_id, Contact.tenant_id == tenant_id)
            .values(status="active", version=contact.version + 1, updated_at=now)
        )

        from app.db.models.audit import TenantAuditEvent

        await txn.execute(
            TenantAuditEvent.__table__.insert().values(  # type: ignore[attr-defined]
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                actor_user_id=actor_user.id,
                action="restore_contact",
                target_type="contact",
                target_id=contact_id,
                metadata=json.dumps({"version": contact.version + 1}),
                created_at=now,
            )
        )

    async with tenant_transaction(await db.connection(), tenant_id) as txn:
        res = await txn.execute(select(Contact).where(Contact.id == contact_id))
        return res.scalar_one()
