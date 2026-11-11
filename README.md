# Portal Contable

Aplicación web (Streamlit) con herramientas para el área contable. Se entra con usuario y contraseña.

| Herramienta | Para qué sirve |
|---|---|
| Comparativa Contable | Cruza el extracto bancario contra el libro contable. Reconoce los gastos bancarios acumulados. |
| Comparativa IVA | Compara NIT, nombre e IVA de las facturas electrónicas contra el libro auxiliar de IVA. |
| Traslado de Nómina | Pasa la información del archivo 3.3 al 3.2 y genera la hoja SIIGO. |
| Anexos ESF / ERI | Genera los estados financieros y sus anexos desde el archivo de Anexos. |
| Agente de Datos | Responde preguntas sobre un Excel o CSV con IA (Gemini, capa gratuita). |
| Comparativa Contable 2 | Igual a la comparativa, pero lee extractos en PDF con OpenAI. |

## Ejecutarla en el computador

Necesitas Python 3.10, 3.11 o 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Crea tu archivo de configuración a partir del ejemplo y complétalo (ver las secciones siguientes):

```bash
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Y arranca la aplicación:

```bash
streamlit run Inicio.py
```

`.streamlit/secrets.toml` guarda contraseñas y claves. **No se sube a GitHub** (está en `.gitignore`). Nunca lo envíes por correo ni lo pegues en un chat.

## Usuarios y contraseñas

Los usuarios se definen en `secrets.toml`, y la contraseña se guarda cifrada. Para cifrar una:

```bash
python -c "import streamlit_authenticator as s; print(s.Hasher(['TuContraseña']).generate()[0])"
```

Copia el resultado en el campo `password` del usuario. Para agregar otro usuario, copia el bloque `[credentials.admin]` y cambia el nombre.

La sesión dura `expiry_days` días (por defecto 1). Pasado ese tiempo hay que iniciar sesión otra vez.

## Agente de Datos con Gemini (configurar la API)

### Cómo funciona

1. Subes un Excel o CSV.
2. Conversas con el archivo en un chat. Escribes una pregunta, por ejemplo: "¿Cuánto suma la columna Valor por cada concepto?", y puedes seguir preguntando sobre la respuesta ("¿y el segundo?", "de esos, ¿cuál es el mayor?"). Con **Nueva conversación** empiezas de cero.
3. Gemini recibe **la pregunta, los nombres de las columnas y 3 filas de ejemplo** (no el archivo completo) y propone un cálculo.
4. El cálculo se hace en la aplicación, sobre todos los datos, y Gemini redacta la respuesta.
5. La respuesta se muestra en lenguaje normal, sin código. Debajo aparece qué modelo la generó.

### Obtener la clave (gratis)

1. Entra a <https://aistudio.google.com/apikey> con una cuenta de Google.
2. Pulsa **Create API key** (Crear clave de API) y elige o crea un proyecto.
3. Copia la clave. Es un texto largo que empieza por `AIza`.

### Dónde ponerla

Elige **una** de estas opciones:

**A. Pegarla en la pantalla (la más rápida para probar).** Abre el Agente de Datos, sube un archivo y pega la clave en *Configuración de Gemini*. Solo se usa en esa sesión y no se guarda.

**B. En `secrets.toml` (queda fija).** Agrega al final del archivo:

```toml
[gemini]
api_key = "AIza...tu-clave..."
model = "gemini-3.6-flash"   # opcional
```

**C. Como variable de entorno** (en PowerShell, antes de arrancar):

```powershell
$env:GEMINI_API_KEY = "AIza...tu-clave..."
streamlit run Inicio.py
```

**En Streamlit Cloud:** abre la aplicación, *Settings*, *Secrets*, y pega el mismo bloque `[gemini]` de la opción B.

### Modelos y límites

**Qué modelo elegir.** Lo más fácil es dejar **Automático** (es lo que viene por defecto): empieza por el más liviano y, si está lleno o saturado, pasa solo al siguiente.

| Modelo | Cuándo usarlo |
|---|---|
| `gemini-3.5-flash-lite` (Rápido y liviano) | Para empezar y para preguntas directas: sumas, conteos, filtros, totales por grupo. Responde en pocos segundos. |
| `gemini-3.1-flash-lite` (Liviano, alternativa) | Si el anterior está lleno o no responde. |
| `gemini-3.6-flash` (Más preciso) | Preguntas largas o de varios pasos. Su cupo gratuito es muy pequeño. |
| `gemini-3.8-flash` (El más nuevo) | Solo si los demás fallan: suele estar saturado. |

**Cupos de la capa gratuita.** Cada modelo tiene su propio cupo diario, y cada pregunta gasta 2 o más consultas. Al probar esto (noviembre de 2026), `gemini-3.6-flash` permitía 20 consultas al día, y los modelos más nuevos estaban saturados. Estos datos cambian: los cupos vigentes de tu proyecto se ven en <https://aistudio.google.com/rate-limit>, y los modelos disponibles en <https://aistudio.google.com/docs/models>.

Si un nombre de modelo deja de existir, elige otro de la lista o escribe el vigente en **Otro modelo**. También puedes fijar uno en `secrets.toml` con `model = "..."` dentro de `[gemini]`.

**Para que el agente no invente cifras:** en cada pregunta se le obliga a calcular con los datos (no puede responder de memoria). El código que usa para calcular no se muestra a las personas.

### Privacidad (importante)

Con la capa gratuita, **Google puede usar lo que se envía para mejorar sus productos**. Por eso:

- Usa el agente solo con **datos de prueba**: nada de nóminas, cédulas, saldos de clientes ni información confidencial.
- Para usarlo con datos reales hace falta una clave de pago (en el plan de pago Google indica que el contenido no se usa para mejorar sus productos). Revisa las condiciones vigentes antes de decidir.

### Seguridad del cálculo

El código que propone Gemini solo puede trabajar con los datos cargados: no puede leer ni escribir archivos, ni importar librerías. Es una protección razonable, no un aislamiento total, y es otra razón para usar datos de prueba.

### Si algo falla

| Mensaje | Qué hacer |
|---|---|
| Falta la API key de Gemini | Pega la clave en la pantalla o configúrala como se explicó arriba. |
| La clave no es válida | Cópiala de nuevo completa desde Google AI Studio. |
| El modelo no existe | Elige «Automático» u otro modelo de la lista, o escribe uno vigente. |
| Se agotó el cupo diario | Elige «Automático» (usa otros modelos con su propio cupo) o espera al día siguiente. |
| Límite por minuto | Espera un minuto. El agente también espera y reintenta solo cuando Google lo permite. |
| El servicio está saturado (error 503) | Es temporal y es de Google. En «Automático» el agente pasa al siguiente modelo; si elegiste uno fijo, reintenta solo un par de veces. |
| No devolvió una respuesta | El mensaje indica la causa (respuesta bloqueada, demasiado larga o muchos pasos). Reformula con los nombres de las columnas. |

## Comparativa Contable 2 (PDF)

Esta herramienta lee los extractos en PDF con OpenAI. Necesita una clave de OpenAI en `secrets.toml`:

```toml
[settings]
key = "sk-...tu-clave..."
```

## Estructura del proyecto

```
Inicio.py        Pantalla de inicio y login
pages/           Una archivo por herramienta
ui.py            Estilos y componentes de diseño compartidos
sesion.py        Manejo de la sesión y la cookie de inicio de sesión
agente.py        Lógica del Agente de Datos (Gemini)
.streamlit/      Configuración (secrets.toml no se sube a GitHub)
```
