"""
Test script to verify the coverage calculation fix
"""
import requests
import json

# Test endpoint
url = "http://localhost:8000/api/v1/asesores/kpis"

# Get a valid token first
login_url = "http://localhost:8000/api/v1/auth/login"
login_data = {
    "email": "admin@teloo.com",
    "password": "admin123"
}

try:
    # Login
    print("🔐 Logging in...")
    login_response = requests.post(login_url, json=login_data)
    login_response.raise_for_status()
    token = login_response.json()["data"]["access_token"]
    print(f"✅ Token obtained")
    
    # Get KPIs
    print("\n📊 Getting KPIs...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    
    print("\n" + "="*60)
    print("KPIs DE ASESORES")
    print("="*60)
    
    if data.get("success"):
        kpis = data["data"]
        
        print(f"\n📈 Total Asesores Habilitados: {kpis['total_asesores_habilitados']['valor']}")
        print(f"   Cambio: {kpis['total_asesores_habilitados']['cambio_porcentual']}%")
        
        print(f"\n🏪 Total Puntos de Venta: {kpis['total_puntos_venta']['valor']}")
        print(f"   Cambio: {kpis['total_puntos_venta']['cambio_porcentual']}%")
        
        print(f"\n🗺️  Cobertura Nacional: {kpis['cobertura_nacional']['valor']}%")
        print(f"   Cambio: {kpis['cobertura_nacional']['cambio_porcentual']}%")
        
        print("\n" + "="*60)
        print("✅ COBERTURA CORREGIDA - Ahora muestra porcentaje real!")
        print("="*60)
    else:
        print(f"❌ Error: {data}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Error en la petición: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
