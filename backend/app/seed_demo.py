"""Create the public demo identities and sample vehicles once, without overwrites.

Run as a backend-only deployment step: ``python -m app.seed_demo``.
"""
import os

from sqlalchemy import select, text

from app.main import DATABASE_URL, Base, SessionLocal, User, Vehicle, engine, password_hash

DEMO_VEHICLES = (
    {"make": "Toyota", "model": "Camry Demo", "category": "Sedan", "price": "28995.00", "quantity": 5},
    {"make": "Honda", "model": "Civic Demo", "category": "Compact", "price": "24950.00", "quantity": 4},
    {"make": "Ford", "model": "Bronco Demo", "category": "SUV", "price": "41900.00", "quantity": 3},
)


def required_demo_settings():
    fields = {
        "DEMO_CUSTOMER_EMAIL": os.getenv("DEMO_CUSTOMER_EMAIL", "").strip().lower(),
        "DEMO_CUSTOMER_PASSWORD": os.getenv("DEMO_CUSTOMER_PASSWORD", ""),
        "DEMO_ADMIN_EMAIL": os.getenv("DEMO_ADMIN_EMAIL", "").strip().lower(),
        "DEMO_ADMIN_PASSWORD": os.getenv("DEMO_ADMIN_PASSWORD", ""),
    }
    missing = [name for name, value in fields.items() if not value]
    if missing:
        raise RuntimeError("Set backend-only demo settings: " + ", ".join(missing))
    if fields["DEMO_CUSTOMER_EMAIL"] == fields["DEMO_ADMIN_EMAIL"]:
        raise RuntimeError("Demo customer and admin must use distinct email addresses")
    if fields["DEMO_CUSTOMER_PASSWORD"] == fields["DEMO_ADMIN_PASSWORD"]:
        raise RuntimeError("Demo customer and admin passwords must be distinct")
    if any(len(fields[name]) < 16 for name in ("DEMO_CUSTOMER_PASSWORD", "DEMO_ADMIN_PASSWORD")):
        raise RuntimeError("Each demo password must contain at least 16 characters")
    return fields


def seed_demo():
    settings = required_demo_settings()
    # create_all adds missing tables but leaves existing tables and rows intact.
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # Serialize deploys/startups so two instances cannot insert duplicates.
        if DATABASE_URL.startswith("postgresql"):
            db.execute(text("SELECT pg_advisory_xact_lock(731904271)"))
        for email_key, password_key, role in (
            ("DEMO_CUSTOMER_EMAIL", "DEMO_CUSTOMER_PASSWORD", "customer"),
            ("DEMO_ADMIN_EMAIL", "DEMO_ADMIN_PASSWORD", "admin"),
        ):
            email = settings[email_key]
            existing = db.scalar(select(User).where(User.email == email))
            if existing is None:
                db.add(User(email=email, password_hash=password_hash.hash(settings[password_key]), role=role))
            elif existing.role != role:
                raise RuntimeError(f"Existing demo identity {email} has a different role; refusing to modify it")
            elif not password_hash.verify(settings[password_key], existing.password_hash):
                raise RuntimeError(f"Existing demo identity {email} has a different password; refusing to reset it")
            # Existing passwords/roles are never reset or elevated by reseeding.

        for vehicle_data in DEMO_VEHICLES:
            existing = db.scalar(select(Vehicle).where(
                Vehicle.make == vehicle_data["make"],
                Vehicle.model == vehicle_data["model"],
                Vehicle.category == vehicle_data["category"],
            ))
            if existing is None:
                db.add(Vehicle(**vehicle_data))
        db.commit()


if __name__ == "__main__":
    seed_demo()
    print("Demo accounts and sample inventory are ready.")
