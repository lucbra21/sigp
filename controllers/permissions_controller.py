"""Permissions assignment to roles."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from sigp import db
from sigp.models import Base

perm_bp = Blueprint("permissions", __name__, url_prefix="/permissions")

# Mapeo de módulos a nombres visibles (usados también en el menú)
MODULE_LABELS = {
    'programs': 'Programas',
    'campus': 'Campus',
    'users': 'Usuarios',
    'roles': 'Roles',
    'permissions': 'Permisos',
    'prescriptor': 'Prescriptores',
    'prescriptors': 'Prescriptores',
    'notifications': 'Notificaciones',
    'state_ledger': 'Estados de ledger',
    'state_prescriptor': 'Estados de prescriptor',
    'state_user': 'Estados de usuario',
    'prescriptor_type': 'Tipos de Prescriptor',
    'confidence_level': 'Niveles de confianza',
    'edition': 'Ediciones',
    'approve': 'Aprobaciones',
    'confidence': 'Confianza',
    'program': 'Programas',
    'role': 'Roles',
    'state_lead': 'Estados de Lead',
    'user': 'Usuarios',
    'payments': 'Pagos',
    'own': 'Propios',
    'own_leads': 'Leads Propios',
}


def _model(name):
    return getattr(Base.classes, name, None)


@perm_bp.get("/")
@login_required
def roles_select():
    Role = _model("roles")
    if not Role:
        return "Modelo roles no disponible", 500
    roles = db.session.query(Role).order_by(Role.name).all()
    return render_template("list/permission_roles.html", roles=roles)


@perm_bp.route("/role/<role_id>", methods=["GET", "POST"])
@login_required
def assign_permissions(role_id):
    Role = _model("roles")
    Permission = _model("permissions")
    RolePerm = _model("role_permissions") or _model("roles_permissions")
    # Descubrir tabla intermedia si no se encontró
    if not RolePerm:
        for name, cls in Base.classes.items():
            cols = set(c.name for c in cls.__table__.columns)
            if {"role_id", "permission_id"}.issubset(cols):
                RolePerm = cls
                break

    # Si sigue sin encontrarse, puede ser una tabla de asociación sin clase mapeada
    role_perm_table = None
    if not RolePerm:
        role_perm_table = Base.metadata.tables.get("role_permissions")
        if role_perm_table is None:
            role_perm_table = Base.metadata.tables.get("roles_permissions")

    if not (Role and Permission and (RolePerm is not None or role_perm_table is not None)):
        return "Modelos necesarios no disponibles", 500

    role = db.session.get(Role, role_id)
    if not role:
        return "Rol no encontrado", 404

    if request.method == "POST":
        import uuid
        selected_keys = request.form.getlist("perm_keys")
        # limpiar actuales
        if RolePerm:
            db.session.query(RolePerm).filter(RolePerm.role_id == role_id).delete()
        else:
            from sqlalchemy import delete
            db.session.execute(delete(role_perm_table).where(role_perm_table.c.role_id == role_id))

        def ensure_assoc(pid):
            if RolePerm:
                db.session.add(RolePerm(role_id=role_id, permission_id=pid))
            else:
                from sqlalchemy import insert
                db.session.execute(insert(role_perm_table).values(role_id=role_id, permission_id=pid))

        for key in selected_keys:
            if key.startswith("new|"):
                perm_name = key[4:]
                perm = db.session.query(Permission).filter_by(name=perm_name).first()
                if not perm:
                    perm = Permission(id=str(uuid.uuid4()), name=perm_name)
                    db.session.add(perm)
                    db.session.flush()
                ensure_assoc(perm.id)
            else:
                ensure_assoc(key)

        db.session.commit()
        flash("Permisos actualizados", "success")
        return redirect(url_for("permissions.roles_select"))

    permissions = db.session.query(Permission).order_by(Permission.name).all()
    if RolePerm:
        current_ids = {
            rp.permission_id
            for rp in db.session.query(RolePerm).filter(RolePerm.role_id == role_id)
        }
    else:
        rows = db.session.execute(
            role_perm_table.select().with_only_columns(role_perm_table.c.permission_id).where(role_perm_table.c.role_id == role_id)
        )
        current_ids = {row.permission_id for row in rows}

    # Agrupar por módulo usando el prefijo del nombre (users_nuevo -> users)
    grouped = {}
    for p in permissions:
        if "_" not in p.name:
            # ignore malformed permission names
            continue
        parts = p.name.split("_", 1)
        module = parts[0]
        grouped.setdefault(module, []).append(p)

    actions = ["admin", "create", "delete", "manage", "read", "update", "view"]
    table_data = {}

    # Recalcular agrupación considerando posible nomenclatura 'action_module'
    regrouped = {}
    for p in permissions:
        if "_" not in p.name:
            # skip unexpected names
            continue
        first, second = p.name.split("_", 1)
        first_l = first.lower()
        second_l = second.lower()
        if first_l in actions:
            module = second_l
            action = first_l
        else:
            module = first_l
            action = second_l
        regrouped.setdefault(module, {}).setdefault(action, p)

    for module, action_map in regrouped.items():
        mapping = {a: None for a in actions}
        mapping.update(action_map)
        # agregar faltantes con nombre futuro
        for act in actions:
            if mapping[act] is None:
                mapping[act] = f"new|{module}_{act}"
        display_label = MODULE_LABELS.get(module, module.replace('_', ' ').title())
        table_data[display_label] = mapping

    return render_template(
        "records/assign_permissions.html",
        role=role,
        actions=actions,
        table_data=table_data,
        current_ids=current_ids,
    )
