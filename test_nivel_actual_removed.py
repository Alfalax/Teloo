"""
Test completo para verificar que nivel_actual fue eliminado correctamente
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


async def test_modelo():
    """Test 1: Verificar que el campo no existe en el modelo"""
    print("\n" + "="*60)
    print("TEST 1: Verificar modelo Asesor")
    print("="*60)
    
    try:
        from services.core_api.models.user import Asesor
        
        fields = list(Asesor._meta.fields_map.keys())
        
        if 'nivel_actual' in fields:
            print("❌ FALLO: nivel_actual todavía existe en el modelo")
            return False
        else:
            print("✅ ÉXITO: nivel_actual NO existe en el modelo")
            print(f"\n📋 Campos actuales ({len(fields)}):")
            for field in sorted(fields):
                print(f"   - {field}")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_routers():
    """Test 2: Verificar que no existe en routers"""
    print("\n" + "="*60)
    print("TEST 2: Verificar routers/asesores.py")
    print("="*60)
    
    try:
        router_file = Path("services/core-api/routers/asesores.py")
        content = router_file.read_text(encoding='utf-8')
        
        if '"nivel_actual"' in content or "'nivel_actual'" in content:
            print("❌ FALLO: nivel_actual todavía aparece en routers")
            # Contar ocurrencias
            count = content.count('nivel_actual')
            print(f"   Encontradas {count} referencias")
            return False
        else:
            print("✅ ÉXITO: nivel_actual NO aparece en routers")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_services():
    """Test 3: Verificar que no existe en services"""
    print("\n" + "="*60)
    print("TEST 3: Verificar services/asesores_service.py")
    print("="*60)
    
    try:
        service_file = Path("services/core-api/services/asesores_service.py")
        content = service_file.read_text(encoding='utf-8')
        
        if "'nivel_actual'" in content or '"nivel_actual"' in content:
            print("❌ FALLO: nivel_actual todavía aparece en services")
            return False
        else:
            print("✅ ÉXITO: nivel_actual NO aparece en services")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_frontend_types():
    """Test 4: Verificar tipos TypeScript"""
    print("\n" + "="*60)
    print("TEST 4: Verificar tipos TypeScript")
    print("="*60)
    
    try:
        types_file = Path("frontend/admin/src/types/asesores.ts")
        content = types_file.read_text(encoding='utf-8')
        
        if 'nivel_actual' in content:
            print("❌ FALLO: nivel_actual todavía aparece en tipos")
            return False
        else:
            print("✅ ÉXITO: nivel_actual NO aparece en tipos")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_frontend_table():
    """Test 5: Verificar componente de tabla"""
    print("\n" + "="*60)
    print("TEST 5: Verificar AsesoresTable.tsx")
    print("="*60)
    
    try:
        table_file = Path("frontend/admin/src/components/asesores/AsesoresTable.tsx")
        content = table_file.read_text(encoding='utf-8')
        
        if 'nivel_actual' in content:
            print("❌ FALLO: nivel_actual todavía aparece en tabla")
            return False
        else:
            print("✅ ÉXITO: nivel_actual NO aparece en tabla")
            
            # Verificar que la columna "Nivel" fue eliminada
            if '<TableHead>Nivel</TableHead>' in content:
                print("❌ FALLO: Columna 'Nivel' todavía existe en header")
                return False
            else:
                print("✅ ÉXITO: Columna 'Nivel' eliminada del header")
            
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_sql_migration():
    """Test 6: Verificar que existe el script SQL"""
    print("\n" + "="*60)
    print("TEST 6: Verificar script de migración SQL")
    print("="*60)
    
    try:
        sql_file = Path("scripts/remove_nivel_actual_from_asesores.sql")
        
        if not sql_file.exists():
            print("❌ FALLO: Script SQL no existe")
            return False
        
        content = sql_file.read_text(encoding='utf-8')
        
        if 'DROP COLUMN nivel_actual' not in content:
            print("❌ FALLO: Script SQL no contiene DROP COLUMN")
            return False
        
        print("✅ ÉXITO: Script SQL existe y es correcto")
        print(f"   Ubicación: {sql_file}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "="*60)
    print("🧪 SUITE DE TESTS: Eliminación de nivel_actual")
    print("="*60)
    
    results = []
    
    # Test 1: Modelo
    results.append(await test_modelo())
    
    # Test 2: Routers
    results.append(test_routers())
    
    # Test 3: Services
    results.append(test_services())
    
    # Test 4: Frontend Types
    results.append(test_frontend_types())
    
    # Test 5: Frontend Table
    results.append(test_frontend_table())
    
    # Test 6: SQL Migration
    results.append(test_sql_migration())
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Tests exitosos: {passed}/{total}")
    print(f"❌ Tests fallidos: {total - passed}/{total}")
    
    if all(results):
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("\n⚠️  PENDIENTE: Ejecutar migración SQL en la base de datos")
        print("   Comando: psql -U postgres -d teloo_v3 -f scripts/remove_nivel_actual_from_asesores.sql")
        return True
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - Revisar errores arriba")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
