# Panel de Administración de Mark

Este documento proporciona información detallada sobre el panel de administración web del asistente Mark, diseñado para el Centre de Psicologia Jaume I.

## Descripción general

El panel de administración es una interfaz web que permite a los administradores y terapeutas del centro gestionar todos los aspectos del asistente Mark, incluyendo:

- Gestión de pacientes
- Seguimiento de sesiones
- Administración de notificaciones
- Configuración del sistema
- Monitorización de actividad

## Acceso al panel

El panel de administración se ejecuta en un puerto separado del servidor API principal:

- **URL**: `http://[host]:8001` (por defecto)
- **Credenciales por defecto**:
  - Usuario: `admin`
  - Contraseña: `mark2024` (debe cambiarse después del primer inicio de sesión)

## Estructura y funcionalidades

### Dashboard

La página principal del panel muestra un resumen de la actividad del sistema:

- Número total de pacientes activos
- Sesiones programadas para hoy y mañana
- Notificaciones pendientes
- Gráficos de actividad reciente
- Alertas del sistema

### Gestión de pacientes

La sección de pacientes permite:

- Ver la lista completa de pacientes
- Buscar pacientes por nombre, teléfono o ID
- Crear nuevos registros de pacientes
- Editar información de pacientes existentes
- Ver el historial de conversaciones de cada paciente
- Asignar etiquetas y notas a los pacientes

### Gestión de sesiones

La sección de sesiones permite:

- Ver todas las sesiones programadas
- Filtrar sesiones por fecha, terapeuta o paciente
- Crear nuevas sesiones manualmente
- Cancelar o reprogramar sesiones existentes
- Ver estadísticas de asistencia

### Notificaciones

La sección de notificaciones permite:

- Ver todas las notificaciones enviadas y pendientes
- Crear nuevas notificaciones programadas
- Configurar recordatorios automáticos
- Ver estadísticas de entrega y lectura

### Configuración del sistema

La sección de configuración permite:

- Gestionar credenciales de servicios externos (Twilio, Calendly, etc.)
- Configurar los playbooks y respuestas predeterminadas
- Ajustar parámetros del sistema
- Gestionar usuarios del panel de administración
- Configurar copias de seguridad

### Registros y auditoría

La sección de registros permite:

- Ver logs del sistema
- Monitorizar errores y advertencias
- Auditar acciones de los usuarios
- Exportar registros para análisis

## Seguridad

El panel de administración implementa varias medidas de seguridad:

- Autenticación basada en JWT (JSON Web Tokens)
- Sesiones con tiempo de expiración configurable
- Registro de todos los intentos de inicio de sesión
- Protección contra ataques de fuerza bruta
- Cifrado de datos sensibles

## Personalización

El panel puede personalizarse mediante:

- Ajustes de marca (logo, colores, etc.)
- Configuración de idioma de la interfaz
- Ajustes de notificaciones por correo electrónico
- Configuración de informes automáticos

## Solución de problemas

### Problemas comunes

1. **No se puede acceder al panel**
   - Verificar que el servidor esté en ejecución
   - Comprobar el puerto configurado en `.env`
   - Verificar las credenciales de inicio de sesión

2. **Sesión cerrada inesperadamente**
   - Las sesiones expiran después del tiempo configurado en `ACCESS_TOKEN_EXPIRE_MINUTES`
   - Iniciar sesión nuevamente

3. **Cambios no guardados**
   - Asegurarse de hacer clic en "Guardar" después de realizar cambios
   - Verificar los logs para posibles errores

### Contacto de soporte

Para problemas técnicos con el panel de administración, contactar con el equipo de desarrollo:

- **Email**: soporte@centrejaume1.com
- **Teléfono**: +34 600 000 000 