from datetime import date
from datetime import datetime
from decimal import Decimal

from flask import abort
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import (
    Approval,
    Customer,
    Event,
    Invoice,
    MenuItem,
    Order,
    OrderMenuItem,
    Payment,
    Staff,
)


SERVICE_RATE = Decimal("0.10")


def register_customer(name, email, password, phone=None):
    existing = Customer.query.filter(func.lower(Customer.Email) == email.lower()).first()
    if existing:
        raise ValueError("A customer with that email already exists.")

    customer = Customer(
        Name=name,
        Phone=phone,
        Email=email,
        PasswordHash=generate_password_hash(password),
    )
    db.session.add(customer)
    db.session.commit()
    return customer


def authenticate_customer(email, password):
    customer = Customer.query.filter(func.lower(Customer.Email) == email.lower()).first()
    if customer and check_password_hash(customer.PasswordHash, password):
        return customer
    return None


def authenticate_staff(email, password):
    staff = Staff.query.filter(func.lower(Staff.Email) == email.lower()).first()
    if staff and check_password_hash(staff.PasswordHash, password):
        return staff
    return None


def default_staff():
    staff = Staff.query.order_by(Staff.StaffID.asc()).first()
    if not staff:
        raise ValueError("At least one STAFF record is required before orders can be created.")
    return staff


def booking_id(event):
    year = event.EventDate.year if event.EventDate else date.today().year
    return f"EVT-{year}-{event.EventID:04d}"


def grand_total(invoice):
    return (invoice.Subtotal or Decimal("0.00")) + (invoice.ServiceCharge or Decimal("0.00"))


def payment_total(invoice):
    return sum((payment.Amount or Decimal("0.00")) for payment in invoice.payments)


def payment_status(invoice):
    paid = payment_total(invoice)
    total = grand_total(invoice)
    if paid <= 0:
        return "unpaid"
    if paid >= total:
        return "fully_paid"
    return "deposit_paid"


def latest_order_for_event(event):
    return Order.query.filter_by(EventID=event.EventID).order_by(Order.OrderID.desc()).first()


def latest_invoice_for_order(order):
    return Invoice.query.filter_by(OrderID=order.OrderID).order_by(Invoice.InvoiceID.desc()).first()


def latest_approval_for_invoice(invoice):
    return (
        Approval.query.filter_by(InvoiceID=invoice.InvoiceID)
        .order_by(Approval.ApprovalID.desc())
        .first()
    )


def create_event(customer_id, form):
    event_date = form.get("event-date") or None
    event_time = form.get("event-time") or None
    event = Event(
        EventName=form.get("event-name") or "Untitled Event",
        EventType=form.get("event-type") or "Catering",
        EventDate=datetime.strptime(event_date, "%Y-%m-%d").date() if event_date else None,
        EventTime=datetime.strptime(event_time, "%H:%M").time() if event_time else None,
        VenueName=form.get("venue-name") or None,
        Address=form.get("venue") or None,
        GuestCount=int(form.get("guest-count") or 0),
        CustomerID=customer_id,
    )
    db.session.add(event)
    db.session.commit()
    return event


def get_customer_events(customer_id):
    return Event.query.filter_by(CustomerID=customer_id).order_by(Event.EventDate.desc()).all()


def get_or_create_order(event):
    order = latest_order_for_event(event)
    if order:
        return order

    staff = default_staff()
    order = Order(
        OrderStatus="draft",
        IsSelected=False,
        EventID=event.EventID,
        StaffID=staff.StaffID,
    )
    db.session.add(order)
    db.session.commit()
    return order


def replace_order_items(order, selected_items):
    if order.OrderStatus not in ("draft", "cancelled"):
        raise ValueError("Only draft or cancelled orders can be changed.")

    OrderMenuItem.query.filter_by(OrderID=order.OrderID).delete()

    for item_id, quantity in selected_items:
        item = MenuItem.query.get(item_id)
        if not item:
            continue
        quantity = int(quantity)
        if quantity <= 0:
            continue
        db.session.add(
            OrderMenuItem(
                OrderID=order.OrderID,
                MenuItemID=item.MenuItemID,
                Quantity=quantity,
                PriceAtOrderTime=item.Price,
            )
        )

    db.session.commit()
    return order


def order_subtotal(order):
    subtotal = Decimal("0.00")
    for line in order.order_items:
        subtotal += (line.PriceAtOrderTime or Decimal("0.00")) * line.Quantity

    return subtotal

def order_service(subtotal):
    service = subtotal * Decimal('0.10')
    total = subtotal + service
    return total


def confirm_order(order):
    if not order.order_items:
        raise ValueError("Cannot submit an empty order.")
    if order.OrderStatus not in ("draft", "cancelled", "pending"):
        raise ValueError("Only draft, pending, or cancelled orders can be submitted.")

    staff = default_staff()
    subtotal = order_subtotal(order)
    service_charge = (subtotal * SERVICE_RATE).quantize(Decimal("0.01"))
    previous_invoice = latest_invoice_for_order(order)

    invoice = Invoice(
        InvoiceNumber=f"INV-{date.today().year}-{order.OrderID:04d}-{(previous_invoice.InvoiceID if previous_invoice else 0) + 1:04d}",
        InvoiceDate=date.today(),
        Subtotal=subtotal,
        ServiceCharge=service_charge,
        Status="unpaid",
        OrderID=order.OrderID,
        PreviousInvoiceID=previous_invoice.InvoiceID if previous_invoice else None,
        StaffID=staff.StaffID,
    )
    db.session.add(invoice)
    db.session.flush()

    approval = Approval(
        Status="pending",
        ApprovalDate=None,
        InvoiceID=invoice.InvoiceID,
        CustomerID=order.event.CustomerID,
        StaffID=None,
    )
    db.session.add(approval)

    order.OrderStatus = "pending"
    order.IsSelected = True
    db.session.commit()
    return invoice, approval


def approve_order(approval_id, staff_id):
    approval = Approval.query.get_or_404(approval_id)
    order = approval.invoice.order
    if order.OrderStatus != "pending" or approval.Status != "pending":
        raise ValueError("Only pending approvals can be approved.")

    approval.Status = "approved"
    approval.ApprovalDate = date.today()
    approval.StaffID = staff_id
    order.OrderStatus = "approved"
    db.session.commit()
    return approval


def cancel_order(approval_id, staff_id):
    approval = Approval.query.get_or_404(approval_id)
    order = approval.invoice.order
    if order.OrderStatus not in ("pending", "approved"):
        raise ValueError("Only pending or approved orders can be cancelled.")

    approval.Status = "cancelled"
    approval.ApprovalDate = date.today()
    approval.StaffID = staff_id
    order.OrderStatus = "cancelled"
    db.session.commit()
    return approval


def resubmit_cancelled_order(order):
    if order.OrderStatus != "cancelled":
        raise ValueError("Only cancelled orders can be resubmitted.")
    return confirm_order(order)


def delete_cancelled_event(event):
    order = latest_order_for_event(event)
    if not order or order.OrderStatus != "cancelled":
        raise ValueError("Only cancelled orders can be deleted.")

    invoices = Invoice.query.filter_by(OrderID=order.OrderID).all()
    invoice_ids = [invoice.InvoiceID for invoice in invoices]

    if invoice_ids:
        Approval.query.filter(Approval.InvoiceID.in_(invoice_ids)).delete(synchronize_session=False)
        Payment.query.filter(Payment.InvoiceID.in_(invoice_ids)).delete(synchronize_session=False)
        for invoice in invoices:
            invoice.PreviousInvoiceID = None
        db.session.flush()
        Invoice.query.filter(Invoice.InvoiceID.in_(invoice_ids)).delete(synchronize_session=False)

    OrderMenuItem.query.filter_by(OrderID=order.OrderID).delete()
    db.session.delete(order)
    db.session.delete(event)
    db.session.commit()


def create_payment(invoice_id, amount):
    invoice = Invoice.query.get_or_404(invoice_id)
    payment = Payment(PaymentDate=date.today(), Amount=Decimal(str(amount)), InvoiceID=invoice.InvoiceID)
    db.session.add(payment)
    db.session.flush()
    invoice.Status = payment_status(invoice)
    db.session.commit()
    return payment


def pending_approvals():
    return Approval.query.filter_by(Status="pending").order_by(Approval.ApprovalID.asc()).all()


def admin_event_rows(status=None):
    query = Event.query.join(Order)
    if status and status != "all":
        query = query.filter(Order.OrderStatus == status)
    return query.order_by(Event.EventDate.desc()).all()


def ensure_customer_owns_event(event_id, customer_id):
    event = Event.query.get_or_404(event_id)
    if event.CustomerID != customer_id:
        abort(404)
    return event
