from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..auth_utils import login_staff, logout
from ..services import authenticate_staff


bp = Blueprint("admin_auth", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        staff = authenticate_staff(
            request.form.get("email", "").strip(),
            request.form.get("password", ""),
        )
        if not staff:
            flash("Invalid staff email or password.", "error")
            return render_template("admin/admin-login.html")

        login_staff(staff)
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/admin-login.html")


@bp.route("/logout")
def logout_admin():
    logout()
    return redirect(url_for("admin_auth.login"))
