# Guía rápida para Prescriptores: integrar el formulario de Leads por iframe

Esta guía explica cómo embeber el formulario de leads de SIGP en tu web o landing. No requiere login.

## 1) Snippet listo para pegar

Reemplazá PRESCRIPTOR_ID por el ID de tu prescriptor.

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

Parámetros opcionales en la URL:
- program=PROGRAM_ID  (preseleccionar programa)
- success_url=https://tusitio.com/gracias  (redirigir luego de enviar)
- title=Texto  (título del formulario)
- primary=%23HEXCOLOR  (color primario; usar %23 en lugar de #)

Ejemplo con redirección:

```html
<iframe
  src="https://sigp.eniit.es/leads/embed?prescriptor=PRESCRIPTOR_ID&success_url=https%3A%2F%2Ftusitio.com%2Fgracias"
  width="100%" height="620" style="border:0; max-width:720px; width:100%" loading="lazy"></iframe>
```

## 2) ¿Dónde pegarlo?

- WordPress (Gutenberg): bloque “HTML personalizado” → pegar el iframe.
- Elementor/Divi: elemento HTML → pegar el iframe.
- Webflow/Wix/Squarespace: widget/embebido HTML → pegar el iframe.
- HTML puro: dentro del `<body>` de tu página.

Sugerencia: dejá el `width="100%"` y `max-width: 720px` para buen responsive.

## 3) Campos incluidos

- Nombre y apellido (obligatorio)
- Email (opcional)
- Celular (opcional)
- Programa (opcional)
- Observaciones (opcional)

Al enviar, se crea un lead en SIGP asociado a tu PRESCRIPTOR_ID.

## 4) Personalización visual

- `title`: cambia el título visible.
- `primary`: color del botón y enfoque de campos. Ej.: `primary=%2309a36b` para verde.

Si necesitás más personalización, consultá soporte.

## 5) Pruebas recomendadas

1. Pegar el iframe en un borrador de tu página.
2. Completar los campos (usá un email tuyo).
3. Verificar que aparece “¡Gracias!” o se redirige a tu página de gracias.
4. Confirmar en SIGP que el lead se creó.

## 6) Solución de problemas

- El iframe no carga o se ve en blanco
  - Verificar que la URL incluye `prescriptor=PRESCRIPTOR_ID` válido.
  - Si está en tu dominio y no carga, avisá para autorizar el dominio (política CSP de embeber).

- Me pide login
  - Asegurate de usar exactamente la ruta `https://sigp.eniit.es/leads/embed?...`.

- No aparece el lead
  - Revisá que completaste “Nombre y apellido”.
  - Probá sin adblockers/extensiones.
  - Si persiste, compartí fecha/hora y URL usada.

## 7) Preguntas frecuentes (FAQ)

- ¿Puedo cambiar el alto del iframe?
  - Sí, modificá `height="620"`. Si tu página es larga, aumentalo.

- ¿Puedo rastrear conversiones?
  - Usá `success_url` a una página tuya con tu pixel (Meta, Google, etc.).

- ¿Puedo usarlo en varias páginas?
  - Sí. Usá siempre tu mismo `prescriptor` para que los leads se asignen correctamente.

## 8) Contacto

Si necesitás ayuda para integrar o personalizar el formulario, escribinos indicando la URL de tu landing y el PRESCRIPTOR_ID.
