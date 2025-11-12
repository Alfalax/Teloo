"""
Script para verificar cuántos asesores se importaron
"""

import psycopg2

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "teloo_db",
    "user": "teloo_user",
    "password": "teloo_password"
}

def verify_import():
    """Verify asesores import"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Count total asesores
        cursor.execute("SELECT COUNT(*) FROM asesor")
        total_asesores = cursor.fetchone()[0]
        
        # Count by estado
        cursor.execute("""
            SELECT estado, COUNT(*) 
            FROM asesor 
            GROUP BY estado
        """)
        by_estado = cursor.fetchall()
        
        # Count usuarios with ADVISOR role
        cursor.execute("""
            SELECT COUNT(*) 
            FROM usuario 
            WHERE rol = 'ADVISOR'
        """)
        total_usuarios = cursor.fetchone()[0]
        
        # Get sample of imported asesores
        cursor.execute("""
            SELECT a.id, u.nombre, u.apellido, u.email, a.ciudad, a.estado
            FROM asesor a
            JOIN usuario u ON a.usuario_id = u.id
            WHERE u.email LIKE 'asesor%@teloo.com'
            ORDER BY u.email
            LIMIT 10
        """)
        samples = cursor.fetchall()
        
        print("=" * 60)
        print("VERIFICACIÓN DE IMPORTACIÓN DE ASESORES")
        print("=" * 60)
        print(f"\n📊 Total asesores en BD: {total_asesores}")
        print(f"👥 Total usuarios ADVISOR: {total_usuarios}")
        
        print(f"\n📈 Distribución por estado:")
        for estado, count in by_estado:
            print(f"   • {estado}: {count}")
        
        print(f"\n📋 Muestra de asesores importados:")
        for asesor in samples:
            print(f"   • {asesor[1]} {asesor[2]} ({asesor[3]}) - {asesor[4]} - {asesor[5]}")
        
        if total_asesores >= 250:
            print(f"\n✅ Importación exitosa: {total_asesores} asesores en BD")
        else:
            print(f"\n⚠️  Solo se importaron {total_asesores} asesores (esperados: 250)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_import()
