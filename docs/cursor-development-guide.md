# Guía de Desarrollo en Cursor para el Asistente Virtual Mark

Este documento proporciona una guía para configurar y desarrollar el asistente virtual Mark utilizando Cursor.

## ¿Qué es Cursor?

[Cursor](https://cursor.sh/) es un editor de código basado en VSCode y potenciado por IA. Está especialmente diseñado para facilitar el desarrollo de aplicaciones que usan modelos de lenguaje y tiene integración con LLMs como Claude y GPT-4.

## Configuración inicial

### 1. Descargar e instalar Cursor

Descarga Cursor desde la [página oficial](https://cursor.sh/) para tu sistema operativo.

### 2. Clonar el repositorio

Abre Cursor y clona este repositorio:

```bash
git clone https://github.com/your-username/virtual-psychology-center.git
```

### 3. Abrir el proyecto en Cursor

Abre la carpeta del proyecto en Cursor.

### 4. Configurar el entorno

Ejecuta el script de configuración que creará un entorno virtual e instalará las dependencias:

```bash
# Hacer ejecutable el script de configuración
chmod +x cursor_setup.sh

# Ejecutar el script
./cursor_setup.sh
```

Este script creará un entorno virtual, instalará las dependencias y configurará el archivo `.env` con valores por defecto.

### 5. Completar la configuración

Edita el archivo `.env` con tus propias claves API y configuraciones. Como mínimo, necesitarás:

- `CLAUDE_API_KEY`: Para la integración con Claude
- `CLOUDFLARE_API_TOKEN`: Para la integración con Cloudflare D1
- `HUME_API_KEY` y `HUME_CONFIG_ID`: Para la integración con Hume EVI

## Estructura del proyecto

El proyecto sigue una estructura modular para facilitar el desarrollo:

```
VirtualPsychologyCenter/
│
├── main.py                           # Punto de entrada principal
├── core/                             # Componentes principales
├── ai/                               # Componentes de IA
│   ├── claude/                       # Integración con Claude
│   ├── hume/                         # Integración con Hume EVI
│   ├── langsmith/                    # Integración con LangSmith
│   ├── langgraph/                    # Flujos de conversación
│   └── serper/                       # Búsqueda web
├── backend/                          # Lógica del servidor
│   └── services/                     # Servicios de integración
├── i18n/                             # Internacionalización
└── database/                         # Base de datos
```

## Desarrollo con Cursor

### Uso de comandos de IA

Cursor facilita el desarrollo con comandos de IA integrados:

1. **Ctrl+K / Cmd+K**: Abre el prompt de IA para hacer preguntas sobre el código
2. **Ctrl+L / Cmd+L**: Explica el código seleccionado
3. **Ctrl+I / Cmd+I**: Sugiere mejoras para el código seleccionado

### Flujo de trabajo recomendado

1. **Inicia el servidor de desarrollo**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Modifica el código**: Utiliza la funcionalidad de IA de Cursor para ayudarte a entender y mejorar el código.

3. **Prueba los cambios**: Utiliza Insomnia, Postman o curl para probar los endpoints API.

4. **Debugging**: Cursor tiene una excelente integración con el debugger de Python. Coloca puntos de interrupción y utiliza la función de depuración.

## Cheatsheet para desarrollo con Cursor

### Comandos útiles

- **Completar código**: `Tab` mientras escribes código
- **Copiar sugerencia completa**: `Ctrl+Enter` / `Cmd+Enter`
- **Pedir ayuda a la IA**: Selecciona código y presiona `Cmd+K` o `Ctrl+K`
- **Modo chat con IA**: Presiona `Ctrl+Shift+L` / `Cmd+Shift+L`
- **Git Graph visual**: Presiona `Ctrl+Shift+G` / `Cmd+Shift+G`

### Solicitudes útiles para la IA de Cursor

- "Añade comentarios de documentación"
- "Optimiza este código"
- "Encuentra problemas en este código"
- "Explica cómo funciona este componente"
- "Genera tests para esta función"

## Consejos para trabajar en PlayBooks de Claude

Los PlayBooks son los componentes centrales del sistema que determinan cómo responde Mark a diferentes situaciones. Cuando trabajes en ellos:

1. **Mantén la coherencia**: Asegúrate de que los PlayBooks sean coherentes entre sí y sigan la misma estructura.

2. **Prueba exhaustivamente**: Verifica que cada PlayBook funcione correctamente en todos los idiomas soportados.

3. **Asegura la detección de idioma**: Verifica que la detección de idioma y el cambio de PlayBook funcionen correctamente.

4. **Mantén la personalidad**: Mark debe mantener su personalidad amigable, profesional y empática.

5. **Utiliza LangSmith**: Monitorea las conversaciones y evalúa la calidad de las respuestas utilizando LangSmith.

## Recursos adicionales

- [Documentación de Cursor](https://cursor.sh/docs)
- [Documentación de Claude](https://docs.anthropic.com/claude/docs)
- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de LangChain](https://python.langchain.com/en/latest/)
- [Documentación de LangSmith](https://js.langchain.com/langsmith/) 