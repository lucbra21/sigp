"""User notifications blueprint (step 1): view own notifications and mark as read."""
from __future__ import annotations

import datetime
import math

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, TextAreaField, URLField, SubmitField
from wtforms.validators import DataRequired, Length, URL
import uuid

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")

Notification = getattr(Base.classes, "notifications", None)
User = getattr(Base.classes, "users", None)
Role = getattr(Base.classes, "roles", None)


@notifications_bp.get("/my")
@login_required
def my_notifications():
    if Notification is None:
        flash("Tabla notifications no disponible", "danger")
        return redirect(url_for("main.index"))

    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    per_page = 15
    per_page = 20
    q = db.session.query(Notification).filter_by(user_id=current_user.id)
    if status == "unread":
        q = q.filter_by(is_read=0)
    elif status == "read":
        q = q.filter_by(is_read=1)
    q = q.order_by(Notification.created_at.desc())
    total = q.count()
    notifications = q.offset((page - 1) * per_page).limit(per_page).all()

    return render_template(
        "list/my_notifications.html",
        notifs=notifications,
        total=total,
        page=page,
        per_page=per_page,
        status=status,
    )


class NotificationForm(FlaskForm):
    recipient_type = SelectField("Destinatario", choices=[("ALL", "Todos"), ("ROLE", "Rol(es)"), ("USER", "Usuario(s)")], validators=[DataRequired()])
    roles = SelectMultipleField("Roles", coerce=str)
    users = SelectMultipleField("Usuarios", coerce=str)
    notif_type = SelectField("Tipo", choices=[("INFO", "Info"), ("ACTION", "Acción"), ("WARNING", "Advertencia"), ("ERROR", "Error")])
    title = StringField("Título", validators=[DataRequired(), Length(max=150)])
    body = TextAreaField("Cuerpo", validators=[Length(max=2000)])
    link_url = URLField("URL", validators=[URL(require_tld=False), Length(max=255)], default="")
    submit = SubmitField("Guardar")


@notifications_bp.route("/", methods=["GET"])
@login_required
@require_perm("read_notifications")
def list_all():
    if Notification is None:
        flash("Tabla notifications no disponible", "danger")
        return redirect(url_for("main.index"))
    status = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    per_page = 15
    q = db.session.query(Notification)
    if status == "unread":
        q = q.filter_by(is_read=0)
    elif status == "read":
        q = q.filter_by(is_read=1)
    total = q.count()
    notifs = (
        q.order_by(Notification.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)
    # build user name map
    user_map = {}
    if User is not None:
        ids = [n.user_id for n in notifs]
        if ids:
            q_users = db.session.query(User).filter(User.id.in_(ids))
            for u in q_users:
                name_attr = getattr(u, "name", None) or getattr(u, "email", None) or u.id
                user_map[u.id] = name_attr
    return render_template(
        "list/notifications_admin.html",
        notifs=notifs,
        status=status,
        page=page,
        pages=pages,
        user_map=user_map,
    )


@notifications_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_notifications")
def new_notification():
    if Notification is None or User is None:
        flash("Tablas requeridas no disponibles", "danger")
        return redirect(url_for("notifications.list_all"))

    form = NotificationForm()
    # populate choices
    if Role is not None:
        form.roles.choices = [(r.id, r.name) for r in db.session.query(Role).order_by(Role.name)]
    if User is not None:
        form.users.choices = [(u.id, u.email) for u in db.session.query(User).order_by(User.email)]

    if form.validate_on_submit():
        recipient_type = form.recipient_type.data
        user_ids = []
        if recipient_type == "ALL":
            user_ids = [u.id for u in db.session.query(User.id).all()]
        elif recipient_type == "ROLE" and Role is not None:
            sel_roles = form.roles.data
            if sel_roles:
                # gather users in those roles
                # assume User has roles relationship
                q = db.session.query(User)
                if hasattr(User, "roles"):
                    q = q.join(User.roles)
                    user_ids = [u.id for u in q.filter(Role.id.in_(sel_roles)).all()]
        elif recipient_type == "USER":
            user_ids = form.users.data

        if not user_ids:
            flash("No se encontraron usuarios destinatarios", "warning")
            return render_template("records/notification_form.html", form=form, action=url_for("notifications.new_notification"))

        to_insert = []
        for uid in set(user_ids):
            to_insert.append(Notification(
                id=str(uuid.uuid4()),
                user_id=uid,
                title=form.title.data,
                body=form.body.data,
                link_url=form.link_url.data or None,
                notif_type=form.notif_type.data,
                is_read=0,
                created_at=datetime.datetime.utcnow()
            ))
        db.session.bulk_save_objects(to_insert)
        db.session.commit()
        flash(f"Se crearon {len(to_insert)} notificaciones", "success")
        return redirect(url_for("notifications.list_all"))

    return render_template("records/notification_form.html", form=form, action=url_for("notifications.new_notification"))


@notifications_bp.route("/mark-read/<notif_id>")
@login_required
def mark_read(notif_id):
    if Notification is None:
        return redirect(url_for("notifications.my_notifications"))

    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == current_user.id and not notif.is_read:
        notif.is_read = 1
        notif.read_at = datetime.datetime.utcnow()
        db.session.commit()
    return redirect(request.referrer or url_for("notifications.my_notifications"))


@notifications_bp.route("/delete/<notif_id>", methods=["POST"])
@login_required
@require_perm("delete_notifications")
def delete_notification(notif_id):
    if Notification is None:
        return redirect(url_for("notifications.list_all"))
    notif = db.session.get(Notification, notif_id)
    if notif:
        db.session.delete(notif)
        db.session.commit()
        flash("Notificación eliminada", "success")
    return redirect(request.referrer or url_for("notifications.list_all"))


@notifications_bp.route("/mark-unread/<notif_id>")
@login_required
def mark_unread(notif_id):
    if Notification is None:
        return redirect(url_for("notifications.my_notifications"))
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == current_user.id and notif.is_read:
        notif.is_read = 0
        notif.read_at = None
        db.session.commit()
    return redirect(request.referrer or url_for("notifications.my_notifications"))
