from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..auth_utils import customer_login_required, require_event_owner
from ..extensions import db
from ..models import Customer, MenuItem
from ..services import (
    booking_id,
    confirm_order,
    delete_cancelled_event,
    ensure_customer_owns_event,
    get_customer_events,
    get_or_create_order,
    grand_total,
    latest_approval_for_invoice,
    latest_invoice_for_order,
    latest_order_for_event,
    order_subtotal,
    payment_status,
    replace_order_items,
    resubmit_cancelled_order,
    create_event as create_event_service,
    order_service
)


bp = Blueprint("customer", __name__)


@bp.route("/dashboard")
@customer_login_required
def dashboard():
    customer = Customer.query.get_or_404(session["CustomerID"])
    events = get_customer_events(customer.CustomerID)
    return render_template(
        "dashboard.html",
        customer=customer,
        events=events,
        booking_id=booking_id,
        latest_order_for_event=latest_order_for_event,
    )


@bp.route("/events/new", methods=["GET", "POST"])
@customer_login_required
def create_event():
    if request.method == "POST":
        event = create_event_service(session["CustomerID"], request.form)
        return redirect(url_for("customer.menu", event_id=event.EventID))
    return render_template("create-event.html", mode="create")


@bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@customer_login_required
def edit_event(event_id):
    event = ensure_customer_owns_event(event_id, session["CustomerID"])
    order = latest_order_for_event(event)
    if not order or order.OrderStatus != "cancelled":
        flash("Only cancelled orders can be edited.", "error")
        return redirect(url_for("customer.dashboard"))

    if request.method == "POST":
        event.EventName = request.form.get("event-name") or event.EventName
        event.EventType = request.form.get("event-type") or event.EventType
        from datetime import datetime

        event_date = request.form.get("event-date") or None
        event_time = request.form.get("event-time") or None
        event.EventDate = datetime.strptime(event_date, "%Y-%m-%d").date() if event_date else None
        event.EventTime = datetime.strptime(event_time, "%H:%M").time() if event_time else None
        event.VenueName = request.form.get("venue-name") or None
        event.Address = request.form.get("venue") or None
        event.GuestCount = int(request.form.get("guest-count") or 0)
        db.session.commit()
        return redirect(url_for("customer.menu", event_id=event.EventID))

    return render_template("create-event.html", mode="edit", event=event)


@bp.route("/events/<int:event_id>/menu", methods=["GET", "POST"])
@customer_login_required
def menu(event_id):
    event = ensure_customer_owns_event(event_id, session["CustomerID"])
    order = get_or_create_order(event)
    if order.OrderStatus not in ("draft", "cancelled"):
        flash("Only draft or cancelled orders can be changed.", "error")
        return redirect(url_for("customer.dashboard"))

    if request.method == "POST":
        selected = []
        for key, value in request.form.items():
            if key.startswith("quantity_") and value:
                selected.append((int(key.replace("quantity_", "")), int(value)))
        replace_order_items(order, selected)
        return redirect(url_for("customer.checkout", event_id=event.EventID))

    menu_items = MenuItem.query.order_by(MenuItem.MenuItemID.asc()).all()
    existing = {line.MenuItemID: line.Quantity for line in order.order_items}
    return render_template(
        "menu.html",
        event=event,
        order=order,
        menu_items=menu_items,
        existing=existing,
    )


@bp.route("/events/<int:event_id>/checkout", methods=["GET", "POST"])
@customer_login_required
def checkout(event_id):
    event = ensure_customer_owns_event(event_id, session["CustomerID"])
    order = latest_order_for_event(event)
    if not order:
        return redirect(url_for("customer.menu", event_id=event.EventID))

    if request.method == "POST":
        try:
            if order.OrderStatus == "cancelled":
                invoice, approval = resubmit_cancelled_order(order)
            else:
                invoice, approval = confirm_order(order)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("customer.menu", event_id=event.EventID))
        return redirect(url_for("customer.confirmation", event_id=event.EventID))

    invoice = latest_invoice_for_order(order)
    return render_template(
        "checkout.html",
        event=event,
        order=order,
        invoice=invoice,
        grand_total=grand_total,
        order_subtotal=order_subtotal,
        order_service=order_service,
    )


@bp.route("/events/<int:event_id>/confirmation")
@customer_login_required
def confirmation(event_id):
    event = ensure_customer_owns_event(event_id, session["CustomerID"])
    order = latest_order_for_event(event)
    invoice = latest_invoice_for_order(order) if order else None
    approval = latest_approval_for_invoice(invoice) if invoice else None
    return render_template(
        "confirmation.html",
        event=event,
        order=order,
        invoice=invoice,
        approval=approval,
        booking_id=booking_id,
    )


@bp.route("/events/<int:event_id>/delete", methods=["POST"])
@customer_login_required
def delete_event(event_id):
    event = ensure_customer_owns_event(event_id, session["CustomerID"])
    try:
        delete_cancelled_event(event)
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("customer.dashboard"))
