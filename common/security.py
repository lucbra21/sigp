"""Permission helpers relocated from sigp.security"""
from functools import wraps
from typing import Set
from flask import abort
from flask_login import current_user
from sigp import db
from sigp.models import Base

Permission = getattr(Base.classes, "permissions", None)
Role = getattr(Base.classes, "roles", None)
RolePerm = getattr(Base.classes, "role_permissions", None)
if RolePerm is None:
    RolePerm = getattr(Base.classes, "roles_permissions", None)
if RolePerm is None:
    RolePerm = Base.metadata.tables.get("role_permissions")
if RolePerm is None:
    RolePerm = Base.metadata.tables.get("roles_permissions")

_perm_cache_attr = "_cached_perm_names"

def _permission_names_for_user(user) -> Set[str]:
    if not (user and user.is_authenticated and Permission is not None and RolePerm is not None and Role is not None):
        return set()
    role_ids = []
    if hasattr(user, "roles") and getattr(user, "roles") is not None:
        val = getattr(user, "roles")
        try:
            role_ids = [r.id for r in val]
        except TypeError:
            role_ids = [val.id] if hasattr(val, "id") else []
    if not role_ids and hasattr(user, "role") and getattr(user, "role") is not None:
        role_ids = [user.role.id]
    if not role_ids and hasattr(user, "role_id") and user.role_id:
        role_ids = [user.role_id]
    if not role_ids:
        assoc = None
        for cls in Base.classes.values():
            cols = {c.name for c in cls.__table__.columns}
            if {"user_id", "role_id"}.issubset(cols):
                assoc = cls; break
        if assoc:
            role_ids = [row.role_id for row in db.session.query(assoc.role_id).filter_by(user_id=user.id)]
    if not role_ids:
        return set()
    perm_ids = set()
    if hasattr(RolePerm, 'permission_id'):
        perm_ids = {rp.permission_id for rp in db.session.query(RolePerm.permission_id).filter(RolePerm.role_id.in_(role_ids))}
    elif hasattr(RolePerm, 'c') and 'permission_id' in RolePerm.c:
        rows = db.session.execute(RolePerm.select().with_only_columns(RolePerm.c.permission_id).where(RolePerm.c.role_id.in_(role_ids))).all()
        perm_ids = {row[0] for row in rows}
    if not perm_ids:
        return set()
    names = {p.name.lower() for p in db.session.query(Permission.name).filter(Permission.id.in_(perm_ids))}
    return names

def _perm_set(user):
    if not user or not user.is_authenticated:
        return set()
    if not hasattr(user, _perm_cache_attr):
        setattr(user, _perm_cache_attr, _permission_names_for_user(user))
    return getattr(user, _perm_cache_attr)

def has_perm(user, perm_name: str) -> bool:
    return perm_name in _perm_set(user)

def has_any_prefix(user, module: str) -> bool:
    """True si el usuario tiene algún permiso que empiece o termine con el módulo indicado."""
    perms = _perm_set(user)
    mod = module.lower()
    mod_sing = mod[:-1] if mod.endswith('s') else mod
    return any((pl := p.lower()) and (
        pl.startswith(f"{mod}_") or pl.startswith(f"{mod_sing}_") or
        pl.endswith(f"_{mod}") or pl.endswith(f"_{mod_sing}")
    ) for p in perms)

def require_perm(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_perm(current_user, name):
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator
