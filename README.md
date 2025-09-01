# sigp

## Ejecución Local
```bash
FLASK_APP=sigp:create_app flask --debug run --port 5001  
```

## Migraciones de base de datos (Alembic)

El proyecto parte de la revisión **baseline_20250708**.  Todas las migraciones
futuras deben colgar de esta para mantener una historia lineal y evitar
conflictos.

Pasos recomendados:

1. Crea tu rama de trabajo y asegúrate de tener la base actualizada:

   ```bash
   git checkout -b feature/mi-cambio
   git pull origin main
   ```

2. Genera la migración con autogeneración de metadatos ya reflejados:

   ```bash
   alembic revision --autogenerate -m "<descripción>"
   ```

   *No uses* `--head` ni cambies `down_revision`; Alembic ajustará la cadena
   automáticamente al último commit de la rama principal de migraciones.

3. Revisa y ajusta el script generado antes de aplicarlo.

4. Aplica la migración localmente para verificar:

   ```bash
   alembic upgrade head
   ```

5. Sube la rama y abre un *pull-request*.  La CI aplicará `alembic upgrade head`
   contra una base de pruebas para asegurar su validez.

Resumiendo: **nunca reescribas migraciones ya compartidas**.  Si necesitas
corregir algo, genera una nueva migración que modifique lo necesario.

## Formulario de Leads embebible (público)

Se agregó un formulario público para capturar leads embebido via `<iframe>`.

- **Vista (GET)**: `leads.embed_lead_get()` en `controllers/leads_controller.py`
- **Creación (POST)**: `leads.embed_lead_post()` en `controllers/leads_controller.py`
- **Template**: `templates/public/lead_embed.html`

### Endpoints

- GET `/leads/embed?prescriptor=<ID>&title=<txt>&primary=<hex>&program=<PROGRAM_ID>&success_url=<URL>`
  - Renderiza el formulario dentro del iframe. No requiere login.
- POST `/leads/embed` (form-data)
  - Crea el lead y muestra “gracias” o redirige a `success_url` si se indicó.

### Parámetros soportados (GET)

- `prescriptor` (requerido): ID del prescriptor al que se asocia el lead.
- `title` (opcional): título a mostrar en el encabezado. Por defecto: “Quiero información”.
- `primary` (opcional): color primario en HEX. Ej: `%230d6efd` para `#0d6efd`.
- `program` (opcional): ID de programa a preseleccionar en el combo.
- `success_url` (opcional): URL a la que se redirige dentro del iframe al crear el lead.

### Campos del formulario (POST)

- `prescriptor_id` (hidden)
- `candidate_name` (obligatorio)
- `candidate_email` (opcional)
- `candidate_cellular` (opcional)
- `program_info_id` (opcional)
- `observations` (opcional) — se persiste si el modelo `Lead` posee esa columna.

### Seguridad de Embebido (CSP)

La acción GET/POST de `/leads/embed` aplica encabezado CSP `frame-ancestors` para controlar en qué orígenes puede embeberse:

- Variable de entorno `EMBED_ALLOWED_ORIGINS` (separado por comas):
  - Ej.: `EMBED_ALLOWED_ORIGINS="https://tusitio.com, https://otro.com"`
  - Si está vacía o no definida, se permite `*` (cualquiera). Recomendada su configuración en producción.

Además, se remueve `X-Frame-Options` para no bloquear el iframe.

### Ejemplo de iframe para prescriptores

```html
<iframe
  src="https://sigp.eniit.es/leads/embed?prescriptor=PRESCRIPTOR_ID&title=Quiero+información&primary=%230d6efd"
  width="100%"
  height="620"
  style="border:0; max-width: 720px; width: 100%;"
  loading="lazy"
  referrerpolicy="no-referrer-when-downgrade"
  allowtransparency="true">
</iframe>
```

Parámetros opcionales: `program`, `success_url`, `title`, `primary`.

### Cómo probar localmente

1. Ejecutar la app en `http://127.0.0.1:5001` (ver “Ejecución Local”).
2. Abrir en el navegador:
   - `http://127.0.0.1:5001/leads/embed?prescriptor=<ID>&title=Quiero+información&primary=%230d6efd`
3. Completar y enviar. Verás “¡Gracias!” o redirección si definiste `success_url`.
4. Verificar en el panel que el lead se creó y que `observations` quedó persistido si la columna existe.

### Manejo de errores comunes

- 404/redirect a login: asegurarse de haber desplegado estas rutas y que no haya middleware global forzando auth.
- El iframe no carga en otros dominios: configurar `EMBED_ALLOWED_ORIGINS`.
- Validación: `candidate_name` requerido; email opcional con validación básica.