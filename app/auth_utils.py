from functools import wraps

from flask import abort, redirect, session, url_for


def login_customer(customer):
    session.clear()
    session["CustomerID"] = customer.CustomerID


def login_staff(staff):
    session.clear()
    session["StaffID"] = staff.StaffID
    session["Role"] = staff.Role


def logout():
    session.clear()


def customer_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("CustomerID"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("StaffID"):
            return redirect(url_for("admin_auth.login"))
        return view(*args, **kwargs)

    return wrapped


def require_event_owner(event):
    if not event or event.CustomerID != session.get("CustomerID"):
        abort(404)
