import os
from decimal import Decimal
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import Staff, MenuItem, Customer, Event

def seed():
    app = create_app()
    with app.app_context():
        print("Seeding database...")
        
        # 1. Create a default admin/staff account if it doesn't exist
        admin = Staff.query.filter_by(Email="admin@menuplus.com").first()
        if not admin:
            admin = Staff(
                Name="System Admin",
                Role="admin",
                Email="admin@menuplus.com",
                PasswordHash=generate_password_hash("admin123")
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default admin: admin@menuplus.com / admin123")
        else:
            print("Admin account already exists.")

        # 2. Create sample menu items if they don't exist
        default_items = [
            ("Jollof Rice", Decimal("1500.00")),
            ("Fried Rice", Decimal("1500.00")),
            ("Pounded Yam", Decimal("2000.00")),
            ("Plantain", Decimal("500.00")),
            ("Coleslaw", Decimal("500.00")),
            ("Chapman", Decimal("800.00")),
            ("Soft Drinks", Decimal("400.00")),
            ("Chocolate Fountain", Decimal("3500.00")),
            ("Mini Pastries", Decimal("1200.00"))
        ]
        
        for name, price in default_items:
            existing = MenuItem.query.filter_by(ItemName=name).first()
            if not existing:
                item = MenuItem(
                    ItemName=name,
                    Price=price,
                    StaffID=admin.StaffID
                )
                db.session.add(item)
                print(f"Added menu item: {name} (NGN {price})")
        db.session.commit()

        # 3. Create a sample customer and event for demonstration
        customer = Customer.query.filter_by(Email="customer@example.com").first()
        if not customer:
            customer = Customer(
                Name="Amaka Okonkwo",
                Phone="08012345678",
                Email="customer@example.com",
                PasswordHash=generate_password_hash("password123")
            )
            db.session.add(customer)
            db.session.commit()
            print("Created sample customer: customer@example.com / password123")
        else:
            print("Sample customer already exists.")

        print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed()
