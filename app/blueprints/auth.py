from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..auth_utils import login_customer, logout
from ..services import authenticate_customer, register_customer


bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            customer = register_customer(
                request.form.get("name", "").strip(),
                request.form.get("email", "").strip(),
                request.form.get("password", ""),
                request.form.get("phone", "").strip() or None,
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("register.html")

        login_customer(customer)
        return redirect(url_for("customer.dashboard"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        customer = authenticate_customer(
            request.form.get("email", "").strip(),
            request.form.get("password", ""),
        )
        if not customer:
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        login_customer(customer)
        return redirect(url_for("customer.dashboard"))

    return render_template("login.html")


@bp.route("/logout")
def logout_customer():
    logout()
    return redirect(url_for("auth.login"))
