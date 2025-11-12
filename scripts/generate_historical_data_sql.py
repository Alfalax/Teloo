"""
Script para generar datos históricos simulados usando SQL directo
Se ejecuta después de importar los asesores desde Excel
"""

import psycopg2
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "teloo_v3",
    "user": "teloo_user",
    "password": "teloo_password"
}


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)


def generate_historical_data():
    """Generate historical data for asesores"""
    print("🚀 Generando datos históricos para asesores...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all asesores (table name is 'asesores' plural)
        cursor.execute("SELECT id FROM asesores WHERE estado = 'ACTIVO'")
        asesores = cursor.fetchall()
        
        if not asesores:
            print("   ⚠️  No hay asesores en la base de datos.")
            print("   Por favor, importa los asesores desde Excel primero.")
            return
        
        print(f"   📊 Encontrados {len(asesores)} asesores")
        
        total_historial = 0
        total_ofertas = 0
        total_auditorias = 0
        
        for i, (asesor_id,) in enumerate(asesores, 1):
            # Generar historial de respuestas (últimos 30 días)
            num_respuestas = random.randint(5, 20)
            for _ in range(num_respuestas):
                fecha_envio = datetime.now() - timedelta(days=random.randint(1, 30))
                respondio = random.random() > 0.3  # 70% responde
                tiempo_respuesta = random.randint(300, 7200) if respondio else None
                
                cursor.execute("""
                    INSERT INTO historial_respuesta_oferta 
                    (asesor_id, fecha_envio, respondio, tiempo_respuesta_seg)
                    VALUES (%s, %s, %s, %s)
                """, (str(asesor_id), fecha_envio, respondio, tiempo_respuesta))
                total_historial += 1
            
            # Generar ofertas históricas (últimos 6 meses)
            num_ofertas = random.randint(10, 50)
            for _ in range(num_ofertas):
                fecha = (datetime.now() - timedelta(days=random.randint(1, 180))).date()
                adjudicada = random.random() > 0.7  # 30% gana
                aceptada = adjudicada and random.random() > 0.2  # 80% de ganadoras son aceptadas
                exitosa = aceptada and random.random() > 0.1  # 90% de aceptadas son exitosas
                monto = Decimal(str(random.randint(100000, 5000000)))
                tiempo_respuesta = random.randint(300, 7200)
                
                cursor.execute("""
                    INSERT INTO oferta_historica 
                    (asesor_id, fecha, monto, adjudicada, aceptada_cliente, entrega_exitosa, tiempo_respuesta_seg)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (str(asesor_id), fecha, monto, adjudicada, aceptada, exitosa, tiempo_respuesta))
                total_ofertas += 1
            
            # Generar auditoría de confianza (50% de asesores tienen auditoría reciente)
            if random.random() > 0.5:
                fecha_revision = datetime.now() - timedelta(days=random.randint(1, 25))
                puntaje = Decimal(str(round(random.uniform(2.5, 5.0), 2)))
                
                cursor.execute("""
                    INSERT INTO auditoria_tienda 
                    (asesor_id, fecha_revision, puntaje_confianza, vigencia_dias, observaciones)
                    VALUES (%s, %s, %s, %s, %s)
                """, (str(asesor_id), fecha_revision, puntaje, 30, f"Auditoría automática - Puntaje: {puntaje}"))
                total_auditorias += 1
            
            if i % 50 == 0:
                print(f"   ✓ Procesados {i}/{len(asesores)} asesores...")
                conn.commit()  # Commit cada 50 asesores
        
        # Final commit
        conn.commit()
        
        print(f"\n✅ Datos históricos generados:")
        print(f"   • Historial respuestas: {total_historial}")
        print(f"   • Ofertas históricas: {total_ofertas}")
        print(f"   • Auditorías: {total_auditorias}")
        print(f"\n🎯 Ahora el algoritmo de escalamiento tiene métricas para calcular:")
        print(f"   • Variable actividad (% respuesta)")
        print(f"   • Variable desempeño (% éxito)")
        print(f"   • Variable confianza (puntaje)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution"""
    try:
        generate_historical_data()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
