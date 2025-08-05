"""Blueprint de Multimedia (scaffolding inicial)

Por ahora solo incluye:
• Gestión de categorías
• Carga de archivo
• Visualización de archivos

Cada vista verifica permisos mediante el decorador requires_roles ya
usado en el proyecto.

IMPORTANTE: Se usa automap de SQLAlchemy. Las tablas deben existir en la
BD para reflejarlas.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField, TextAreaField, SelectField, URLField
from wtforms.validators import DataRequired, Length

from sigp import db
from sigp.security import require_perm
from sigp.models import Base
# TODO: integrar verificación de roles cuando esté disponible

multimedia_bp = Blueprint("multimedia", __name__, url_prefix="/media")

# ────────────────────────────────────────────────────────────────────────────
# Formularios
# ────────────────────────────────────────────────────────────────────────────
class CategoryForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Descripción", validators=[Length(max=255)])
    submit = SubmitField("Guardar")


class UploadForm(FlaskForm):
    source_type = SelectField("Tipo", choices=[("FILE", "Archivo"), ("LINK", "Enlace")], validators=[DataRequired()])
    category = SelectField("Categoría", coerce=int, validators=[DataRequired()])
    # Usamos str para permitir UUID u otros tipos de clave primaria
    role_id = SelectField("Rol", coerce=str)
    visibility = SelectField(
        "Visibilidad",
        choices=[("PUBLIC", "Pública"), ("PRIVATE", "Privada"), ("ROLE", "Por rol"), ("CUSTOM", "Personalizada")],
        validators=[DataRequired()],
    )
    title = StringField("Título", validators=[DataRequired(), Length(max=255)])
    description = TextAreaField("Descripción", validators=[Length(max=1000)])
    url = URLField("URL (si es enlace)")
    file = FileField(
        "Archivo",
        validators=[FileAllowed(["jpg", "jpeg", "png", "gif", "mp4", "pdf"], "Tipos permitidos: imágenes, video mp4, pdf")]
    )
    submit = SubmitField("Subir")


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _get_models():
    """Devuelve modelos reflejados o None si no existen."""
    Category = getattr(Base.classes, "media_categories", None)
    Media = getattr(Base.classes, "media_files", None)
    return Category, Media


# ────────────────────────────────────────────────────────────────────────────
# Categorías
# ────────────────────────────────────────────────────────────────────────────
@multimedia_bp.get("/categories")
@login_required
@require_perm("read_media")
def list_categories():
    Category, _ = _get_models()
    if not Category:
        flash("Tabla media_categories no disponible", "danger")
        return redirect(url_for("main.index"))
    cats = db.session.query(Category).order_by(Category.name.asc()).all()
    return render_template("list/media_categories.html", cats=cats)


@multimedia_bp.route("/categories/new", methods=["GET", "POST"])
@login_required
@require_perm("create_media")
def create_category():
    Category, _ = _get_models()
    if not Category:
        flash("Tabla media_categories no disponible", "danger")
        return redirect(url_for("multimedia.list_categories"))
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data, description=form.description.data)
        db.session.add(cat)
        db.session.commit()
        flash("Categoría creada", "success")
        return redirect(url_for("multimedia.list_categories"))
    return render_template("records/media_category_form.html", form=form, action=url_for("multimedia.create_category"))


# ────────────────────────────────────────────────────────────────────────────
# Upload de archivos
# ────────────────────────────────────────────────────────────────────────────
@multimedia_bp.route("/upload", methods=["GET", "POST"])
@login_required
@require_perm("create_media")
def upload_media():
    Category, Media = _get_models()
    if not Media:
        flash("Tabla media_files no disponible", "danger")
        return redirect(url_for("multimedia.list_media"))
        # build choices
    if Category:
        form = UploadForm()
        form.category.choices = [(c.id, c.name) for c in db.session.query(Category).order_by(Category.name).all()]
        # poblar roles
        Role = getattr(Base.classes, "roles", None)
        if Role is not None:
            role_rows = db.session.query(Role).order_by(Role.name).all()
            form.role_id.choices = [("0", "Todos")] + [(str(r.id), getattr(r, "name", r.id)) for r in role_rows]
        else:
            form.role_id.choices = [("0", "Todos")]
    else:
        form = UploadForm()
        form.category.choices = []
        form.role_id.choices = [("0", "Todos")]

    if form.validate_on_submit():
        media_id = str(uuid.uuid4())
        if form.source_type.data == "FILE":
            f = form.file.data
            orig_name = secure_filename(f.filename)
            ext = Path(orig_name).suffix.lstrip(".")
            filename = f"{media_id}.{ext}"
            storage_path = Path(current_app.root_path) / "static/uploads" / filename
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            f.save(storage_path)
            storage_key = f"uploads/{filename}"
            mime = f.mimetype
            size_b = storage_path.stat().st_size
        else:
            storage_key = form.url.data
            mime = "url/external"
            size_b = None
            orig_name = form.url.data

        media = Media(
            id=media_id,
            uploader_id=current_user.id,
            storage_key=storage_key,
            original_name=orig_name,
            mime_type=mime,
            size_bytes=size_b,
            source_type=form.source_type.data,
            title=form.title.data,
            description=form.description.data,
            visibility=form.visibility.data,
            role_id=(None if form.role_id.data == "0" else form.role_id.data),
        )
        db.session.add(media)
        db.session.commit()
        # asociar categoría elegida
        Assoc = getattr(Base.classes, "media_file_category", None)
        if Assoc is not None and form.category.data:
            db.session.add(Assoc(media_id=media_id, category_id=form.category.data))
        # asociar rol elegido
        RoleAssoc = getattr(Base.classes, "media_file_role", None)
        if RoleAssoc is not None and form.role_id.data and form.role_id.data != "0":
            db.session.add(RoleAssoc(media_id=media_id, role_id=form.role_id.data))  # type: ignore[arg-type]
        db.session.commit()
        flash("Archivo subido", "success")
        return redirect(url_for("multimedia.list_media"))
    return render_template("records/media_upload.html", form=form, action=url_for("multimedia.upload_media"))


# ────────────────────────────────────────────────────────────────────────────
# Visualizar archivos
# ────────────────────────────────────────────────────────────────────────────
@multimedia_bp.get("/files")
@login_required
@require_perm("read_media")
def list_media():
    Category, Media = _get_models()
    Assoc = getattr(Base.classes, "media_file_category", None)
    if not Media:
        flash("Tabla media_files no disponible", "danger")
        return redirect(url_for("main.index"))

    cat_id = request.args.get("category_id", type=int)

    q = db.session.query(Media)
    if cat_id and Assoc is not None:
        q = q.join(Assoc, Assoc.media_id == Media.id).filter(Assoc.category_id == cat_id)
    # recuperamos archivos y nombre de categoría en una sola consulta
    files = []
    # obtener mapping de roles
    Role = getattr(Base.classes, "roles", None)
    role_lookup: dict[str, str] = {}
    if Role is not None:
        role_lookup = {str(r.id): getattr(r, "name", str(r.id)) for r in db.session.query(Role).all()}

    if Category:
        # crear lookup de categorías
        cat_lookup = {c.id: c.name for c in db.session.query(Category).all()}
        rows = q.order_by(Media.created_at.desc()).limit(100).all()
        for media_obj in rows:
            media_obj.category_name = cat_lookup.get(getattr(media_obj, "category_id", None), "-")
            role_val = getattr(media_obj, "role_id", None)
            media_obj.role_name = "Todos" if not role_val else role_lookup.get(str(role_val), "-")
            files.append(media_obj)
    else:
        files = q.order_by(Media.created_at.desc()).limit(100).all()
        for media_obj in files:
            media_obj.category_name = "-"
            role_val = getattr(media_obj, "role_id", None)
            media_obj.role_name = "Todos" if not role_val else role_lookup.get(str(role_val), "-")
    cats = db.session.query(Category).order_by(Category.name).all() if Category else []
    return render_template("list/media_files.html", files=files, cats=cats, selected_cat=cat_id)


# ────────────────────────────────────────────────────────────────────────────
# Vista de usuario final: Mis archivos
# ────────────────────────────────────────────────────────────────────────────
@multimedia_bp.get("/my")
@login_required
@require_perm("media_view")
def my_media():
    """Lista archivos visibles para el rol del usuario (solo lectura)."""
    Category, Media = _get_models()
    if not Media:
        flash("Tabla media_files no disponible", "danger")
        return redirect(url_for("main.index"))

    Role = getattr(Base.classes, "roles", None)
    # construir query base
    q = db.session.query(Media)

    # aplicar filtros de visibilidad
    from sqlalchemy import or_, and_
    conds = [Media.visibility == "PUBLIC"]
    # si el archivo está restringido a rol, coincide con rol del usuario
    if hasattr(current_user, "role_id") and current_user.role_id:
        conds.append(and_(Media.visibility == "ROLE", Media.role_id == str(current_user.role_id)))
    # archivos sin role_id (Todos)
    conds.append(Media.role_id == None)
    q = q.filter(or_(*conds))

    files = q.order_by(Media.created_at.desc()).limit(100).all()
    # preparar lookups
    role_lookup = {}
    if Role is not None:
        role_lookup = {str(r.id): getattr(r, "name", str(r.id)) for r in db.session.query(Role).all()}
    cat_lookup = {}
    if Category is not None:
        cat_lookup = {c.id: c.name for c in db.session.query(Category).all()}
    for media_obj in files:
        media_obj.category_name = cat_lookup.get(getattr(media_obj, "category_id", None), "-") if Category else "-"
        role_val = getattr(media_obj, "role_id", None)
        media_obj.role_name = "Todos" if not role_val else role_lookup.get(str(role_val), "-")
    return render_template("list/media_grid.html", files=files)

# Editar / eliminar archivos
# ────────────────────────────────────────────────────────────────────────────
@multimedia_bp.route("/files/<media_id>/delete", methods=["POST"])
@login_required
@require_perm("delete_media")
def delete_media(media_id):
    """Elimina un archivo multimedia y sus relaciones."""
    _, Media = _get_models()
    if not Media:
        abort(404)
    obj = db.session.get(Media, media_id)
    if not obj:
        abort(404)
    # eliminar relaciones intermedias si existen
    AssocCat = getattr(Base.classes, "media_file_category", None)
    AssocRole = getattr(Base.classes, "media_file_role", None)
    if AssocCat:
        db.session.query(AssocCat).filter_by(media_id=media_id).delete()
    if AssocRole:
        db.session.query(AssocRole).filter_by(media_id=media_id).delete()
    db.session.delete(obj)
    db.session.commit()
    flash("Archivo eliminado", "success")
    return redirect(url_for("multimedia.list_media"))


@multimedia_bp.route("/files/<media_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_media")
def edit_media(media_id):
    """Permite editar título, descripción, categoría, rol y visibilidad."""
    Category, Media = _get_models()
    if not Media:
        abort(404)
    obj = db.session.get(Media, media_id)
    if not obj:
        abort(404)

    form = UploadForm(obj=obj)
    # opciones de categorías
    if Category:
        form.category.choices = [(c.id, c.name) for c in db.session.query(Category).order_by(Category.name)]
    else:
        form.category.choices = []
    # roles
    Role = getattr(Base.classes, "roles", None)
    if Role is not None:
        role_rows = db.session.query(Role).order_by(Role.name).all()
        form.role_id.choices = [("0", "Todos")] + [(str(r.id), getattr(r, "name", r.id)) for r in role_rows]
    else:
        form.role_id.choices = [("0", "Todos")]

    # ocultamos campos de archivo/url para edición
    del form.file
    del form.url
    del form.source_type

    if form.validate_on_submit():
        obj.title = form.title.data
        obj.description = form.description.data
        obj.visibility = form.visibility.data
        if hasattr(obj, "role_id"):
            obj.role_id = None if form.role_id.data == "0" else form.role_id.data
        # actualizar categoría
        AssocCat = getattr(Base.classes, "media_file_category", None)
        if AssocCat is not None:
            db.session.query(AssocCat).filter_by(media_id=media_id).delete()
            if form.category.data:
                db.session.add(AssocCat(media_id=media_id, category_id=form.category.data))
        # actualizar rol
        if hasattr(obj, "role_id"):
            obj.role_id = None if form.role_id.data == "0" else form.role_id.data
        else:
            AssocRole = getattr(Base.classes, "media_file_role", None)
            if AssocRole is not None:
                db.session.query(AssocRole).filter_by(media_id=media_id).delete()
                if form.role_id.data and form.role_id.data != "0":
                    db.session.add(AssocRole(media_id=media_id, role_id=form.role_id.data))
        db.session.commit()
        flash("Archivo actualizado", "success")
        return redirect(url_for("multimedia.list_media"))

    # poblar valores actuales
    if request.method == "GET":
        form.title.data = obj.title
        form.description.data = obj.description
        form.visibility.data = obj.visibility
        # categoria actual
        AssocCat = getattr(Base.classes, "media_file_category", None)
        if AssocCat is not None:
            cat_rel = db.session.query(AssocCat).filter_by(media_id=media_id).first()
            if cat_rel:
                form.category.data = cat_rel.category_id
        # rol actual
        if hasattr(obj, "role_id") and obj.role_id:
            form.role_id.data = str(obj.role_id)
        else:
            AssocRole = getattr(Base.classes, "media_file_role", None)
            if AssocRole is not None:
                role_rel = db.session.query(AssocRole).filter_by(media_id=media_id).first()
                if role_rel:
                    form.role_id.data = str(role_rel.role_id)
    return render_template("records/media_edit.html", form=form, action=url_for("multimedia.edit_media", media_id=media_id))
