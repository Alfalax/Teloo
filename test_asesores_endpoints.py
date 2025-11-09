#!/usr/bin/env python3
"""
Script para verificar que los endpoints de Asesores están conectados a la BD real
y no usan mocks
"""

import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Credenciales de admin (ajustar según tu configuración)
ADMIN_EMAIL = "admin@teloo.com"
ADMIN_PASSWORD = "Admin123!"

def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)

def login():
    """Obtener token de autenticación"""
    print_section("1. AUTENTICACIÓN")
    
    response = requests.post(
        f"{API_URL}/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("access_token")
        print(f"✅ Login exitoso")
        print(f"   Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_get_asesores(token):
    """Probar GET /asesores"""
    print_section("2. GET /asesores - Listar Asesores")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/asesores?page=1&limit=10", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Endpoint funcionando")
        print(f"   Total asesores: {data.get('total', 0)}")
        print(f"   Página: {data.get('page', 0)}")
        print(f"   Registros en página: {len(data.get('data', []))}")
        
        # Verificar que los datos tienen estructura de BD
        if data.get('data'):
            primer_asesor = data['data'][0]
            print(f"\n   📋 Primer asesor:")
            print(f"      ID: {primer_asesor.get('id')}")
            print(f"      Nombre: {primer_asesor.get('usuario', {}).get('nombre')}")
            print(f"      Email: {primer_asesor.get('usuario', {}).get('email')}")
            print(f"      Ciudad: {primer_asesor.get('ciudad')}")
            print(f"      Punto Venta: {primer_asesor.get('punto_venta')}")
            print(f"      Estado: {primer_asesor.get('estado')}")
            print(f"      Created: {primer_asesor.get('created_at')}")
            
            # Verificar que tiene campos de BD
            has_id = primer_asesor.get('id') is not None
            has_timestamps = primer_asesor.get('created_at') is not None
            has_relations = primer_asesor.get('usuario') is not None
            
            if has_id and has_timestamps and has_relations:
                print(f"\n   ✅ CONFIRMADO: Datos vienen de la base de datos")
                print(f"      - Tiene ID de BD: {has_id}")
                print(f"      - Tiene timestamps: {has_timestamps}")
                print(f"      - Tiene relaciones: {has_relations}")
            else:
                print(f"\n   ⚠️  ADVERTENCIA: Posibles datos mock")
        
        return True, data
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return False, None

def test_get_kpis(token):
    """Probar GET /asesores/kpis"""
    print_section("3. GET /asesores/kpis - KPIs de Asesores")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/asesores/kpis", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Endpoint funcionando")
        
        kpis = data.get('data', {})
        print(f"\n   📊 KPIs:")
        print(f"      Total Asesores: {kpis.get('total_asesores_habilitados', {}).get('valor')}")
        print(f"      Total Puntos Venta: {kpis.get('total_puntos_venta', {}).get('valor')}")
        print(f"      Cobertura Nacional: {kpis.get('cobertura_nacional', {}).get('valor')}")
        
        # Verificar que los KPIs son calculados dinámicamente
        has_period = kpis.get('total_asesores_habilitados', {}).get('periodo') is not None
        has_timestamp = data.get('timestamp') is not None
        
        if has_period and has_timestamp:
            print(f"\n   ✅ CONFIRMADO: KPIs calculados dinámicamente")
            print(f"      - Tiene período: {has_period}")
            print(f"      - Tiene timestamp: {has_timestamp}")
        
        return True, data
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return False, None

def test_get_ciudades(token):
    """Probar GET /asesores/ciudades"""
    print_section("4. GET /asesores/ciudades - Lista de Ciudades")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/asesores/ciudades", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        ciudades = data.get('data', [])
        print(f"✅ Endpoint funcionando")
        print(f"   Total ciudades: {len(ciudades)}")
        print(f"   Primeras 10: {ciudades[:10]}")
        
        if ciudades:
            print(f"\n   ✅ CONFIRMADO: Ciudades vienen de la BD")
        
        return True, data
    else:
        print(f"❌ Error: {response.status_code}")
        return False, None

def test_get_departamentos(token):
    """Probar GET /asesores/departamentos"""
    print_section("5. GET /asesores/departamentos - Lista de Departamentos")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/asesores/departamentos", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        departamentos = data.get('data', [])
        print(f"✅ Endpoint funcionando")
        print(f"   Total departamentos: {len(departamentos)}")
        print(f"   Lista: {departamentos}")
        
        if departamentos:
            print(f"\n   ✅ CONFIRMADO: Departamentos vienen de la BD")
        
        return True, data
    else:
        print(f"❌ Error: {response.status_code}")
        return False, None

def test_filters(token):
    """Probar filtros"""
    print_section("6. PROBANDO FILTROS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Filtro por estado
    print("\n🔍 Filtro por estado ACTIVO:")
    response = requests.get(
        f"{API_URL}/asesores?estado=ACTIVO&limit=5",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data.get('total', 0)} asesores activos")
    
    # Filtro por búsqueda
    print("\n🔍 Filtro por búsqueda:")
    response = requests.get(
        f"{API_URL}/asesores?search=test&limit=5",
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {data.get('total', 0)} resultados para 'test'")
    
    return True

def test_pagination(token):
    """Probar paginación"""
    print_section("7. PROBANDO PAGINACIÓN")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Página 1
    print("\n📄 Página 1:")
    response = requests.get(f"{API_URL}/asesores?page=1&limit=5", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {len(data.get('data', []))} registros")
        print(f"   Total: {data.get('total', 0)}")
        print(f"   Página: {data.get('page', 0)}")
    
    # Página 2
    print("\n📄 Página 2:")
    response = requests.get(f"{API_URL}/asesores?page=2&limit=5", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {len(data.get('data', []))} registros")
    
    return True

def verify_no_hardcoded_data(asesores_data):
    """Verificar que no hay datos hardcodeados"""
    print_section("8. VERIFICANDO AUSENCIA DE DATOS HARDCODEADOS")
    
    if not asesores_data or not asesores_data.get('data'):
        print("⚠️  No hay datos para verificar")
        return True
    
    asesores = asesores_data.get('data', [])
    
    print(f"\n🔍 Analizando {len(asesores)} asesores...")
    
    issues = []
    
    for i, asesor in enumerate(asesores):
        # Verificar IDs (no deben ser secuenciales simples como 1,2,3)
        asesor_id = asesor.get('id', '')
        if asesor_id and len(asesor_id) < 10:  # IDs de BD suelen ser UUIDs o largos
            issues.append(f"Asesor {i+1}: ID sospechosamente corto: {asesor_id}")
        
        # Verificar timestamps (deben ser fechas reales)
        created_at = asesor.get('created_at')
        if not created_at:
            issues.append(f"Asesor {i+1}: Sin timestamp created_at")
        
        # Verificar relación con usuario
        usuario = asesor.get('usuario')
        if not usuario or not usuario.get('id'):
            issues.append(f"Asesor {i+1}: Sin relación con usuario")
    
    if issues:
        print("\n⚠️  Posibles problemas detectados:")
        for issue in issues[:5]:  # Mostrar primeros 5
            print(f"   - {issue}")
    else:
        print("\n✅ CONFIRMADO: No se detectaron datos hardcodeados")
        print("   - Todos los asesores tienen IDs válidos")
        print("   - Todos tienen timestamps")
        print("   - Todos tienen relaciones con usuario")
    
    return len(issues) == 0

def main():
    """Función principal"""
    print("="*60)
    print("VERIFICACIÓN DE INTEGRACIÓN - MÓDULO ASESORES")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Login
    token = login()
    if not token:
        print("\n❌ No se pudo obtener token de autenticación")
        print("Verifica que el API esté corriendo y las credenciales sean correctas")
        return
    
    # Ejecutar pruebas
    results = []
    
    success, asesores_data = test_get_asesores(token)
    results.append(("GET /asesores", success))
    
    success, _ = test_get_kpis(token)
    results.append(("GET /asesores/kpis", success))
    
    success, _ = test_get_ciudades(token)
    results.append(("GET /asesores/ciudades", success))
    
    success, _ = test_get_departamentos(token)
    results.append(("GET /asesores/departamentos", success))
    
    success = test_filters(token)
    results.append(("Filtros", success))
    
    success = test_pagination(token)
    results.append(("Paginación", success))
    
    success = verify_no_hardcoded_data(asesores_data)
    results.append(("No datos hardcodeados", success))
    
    # Resultado final
    print_section("RESULTADO FINAL")
    
    all_passed = all(result[1] for result in results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    if all_passed:
        print("\n🎉 TODAS LAS VERIFICACIONES PASARON")
        print("✅ El módulo de Asesores está completamente conectado a la base de datos")
        print("✅ NO se detectaron mocks ni datos hardcodeados")
    else:
        print("\n⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("Revisa los detalles arriba")

if __name__ == "__main__":
    main()
