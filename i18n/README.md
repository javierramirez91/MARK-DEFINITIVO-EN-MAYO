# Sistema de Internacionalización para Mark

Este módulo proporciona soporte multilingüe para el asistente virtual Mark del Centre de Psicologia Jaume I.

## Características

- **Soporte para múltiples idiomas**: Español (por defecto), Catalán, Inglés y Árabe.
- **Formato estructurado**: Mensajes organizados por categorías para facilitar su mantenimiento.
- **Carga dinámica**: Posibilidad de cargar mensajes desde archivos Python o JSON.
- **Validación de mensajes**: Herramientas para verificar la consistencia entre idiomas.
- **Actualización en tiempo real**: Capacidad para modificar mensajes sin reiniciar la aplicación.

## Estructura de Mensajes

Los mensajes están organizados en categorías para facilitar su mantenimiento:

- `welcome`: Mensajes de bienvenida y retorno.
- `intake`: Mensajes para el proceso de admisión de pacientes.
- `scheduling`: Mensajes relacionados con la programación de citas.
- `payments`: Mensajes sobre pagos y facturación.
- `crisis`: Mensajes para situaciones de crisis.
- `followup`: Mensajes de seguimiento post-sesión.
- `errors`: Mensajes de error.
- `security`: Mensajes relacionados con la seguridad.
- `fields`: Nombres de campos de formularios.
- `specialties`: Nombres de especialidades psicológicas.
- `formats`: Formatos de sesión.
- `confirmation`: Respuestas de confirmación.
- `fallback`: Mensajes para cuando no se entiende la solicitud.

## Uso

### Obtener un mensaje

```python
from i18n import get_message

# Mensaje simple
mensaje = get_message("welcome.greeting", "es")

# Mensaje con variables
mensaje = get_message("intake.personal_info_confirmation", "ca", 
                     name="Joan Pérez", 
                     phone="612345678", 
                     email="joan@example.com", 
                     reason="Ansiedad")
```

### Validar mensajes

```python
from i18n import validate_messages

# Verificar que todos los idiomas tengan las mismas claves
resultados = validate_messages()
print(f"Idioma por defecto: {resultados['default_language']}")
print(f"Total de claves: {resultados['default_keys_count']}")

# Revisar idiomas con mensajes faltantes
for lang, info in resultados["languages"].items():
    if info["missing_count"] > 0:
        print(f"El idioma {lang} tiene {info['missing_count']} mensajes faltantes")
```

### Actualizar mensajes

```python
from i18n import update_message, save_messages_to_json

# Actualizar un mensaje específico
update_message("es", "welcome.greeting", "¡Hola! Soy Mark, ¿en qué puedo ayudarte?")

# Guardar los cambios en archivos JSON
save_messages_to_json()
```

### Añadir un nuevo idioma

```python
from i18n import add_language, translate_missing_keys

# Añadir un nuevo idioma (por ejemplo, francés)
add_language("fr", {
    "welcome": {
        "greeting": "Bonjour! Je suis Mark, comment puis-je vous aider aujourd'hui?",
        "returning": "Bienvenue à nouveau! Comment puis-je vous aider aujourd'hui?"
    }
})

# Traducir automáticamente las claves faltantes
translate_missing_keys("fr")
```

## Archivos

- `__init__.py`: Exporta las funciones principales del módulo.
- `messages.py`: Implementa la lógica principal del sistema de mensajes.
- `es.py`, `ca.py`, `en.py`, `ar.py`: Contienen los mensajes en cada idioma.
- `json/`: Directorio con versiones JSON de los mensajes para carga dinámica.

## Mejoras Futuras

- Integración con servicios de traducción automática para facilitar la adición de nuevos idiomas.
- Interfaz de administración para gestionar traducciones.
- Soporte para pluralización y formatos complejos.
- Pruebas automatizadas para verificar la consistencia de los mensajes. 