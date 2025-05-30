#!/usr/bin/env python3
"""
Script para verificar que el webhook de WhatsApp esté funcionando.
"""
import requests
import sys

# URL del webhook
WEBHOOK_URL = "https://mark-api.onrender.com/api/whatsapp/webhook"

print("\n=== Probando Webhook de WhatsApp ===")
print(f"URL: {WEBHOOK_URL}")

# Verificar que el webhook responde a GET (verificación de Meta)
try:
    print("\n1. Probando GET (verificación)...")
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "test_challenge_123",
        "hub.verify_token": "mark_webhook_2024"  # Cambiar por tu token real
    }
    
    response = requests.get(WEBHOOK_URL, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
    
    if response.status_code == 200:
        print("   ✅ Webhook GET funciona correctamente")
    else:
        print("   ❌ Error en webhook GET")
        
except Exception as e:
    print(f"   ❌ Error conectando: {e}")

# Verificar que el endpoint existe
try:
    print("\n2. Verificando que el endpoint POST existe...")
    response = requests.post(WEBHOOK_URL, json={}, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code in [200, 400, 401, 403]:
        print("   ✅ Endpoint POST existe")
    else:
        print("   ❌ Endpoint POST no encontrado")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n=== IMPORTANTE ===")
print("Si ambas pruebas pasan, verifica en Meta Business que:")
print(f"1. La URL del webhook sea: {WEBHOOK_URL}")
print("2. El token de verificación coincida con WHATSAPP_VERIFY_TOKEN")
print("3. El webhook esté suscrito a 'messages' y 'messaging_postbacks'")
print("4. El webhook esté verificado (marca verde)") 