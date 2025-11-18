import requests
import json

# Configuración
BASE_URL = "http://localhost:8001/api"
ASESOR_EMAIL = "asesor006_1762827727@teloo.com"
ASESOR_PASSWORD = "Teloo2024!"

# 1. Login
print("1. Haciendo login...")
login_response = requests.post(
    f"{BASE_URL}/v1/auth/login",
    json={"email": ASESOR_EMAIL, "password": ASESOR_PASSWORD}
)
print(f"Status: {login_response.status_code}")

if login_response.status_code != 200:
    print(f"Error en login: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Obtener solicitudes
print("\n2. Obteniendo solicitudes...")
solicitudes_response = requests.get(
    f"{BASE_URL}/v1/solicitudes",
    headers=headers,
    params={"page": 1, "page_size": 100}
)
print(f"Status: {solicitudes_response.status_code}")

if solicitudes_response.status_code != 200:
    print(f"Error: {solicitudes_response.text}")
    exit(1)

data = solicitudes_response.json()
solicitudes = data.get("items", [])

print(f"\n3. Total solicitudes: {len(solicitudes)}")
print(f"   Total en respuesta: {data.get('total', 0)}")

# 3. Analizar cada solicitud
for i, sol in enumerate(solicitudes, 1):
    print(f"\n--- Solicitud {i} ---")
    print(f"ID: {sol['id']}")
    print(f"Estado: {sol['estado']}")
    print(f"Nivel: {sol.get('nivel_actual', 'N/A')}")
    print(f"Tiene mi_oferta: {'Sí' if sol.get('mi_oferta') else 'No'}")
    
    if sol.get('mi_oferta'):
        print(f"  Estado oferta: {sol['mi_oferta'].get('estado', 'N/A')}")
        print(f"  Detalles: {len(sol['mi_oferta'].get('detalles', []))} repuestos")

print("\n✅ Prueba completada")
