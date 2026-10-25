from sqlalchemy import delete, select

from app.main import SessionLocal, User, Vehicle
from app.seed_demo import DEMO_VEHICLES, seed_demo


def test_demo_seed_is_repeatable_without_resetting_existing_inventory(monkeypatch):
    monkeypatch.setenv("DEMO_CUSTOMER_EMAIL", "seed.customer@example.com")
    monkeypatch.setenv("DEMO_CUSTOMER_PASSWORD", "Seed-Customer-Demo-2026!")
    monkeypatch.setenv("DEMO_ADMIN_EMAIL", "seed.admin@example.com")
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "Seed-Admin-Demo-2026!")

    try:
        seed_demo()
        with SessionLocal() as db:
            demo_vehicle = db.scalar(select(Vehicle).where(Vehicle.model == DEMO_VEHICLES[0]["model"]))
            demo_vehicle.quantity = 1
            db.commit()

        seed_demo()
        with SessionLocal() as db:
            users = db.scalars(select(User).where(User.email.in_([
                "seed.customer@example.com", "seed.admin@example.com"
            ]))).all()
            vehicles = db.scalars(select(Vehicle).where(Vehicle.model.in_([
                item["model"] for item in DEMO_VEHICLES
            ]))).all()
            assert {user.role for user in users} == {"customer", "admin"}
            assert len(users) == 2
            assert len(vehicles) == len(DEMO_VEHICLES)
            assert next(item for item in vehicles if item.model == DEMO_VEHICLES[0]["model"]).quantity == 1
    finally:
        with SessionLocal() as db:
            db.execute(delete(Vehicle).where(Vehicle.model.in_([item["model"] for item in DEMO_VEHICLES])))
            db.execute(delete(User).where(User.email.in_([
                "seed.customer@example.com", "seed.admin@example.com"
            ])))
            db.commit()
