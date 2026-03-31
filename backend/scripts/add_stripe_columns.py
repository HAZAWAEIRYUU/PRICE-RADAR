import os
import sys

# Allow importing from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text

def apply_migrations():
    print("Applying DB Migrations for Stripe...")
    
    with engine.connect() as conn:
        try:
            # Add stripe_customer_id
            conn.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR;"))
            conn.commit()
            print("Successfully added stripe_customer_id column.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower() or "42701" in str(e):
                print("stripe_customer_id column already exists.")
            else:
                print(f"Error adding stripe_customer_id: {e}")
                
        try:
            # Add stripe_subscription_id
            conn.execute(text("ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR;"))
            conn.commit()
            print("Successfully added stripe_subscription_id column.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower() or "42701" in str(e):
                print("stripe_subscription_id column already exists.")
            else:
                print(f"Error adding stripe_subscription_id: {e}")
                
        # Optional: create indexes if needed
        try:
            conn.execute(text("CREATE INDEX ix_users_stripe_customer_id ON users (stripe_customer_id);"))
            conn.commit()
            print("Successfully added index for stripe_customer_id.")
        except Exception as e:
            if "already exists" in str(e).lower() or "42P07" in str(e):
                pass
                
        try:
            conn.execute(text("CREATE INDEX ix_users_stripe_subscription_id ON users (stripe_subscription_id);"))
            conn.commit()
            print("Successfully added index for stripe_subscription_id.")
        except Exception as e:
            if "already exists" in str(e).lower() or "42P07" in str(e):
                pass

    print("Migration complete.")

if __name__ == "__main__":
    apply_migrations()
