#!/bin/bash
# Script para instalar las dependencias necesarias para Supabase

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Instalando dependencias para Supabase ===${NC}"

# Instalación para Python (SQLAlchemy y Supabase)
echo -e "\n${YELLOW}Instalando dependencias de Python...${NC}"
pip install python-dotenv sqlalchemy psycopg2-binary supabase uuid

# Verificar si la instalación fue exitosa
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencias de Python instaladas correctamente${NC}"
else
    echo -e "${RED}✗ Error al instalar dependencias de Python${NC}"
    echo -e "${YELLOW}Intenta instalar manualmente con: pip install python-dotenv sqlalchemy psycopg2-binary supabase uuid${NC}"
fi

# Instalación para Next.js (si está presente)
if [ -f "package.json" ]; then
    echo -e "\n${YELLOW}Detectado proyecto Next.js. Instalando dependencias...${NC}"
    npm install @supabase/ssr @supabase/supabase-js
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dependencias de Next.js instaladas correctamente${NC}"
    else
        echo -e "${RED}✗ Error al instalar dependencias de Next.js${NC}"
        echo -e "${YELLOW}Intenta instalar manualmente con: npm install @supabase/ssr @supabase/supabase-js${NC}"
    fi
else
    echo -e "\n${YELLOW}No se detectó package.json. Omitiendo instalación de dependencias de Next.js${NC}"
fi

echo -e "\n${GREEN}=== Instalación completada ===${NC}"
echo -e "${YELLOW}Recuerda verificar tu archivo .env con las credenciales correctas de Supabase.${NC}"
echo -e "${YELLOW}Para probar la conexión, ejecuta: python database/sqlalchemy_client.py${NC}"
echo -e "${YELLOW}Para ver ejemplos de uso, ejecuta: python examples/supabase_integration.py${NC}" 