"""
Safe Local Database Snapshot & Clean Baseline Reset
"""
import os
import sys
import shutil
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "core-api")))

from app.core.database import engine, AsyncSessionLocal, Base
from app.core.security import get_password_hash

# Import all SQLAlchemy models to register them in Base.metadata
import app.modules.identity.models
import app.modules.incidents.models
import app.modules.tasks.models
import app.modules.conflicts.models
import app.modules.evidence.models
import app.modules.audit.models

from app.modules.identity.models import Tenant, User
import asyncio


async def run_clean_reset():
    db_file = "shivi_local.db"
    backup_file = "shivi_local_backup.db"
    timestamp_backup = f"shivi_local_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # Create backup snapshot if file exists
    if os.path.exists(db_file):
        shutil.copy2(db_file, backup_file)
        shutil.copy2(db_file, timestamp_backup)
        print(f"[BACKUP] Created snapshot backup: {backup_file} & {timestamp_backup}")
    
    # 2. Reset database schema
    print("[RESET] Recreating clean database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # 3. Re-seed only clean foundational accounts
    async with AsyncSessionLocal() as session:
        # Tenant
        tenant = Tenant(
            id="00000000-0000-0000-0000-000000000001",
            name="SDRF Assam Operations",
            slug="sdrf-assam",
            sector_pack="disaster_response",
        )
        session.add(tenant)
        await session.flush()
        
        # Base Users
        commander = User(
            id="00000000-0000-0000-0000-000000000001",
            tenant_id=tenant.id,
            username="commander",
            email="commander@sdrf.gov.in",
            phone="+919876543210",
            full_name="Col. Rajesh Sharma",
            role="SUPERVISOR",
            hashed_password=get_password_hash("CommandSecure2026!"),
            is_active=True,
        )
        responder = User(
            id="00000000-0000-0000-0000-000000000002",
            tenant_id=tenant.id,
            username="responder1",
            email="responder1@sdrf.gov.in",
            phone="+919876543211",
            full_name="Havildar Amit Borah",
            role="RESPONDER",
            hashed_password=get_password_hash("FieldOps2026!"),
            is_active=True,
        )
        citizen = User(
            id="00000000-0000-0000-0000-000000000003",
            tenant_id=tenant.id,
            username="citizen1",
            email="citizen1@assam.gov.in",
            phone="+919876543212",
            full_name="Priyanka Das",
            role="CITIZEN",
            hashed_password=get_password_hash("CitizenAccess2026!"),
            is_active=True,
        )
        session.add_all([commander, responder, citizen])
        await session.commit()
    
    print("[CLEAN] Database reset to clean baseline successfully.")


if __name__ == "__main__":
    os.environ["ALLOW_DATA_RESET"] = "1"
    asyncio.run(run_clean_reset())
