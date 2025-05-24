# Solución de problemas de conexión con Supabase

Esta guía te ayudará a solucionar problemas comunes al conectar con Supabase desde tu aplicación.

## Problemas comunes

### Error: Connection timed out

```
connection to server at "db.vtfyydqigxiowkswgreu.supabase.co" port 5432 failed: Connection timed out
```

**Posibles causas y soluciones:**

1. **Lista blanca de IP**
   - Asegúrate de que tu dirección IP esté en la lista blanca de Supabase.
   - Ve a: Supabase Dashboard → Proyecto → Settings → Database → Connection Pooling → IP Allow List

2. **Firewall**
   - Verifica que no haya un firewall bloqueando las conexiones salientes al puerto 5432 o 6543.
   - Si estás detrás de un firewall corporativo, consulta con tu administrador de red.

3. **Credenciales incorrectas**
   - Asegúrate de que el host, puerto, nombre de usuario y contraseña sean correctos.
   - Verifica los datos en el archivo `.env` y compáralos con los que aparecen en el panel de Supabase.

### Error: Password authentication failed

```
FATAL: password authentication failed for user "postgres"
```

**Posibles causas y soluciones:**

1. **Contraseña incorrecta**
   - Verifica que la contraseña en tu archivo `.env` sea correcta.
   - Si has cambiado recientemente la contraseña, asegúrate de actualizar el archivo `.env`.

2. **Usuario incorrecto**
   - Para conexión directa: usa `postgres` como usuario.
   - Para connection pooler: usa `postgres.REFERENCIA_PROYECTO` como usuario, donde REFERENCIA_PROYECTO es el identificador de tu proyecto (ej: `vtfyydqigxiowkswgreu`).

### Error: permission denied for schema public

```
{'code': '42501', 'details': None, 'hint': None, 'message': 'permission denied for schema public'}
```

**Posibles causas y soluciones:**

1. **Problemas con Row Level Security (RLS)**
   - Verifica las políticas RLS en las tablas que estás intentando acceder.
   - Para operaciones administrativas, usa la clave de servicio (`SUPABASE_SERVICE_KEY`).

2. **Faltan permisos**
   - Asegúrate de que el usuario tenga los permisos necesarios para la operación que intentas realizar.
   - Puedes gestionar los permisos en: Supabase Dashboard → SQL Editor → Ejecuta comandos SQL para otorgar permisos.

## Comprobación de conexión paso a paso

Si sigues teniendo problemas, sigue estos pasos para comprobar la conexión:

1. **Verificar credenciales desde el panel de Supabase**
   - Ir a Supabase Dashboard → Proyecto → Settings → Database
   - Copiar los valores de "Connection string", "Host", "Password", etc.

2. **Probar con psql (si está instalado)**
   ```bash
   # Conexión directa
   psql postgresql://postgres:TU_CONTRASEÑA@db.vtfyydqigxiowkswgreu.supabase.co:5432/postgres

   # Conexión con transaction pooler
   psql postgresql://postgres.vtfyydqigxiowkswgreu:TU_CONTRASEÑA@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```

3. **Verificar si Supabase está operativo**
   - Visita [Supabase Status](https://status.supabase.com/) para comprobar si hay algún problema conocido.

4. **Habilitar la función de Database Preview en Supabase**
   - Supabase Dashboard → Database → SQL Editor o Table Editor
   - Esto te permite ver y manipular los datos directamente desde el navegador.

## Tipos de conexión a Supabase

Supabase ofrece tres formas de conectarse a la base de datos:

1. **Conexión directa** (puerto 5432)
   - Uso: Operaciones que requieren una conexión duradera
   - Host: `db.vtfyydqigxiowkswgreu.supabase.co`
   - Usuario: `postgres`
   - Puerto: `5432`

2. **Transaction Pooler** (puerto 6543)
   - Uso: Para aplicaciones con muchas conexiones cortas
   - Host: `aws-0-eu-central-1.pooler.supabase.com`
   - Usuario: `postgres.vtfyydqigxiowkswgreu`
   - Puerto: `6543`
   - Nota: Deshabilita el pooling de SQLAlchemy cuando uses Transaction Pooler

3. **Session Pooler** (puerto 5432 en el subdominio pooler)
   - Uso: Para aplicaciones que necesitan mantener el estado de la sesión
   - Host: `aws-0-eu-central-1.pooler.supabase.com`
   - Usuario: `postgres.vtfyydqigxiowkswgreu`
   - Puerto: `5432`
   - Nota: Deshabilita el pooling de SQLAlchemy cuando uses Session Pooler

## Cliente API vs SQLAlchemy

En este proyecto proporcionamos dos formas de interactuar con Supabase:

1. **Cliente API de Supabase (`SupabaseClient`)**
   - Ventajas: Más simple, gestiona autenticación, RLS transparentemente
   - Desventajas: Menos flexible para operaciones complejas

2. **SQLAlchemy ORM (`SupabaseAlchemyClient`)**
   - Ventajas: Más potente, soporte para ORM, transacciones complejas
   - Desventajas: Requiere más configuración, gestión manual de RLS

## Recursos adicionales

- [Documentación oficial de Supabase](https://supabase.com/docs)
- [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
- [Guía de Postgrest (API REST para PostgreSQL)](https://postgrest.org/en/stable/) 