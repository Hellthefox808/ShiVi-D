"""
ShiVi Seed Data Script
Initializes foundational tenant, users, sample incident, and tasks for testing and simulations.
"""
import os
import sys
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "core-api")))

from app.core.database import engine, AsyncSessionLocal, Base
from app.core.security import get_password_hash
from app.modules.identity.models import Tenant, User
from app.modules.incidents.models import Incident, RouteObservation
from app.modules.tasks.models import Task
from app.modules.incidents.priority import calculate_incident_priority
from sqlalchemy.future import select


async def seed():
    print("[SEED] Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if users already exist
        res = await session.execute(select(User).limit(1))
        if res.scalars().first():
            print("[SEED] Database already populated with authenticated accounts. Ready.")
            return

        tenant_id = "11111111-1111-1111-1111-111111111111"
        tenant = Tenant(
            id=tenant_id,
            name="Assam State Disaster Management Authority (ASDMA)",
            slug="asdma-district-01",
            sector_pack="disaster_response",
        )
        session.add(tenant)

        # 2. Seed Users
        supervisor = User(
            id="00000000-0000-0000-0000-000000000001",
            tenant_id=tenant_id,
            username="commander_sharma",
            email="commander@asdma.gov.in",
            hashed_password=get_password_hash("CommandSecure2026!"),
            full_name="Rajesh Sharma (Incident Commander)",
            role="SUPERVISOR",
            phone="+919876543210",
        )

        responder = User(
            id="00000000-0000-0000-0000-000000000002",
            tenant_id=tenant_id,
            username="responder_singh",
            email="singh.sdrf@asdma.gov.in",
            hashed_password=get_password_hash("FieldOps2026!"),
            full_name="Vikram Singh (SDRF Team Lead)",
            role="RESPONDER",
            phone="+919876543211",
        )

        citizen = User(
            id="00000000-0000-0000-0000-000000000003",
            tenant_id=tenant_id,
            username="citizen_das",
            email="citizen@gmail.com",
            hashed_password=get_password_hash("CitizenAccess2026!"),
            full_name="Ananya Das (Community Reporter)",
            role="CITIZEN",
            phone="+919876543212",
        )

        session.add_all([supervisor, responder, citizen])
        await session.commit()
        print("[SEED] Seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
