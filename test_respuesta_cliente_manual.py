"""
Test manual del endpoint respuesta-cliente
"""
import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
SOLICITUD_ID = "120df700-47fa-493b-9167-2d23ad6660a1"

# Headers de servicio
headers = {
    "X-Service-API-Key": "m4YQECAHqUZl_4O9p3ZG8YlYjvFF_IAbxiFu6l_6epk",
    "X-Service-Name": "agent-ia",
    "Content-Type": "application/json"
}

# Payload
payload = {
    "respuesta_texto": "acepto",
    "usar_nlp": False
}

print(f"🔍 Probando endpoint respuesta-cliente...")
print(f"URL: {BASE_URL}/v1/solicitudes/{SOLICITUD_ID}/respuesta-cliente")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/v1/solicitudes/{SOLICITUD_ID}/respuesta-cliente",
        headers=headers,
        json=payload,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response text: {e.response.text}")
