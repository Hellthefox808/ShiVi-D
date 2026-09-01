"""
ShiVi Safe Database Reset Script with Mandatory Accidental Data Loss Prevention
"""
import asyncio
import os
import sys

# Add core-api to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "apps", "core-api"))

from app.core.safety import ADLPSafetyGuard, ProductionDataLossError
from app.core.database import engine, Base
from scripts.seed_data import seed


async def safe_reset(force: bool = False):
    print("=" * 80)
    print("[SAFETY AUDIT] ShiVi Accidental Data Loss Prevention Check")
    print("=" * 80)

    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shivi_local.db")
    print(f"Target Database URL: {db_url}")

    if ADLPSafetyGuard.is_production_database(db_url):
        print("\n[CRITICAL ALERT] Target database is flagged as PRODUCTION!")
        print("Destructive reset is strictly prohibited. Aborting.")
        sys.exit(1)

    if not force and os.getenv("ALLOW_DATA_RESET") != "1":
        print("\n[STOP AND VERIFY] Destructive reset will DROP and RECREATE all tables.")
        print("To proceed, you must provide explicit consent by running with ALLOW_DATA_RESET=1")
        print("Example: $env:ALLOW_DATA_RESET='1'; python scripts/reset_db_safe.py")
        sys.exit(1)

    print("\n[VERIFIED] Explicit local-development consent confirmed. Resetting local database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("[OK] Schema re-created safely. Re-seeding baseline data...")
    await seed()
    print("[SUCCESS] Local development database reset and re-seeded with zero data loss to production.")


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    asyncio.run(safe_reset(force=force_flag))
