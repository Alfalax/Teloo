"""
Script para verificar la última solicitud creada usando SQL directo
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def verify_last_solicitud():
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="teloo_db",
            user="teloo_user",
            password="teloo_password"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener la última solicitud
        cursor.execute("""
            SELECT 
                s.*,
                c.nombre as cliente_nombre,
                c.telefono as cliente_telefono,
                c.email as cliente_email
            FROM solicitudes s
            LEFT JOIN clientes c ON s.cliente_id = c.id
            ORDER BY s.created_at DESC
            LIMIT 1
        """)
        
        solicitud = cursor.fetchone()
        
        if not solicitud:
            print("❌ No se encontraron solicitudes en la base de datos")
            return
        
        print("=" * 80)
        print("✅ ÚLTIMA SOLICITUD CREADA")
        print("=" * 80)
        print(f"\n📋 INFORMACIÓN GENERAL:")
        print(f"   ID: {solicitud['id']}")
        print(f"   Estado: {solicitud['estado']}")
        print(f"   Nivel Actual: {solicitud['nivel_actual']}")
        print(f"   Creada: {solicitud['created_at']}")
        print(f"   Actualizada: {solicitud['updated_at']}")
        
        print(f"\n👤 INFORMACIÓN DEL CLIENTE:")
        print(f"   Nombre: {solicitud['cliente_nombre']}")
        print(f"   Teléfono: {solicitud['cliente_telefono']}")
        print(f"   Email: {solicitud['cliente_email'] or 'N/A'}")
        
        print(f"\n📍 UBICACIÓN:")
        print(f"   Ciudad: {solicitud['ciudad_origen']}")
        print(f"   Departamento: {solicitud['departamento_origen']}")
        
        # Obtener repuestos
        cursor.execute("""
            SELECT *
            FROM repuestos_solicitados
            WHERE solicitud_id = %s
            ORDER BY created_at
        """, (solicitud['id'],))
        
        repuestos = cursor.fetchall()
        
        print(f"\n🔧 REPUESTOS SOLICITADOS ({len(repuestos)}):")
        for i, repuesto in enumerate(repuestos, 1):
            print(f"\n   {i}. {repuesto['nombre']}")
            print(f"      - ID: {repuesto['id']}")
            print(f"      - Código: {repuesto['codigo'] or 'N/A'}")
            print(f"      - Cantidad: {repuesto['cantidad']}")
            print(f"      - Vehículo: {repuesto['marca_vehiculo']} {repuesto['linea_vehiculo'] or ''} ({repuesto['anio_vehiculo']})")
            if repuesto.get('descripcion'):
                print(f"      - Descripción: {repuesto['descripcion']}")
            if repuesto.get('observaciones'):
                print(f"      - Observaciones: {repuesto['observaciones']}")
            if repuesto.get('es_urgente'):
                print(f"      - ⚠️  URGENTE")
            print(f"      - Creado: {repuesto['created_at']}")
        
        if solicitud.get('metadata_json'):
            print(f"\n📊 METADATA:")
            metadata = solicitud['metadata_json']
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            for key, value in metadata.items():
                print(f"   {key}: {value}")
        
        # Estadísticas adicionales
        cursor.execute("SELECT COUNT(*) as total FROM solicitudes")
        total_solicitudes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM repuestos_solicitados")
        total_repuestos = cursor.fetchone()['total']
        
        print("\n" + "=" * 80)
        print("📊 ESTADÍSTICAS GENERALES:")
        print(f"   Total de solicitudes en BD: {total_solicitudes}")
        print(f"   Total de repuestos en BD: {total_repuestos}")
        print("=" * 80)
        print("✅ Verificación completada exitosamente")
        print("=" * 80)
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error de base de datos: {str(e)}")
    except Exception as e:
        print(f"❌ Error al verificar la solicitud: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_last_solicitud()
