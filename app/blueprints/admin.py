from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..auth_utils import admin_login_required
from ..models import Event, Invoice
from ..services import (
    admin_event_rows,
    approve_order,
    booking_id,
    cancel_order,
    create_payment,
    grand_total,
    latest_invoice_for_order,
    latest_order_for_event,
    payment_status,
    pending_approvals,
)


bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard")
@admin_login_required
def dashboard():
    events = Event.query.all()
    pending_count = sum(1 for e in events if (latest_order_for_event(e) and latest_order_for_event(e).OrderStatus == "pending"))
    upcoming_count = sum(1 for e in events if (latest_order_for_event(e) and latest_order_for_event(e).OrderStatus == "approved"))
    cancelled_count = sum(1 for e in events if (latest_order_for_event(e) and latest_order_for_event(e).OrderStatus == "cancelled"))
    return render_template(
        "admin/admin-dashboard.html",
        pending_count=pending_count,
        upcoming_count=upcoming_count,
        completed_count=0,
        refunds_count=cancelled_count,
    )


@bp.route("/approvals")
@admin_login_required
def approvals():
    return render_template(
        "admin/admin-approvals.html",
        approvals=pending_approvals(),
        booking_id=booking_id,
        grand_total=grand_total,
    )


@bp.route("/approvals/<int:approval_id>/approve", methods=["POST"])
@admin_login_required
def approve(approval_id):
    try:
        approve_order(approval_id, session["StaffID"])
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.approvals"))


@bp.route("/approvals/<int:approval_id>/cancel", methods=["POST"])
@admin_login_required
def cancel(approval_id):
    try:
        cancel_order(approval_id, session["StaffID"])
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin.approvals"))


@bp.route("/calendar")
@admin_login_required
def calendar():
    status = request.args.get("status", "all")
    return render_template(
        "admin/admin-calendar.html",
        events=admin_event_rows(status),
        status=status,
        latest_order_for_event=latest_order_for_event,
        latest_invoice_for_order=latest_invoice_for_order,
        payment_status=payment_status,
    )


@bp.route("/events/<int:event_id>", methods=["GET", "POST"])
@admin_login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    order = latest_order_for_event(event)
    invoice = latest_invoice_for_order(order) if order else None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "payment" and invoice:
            create_payment(invoice.InvoiceID, request.form.get("amount"))
        elif action == "cancel" and invoice:
            approval = invoice.approvals[-1] if invoice.approvals else None
            if approval:
                cancel_order(approval.ApprovalID, session["StaffID"])
        return redirect(url_for("admin.event_detail", event_id=event.EventID))

    return render_template(
        "admin/admin-event-detail.html",
        event=event,
        order=order,
        invoice=invoice,
        booking_id=booking_id,
        grand_total=grand_total,
        payment_status=payment_status,
    )


@bp.route("/refunds")
@admin_login_required
def refunds():
    events = [
        event
        for event in Event.query.all()
        if latest_order_for_event(event)
        and latest_order_for_event(event).OrderStatus == "cancelled"
        and latest_invoice_for_order(latest_order_for_event(event))
        and latest_invoice_for_order(latest_order_for_event(event)).payments
    ]
    return render_template(
        "admin/admin-refunds.html",
        events=events,
        booking_id=booking_id,
        latest_order_for_event=latest_order_for_event,
        latest_invoice_for_order=latest_invoice_for_order,
        grand_total=grand_total,
    )


@bp.route("/refunds/<int:invoice_id>/mark-refunded", methods=["POST"])
@admin_login_required
def mark_refunded(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.Status = "refunded"
    from ..extensions import db

    db.session.commit()
    return redirect(url_for("admin.refunds"))
