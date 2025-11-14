"""
Verificar que el campo nivel_actual fue eliminado de la tabla asesores
"""

import asyncio
from tortoise import Tortoise
from services.core_api.models.user import Asesor


async def verify_removal():
    """Verificar que nivel_actual no existe en el modelo"""
    
    # Inicializar Tortoise
    await Tortoise.init(
        db_url="postgres://postgres:postgres@localhost:5432/teloo_v3",
        modules={"models": ["services.core_api.models"]}
    )
    
    print("🔍 Verificando eliminación de nivel_actual...")
    
    # Verificar que el campo no existe en el modelo
    asesor_fields = Asesor._meta.fields_map.keys()
    
    if 'nivel_actual' in asesor_fields:
        print("❌ ERROR: El campo nivel_actual todavía existe en el modelo Asesor")
        print(f"   Campos actuales: {list(asesor_fields)}")
    else:
        print("✅ Campo nivel_actual eliminado correctamente del modelo Asesor")
        print(f"\n📋 Campos actuales del modelo Asesor:")
        for field_name in sorted(asesor_fields):
            field = Asesor._meta.fields_map[field_name]
            print(f"   - {field_name}: {field.__class__.__name__}")
    
    # Intentar obtener un asesor para verificar
    try:
        asesor = await Asesor.first()
        if asesor:
            print(f"\n✅ Asesor de prueba obtenido: {asesor.usuario.nombre_completo}")
            print(f"   - Confianza: {asesor.confianza}")
            print(f"   - Ciudad: {asesor.ciudad}")
            
            # Verificar que no se puede acceder a nivel_actual
            try:
                _ = asesor.nivel_actual
                print("❌ ERROR: Se puede acceder a nivel_actual (no debería existir)")
            except AttributeError:
                print("✅ Confirmado: nivel_actual no es accesible (correcto)")
    except Exception as e:
        print(f"⚠️ No se pudo obtener asesor de prueba: {e}")
    
    await Tortoise.close_connections()
    print("\n✅ Verificación completada")


if __name__ == "__main__":
    asyncio.run(verify_removal())
