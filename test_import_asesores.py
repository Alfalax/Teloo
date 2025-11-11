"""
Test import asesores endpoint
"""
import requests

# Login as admin first
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={
        "email": "admin@teloo.com",
        "password": "admin123"
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Login successful, token: {token[:20]}...")

# Import Excel file
with open("data/asesores_250_ficticios.xlsx", "rb") as f:
    files = {"file": ("asesores.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    headers = {"Authorization": f"Bearer {token}"}
    
    import_response = requests.post(
        "http://localhost:8000/asesores/import/excel",
        files=files,
        headers=headers
    )

print(f"\n📊 Import Response Status: {import_response.status_code}")
print(f"📄 Response Body:")
print(import_response.json())

if import_response.status_code == 200:
    result = import_response.json()
    print(f"\n✅ Importación completada:")
    print(f"   • Total procesados: {result.get('total_procesados', 0)}")
    print(f"   • Exitosos: {result.get('exitosos', 0)}")
    print(f"   • Errores: {result.get('errores', 0)}")
    
    if result.get('detalles_errores'):
        print(f"\n❌ Primeros errores:")
        for error in result['detalles_errores'][:5]:
            print(f"   • Fila {error['fila']}: {error['errores']}")
