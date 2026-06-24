from .extensions import db


class Customer(db.Model):
    __tablename__ = "CUSTOMER"

    CustomerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(20))
    Email = db.Column(db.String(150), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)

    events = db.relationship("Event", back_populates="customer")
    approvals = db.relationship("Approval", back_populates="customer")


class Staff(db.Model):
    __tablename__ = "STAFF"

    StaffID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Role = db.Column(db.String(50), nullable=False)
    Email = db.Column(db.String(150), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)

    menu_items = db.relationship("MenuItem", back_populates="staff")
    orders = db.relationship("Order", back_populates="staff")
    invoices = db.relationship("Invoice", back_populates="staff")
    approvals = db.relationship("Approval", back_populates="staff")


class Event(db.Model):
    __tablename__ = "EVENT"
    __table_args__ = (
        db.CheckConstraint("GuestCount >= 0", name="ck_event_guest_count_nonnegative"),
    )

    EventID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EventName = db.Column(db.String(100), nullable=False)
    EventType = db.Column(db.String(50))
    EventDate = db.Column(db.Date)
    EventTime = db.Column(db.Time)
    VenueName = db.Column(db.String(100))
    Address = db.Column(db.String(255))
    GuestCount = db.Column(db.Integer)
    CustomerID = db.Column(
        db.Integer,
        db.ForeignKey("CUSTOMER.CustomerID", ondelete="RESTRICT"),
        nullable=False,
    )

    customer = db.relationship("Customer", back_populates="events")
    orders = db.relationship("Order", back_populates="event")


class MenuItem(db.Model):
    __tablename__ = "MENU_ITEM"
    __table_args__ = (
        db.CheckConstraint("Price >= 0", name="ck_menu_item_price_nonnegative"),
    )

    MenuItemID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ItemName = db.Column(db.String(100), nullable=False)
    Price = db.Column(db.Numeric(10, 2))
    StaffID = db.Column(
        db.Integer,
        db.ForeignKey("STAFF.StaffID", ondelete="RESTRICT"),
        nullable=False,
    )

    staff = db.relationship("Staff", back_populates="menu_items")
    order_links = db.relationship("OrderMenuItem", back_populates="menu_item")
    orders = db.relationship(
        "Order",
        secondary="ORDER_MENU_ITEM",
        viewonly=True,
        back_populates="menu_items",
    )


class Order(db.Model):
    __tablename__ = "ORDERS"

    OrderID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OrderStatus = db.Column(db.String(50))
    IsSelected = db.Column(db.Boolean)
    EventID = db.Column(
        db.Integer,
        db.ForeignKey("EVENT.EventID", ondelete="RESTRICT"),
        nullable=False,
    )
    StaffID = db.Column(
        db.Integer,
        db.ForeignKey("STAFF.StaffID", ondelete="RESTRICT"),
        nullable=False,
    )

    event = db.relationship("Event", back_populates="orders")
    staff = db.relationship("Staff", back_populates="orders")
    order_items = db.relationship(
        "OrderMenuItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    menu_items = db.relationship(
        "MenuItem",
        secondary="ORDER_MENU_ITEM",
        viewonly=True,
        back_populates="orders",
    )
    invoices = db.relationship("Invoice", back_populates="order")


class OrderMenuItem(db.Model):
    __tablename__ = "ORDER_MENU_ITEM"
    __table_args__ = (
        db.CheckConstraint("Quantity > 0", name="ck_order_menu_item_quantity_positive"),
        db.CheckConstraint(
            "PriceAtOrderTime >= 0",
            name="ck_order_menu_item_price_nonnegative",
        ),
    )

    OrderID = db.Column(
        db.Integer,
        db.ForeignKey("ORDERS.OrderID", ondelete="CASCADE"),
        primary_key=True,
    )
    MenuItemID = db.Column(
        db.Integer,
        db.ForeignKey("MENU_ITEM.MenuItemID", ondelete="RESTRICT"),
        primary_key=True,
    )
    Quantity = db.Column(db.Integer)
    PriceAtOrderTime = db.Column(db.Numeric(10, 2))

    order = db.relationship("Order", back_populates="order_items")
    menu_item = db.relationship("MenuItem", back_populates="order_links")


class Invoice(db.Model):
    __tablename__ = "INVOICE"
    __table_args__ = (
        db.CheckConstraint("Subtotal >= 0", name="ck_invoice_subtotal_nonnegative"),
        db.CheckConstraint(
            "ServiceCharge >= 0",
            name="ck_invoice_service_charge_nonnegative",
        ),
    )

    InvoiceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    InvoiceNumber = db.Column(db.String(50), unique=True, nullable=False)
    InvoiceDate = db.Column(db.Date)
    Subtotal = db.Column(db.Numeric(10, 2))
    ServiceCharge = db.Column(db.Numeric(10, 2))
    Status = db.Column(db.String(50))
    OrderID = db.Column(
        db.Integer,
        db.ForeignKey("ORDERS.OrderID", ondelete="RESTRICT"),
        nullable=False,
    )
    PreviousInvoiceID = db.Column(
        db.Integer,
        db.ForeignKey("INVOICE.InvoiceID", ondelete="SET NULL"),
    )
    StaffID = db.Column(
        db.Integer,
        db.ForeignKey("STAFF.StaffID", ondelete="RESTRICT"),
        nullable=False,
    )

    order = db.relationship("Order", back_populates="invoices")
    previous_invoice = db.relationship("Invoice", remote_side=[InvoiceID])
    staff = db.relationship("Staff", back_populates="invoices")
    payments = db.relationship("Payment", back_populates="invoice")
    approvals = db.relationship("Approval", back_populates="invoice")


class Payment(db.Model):
    __tablename__ = "PAYMENT"
    __table_args__ = (
        db.CheckConstraint("Amount > 0", name="ck_payment_amount_positive"),
    )

    PaymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PaymentDate = db.Column(db.Date)
    Amount = db.Column(db.Numeric(10, 2))
    InvoiceID = db.Column(
        db.Integer,
        db.ForeignKey("INVOICE.InvoiceID", ondelete="RESTRICT"),
        nullable=False,
    )

    invoice = db.relationship("Invoice", back_populates="payments")


class Approval(db.Model):
    __tablename__ = "APPROVAL"

    ApprovalID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Status = db.Column(db.String(50))
    ApprovalDate = db.Column(db.Date)
    InvoiceID = db.Column(
        db.Integer,
        db.ForeignKey("INVOICE.InvoiceID", ondelete="RESTRICT"),
        nullable=False,
    )
    CustomerID = db.Column(
        db.Integer,
        db.ForeignKey("CUSTOMER.CustomerID", ondelete="SET NULL"),
    )
    StaffID = db.Column(
        db.Integer,
        db.ForeignKey("STAFF.StaffID", ondelete="SET NULL"),
    )

    invoice = db.relationship("Invoice", back_populates="approvals")
    customer = db.relationship("Customer", back_populates="approvals")
    staff = db.relationship("Staff", back_populates="approvals")
