"""
Migration script: Rebuild database tables for SaaS multi-tenancy.
Drops all existing tables and recreates them with the new schema
(user_id on products, plan/email on users).
Run this ONCE after deploying the SaaS update.
"""
from database import engine, SessionLocal
import models

def migrate():
    print("⚠️  Dropping all existing tables...")
    models.Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped.")

    print("🔨 Creating tables with new SaaS schema...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tables created with multi-tenant schema.")

    print("\n🌱 Run 'python seed.py' to populate sample data.")

if __name__ == "__main__":
    confirm = input("This will DELETE all existing data. Type 'YES' to continue: ")
    if confirm == "YES":
        migrate()
    else:
        print("Aborted.")
