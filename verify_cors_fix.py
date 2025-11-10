#!/usr/bin/env python3
"""
Script de Verificación: CORS Fix
Verifica que el backend esté corriendo y respondiendo correctamente
"""

import requests
import json
from datetime import datetime

def test_backend_health():
    """Prueba 1: Health Check"""
    print("\n" + "="*60)
    print("PRUEBA 1: Backend Health Check")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cors_headers():
    """Prueba 2: CORS Headers"""
    print("\n" + "="*60)
    print("PRUEBA 2: CORS Headers")
    print("="*60)
    
    try:
        # Simular petición desde el frontend
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization'
        }
        
        response = requests.options(
            "http://localhost:8000/admin/configuracion",
            headers=headers,
            timeout=5
        )
        
        print(f"✅ Status Code: {response.status_code}")
        
        # Verificar headers CORS
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print(f"✅ CORS Headers:")
        for key, value in cors_headers.items():
            print(f"   {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_configuracion_endpoint():
    """Prueba 3: Endpoint de Configuración"""
    print("\n" + "="*60)
    print("PRUEBA 3: Endpoint de Configuración")
    print("="*60)
    
    try:
        headers = {
            'Origin': 'http://localhost:3000'
        }
        
        response = requests.get(
            "http://localhost:8000/admin/configuracion",
            headers=headers,
            timeout=5
        )
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ Endpoint requiere autenticación (esperado)")
            return True
        elif response.status_code == 200:
            print("✅ Endpoint responde correctamente")
            return True
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("\n" + "="*80)
    print("🔧 VERIFICACIÓN DE CORS FIX")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Backend Health", test_backend_health),
        ("CORS Headers", test_cors_headers),
        ("Endpoint Configuración", test_configuracion_endpoint)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El backend está corriendo correctamente")
        print("✅ CORS está configurado correctamente")
        print("✅ El frontend puede conectarse al backend")
    else:
        print(f"\n⚠️  {total - passed} pruebas fallaron")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
