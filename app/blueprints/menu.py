from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..auth_utils import admin_login_required
from ..extensions import db
from ..models import MenuItem


bp = Blueprint("menu", __name__, url_prefix="/admin/menu")


@bp.route("/", methods=["GET", "POST"])
@admin_login_required
def manage():
    if request.method == "POST":
        item = MenuItem(
            ItemName=request.form.get("name", "").strip(),
            Price=request.form.get("price") or 0,
            StaffID=session["StaffID"],
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("menu.manage"))

    return render_template("admin/admin-menu.html", items=MenuItem.query.order_by(MenuItem.MenuItemID.asc()).all())


@bp.route("/<int:item_id>/edit", methods=["POST"])
@admin_login_required
def edit(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.ItemName = request.form.get("name", item.ItemName).strip()
    item.Price = request.form.get("price") or item.Price
    item.StaffID = session["StaffID"]
    db.session.commit()
    return redirect(url_for("menu.manage"))


@bp.route("/<int:item_id>/delete", methods=["POST"])
@admin_login_required
def delete(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if item.order_links:
        flash("Menu items already used in orders cannot be deleted.", "error")
        return redirect(url_for("menu.manage"))
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("menu.manage"))
