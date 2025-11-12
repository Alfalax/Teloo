"""
Script para generar datos históricos simulados para asesores
Esto permite que el algoritmo de escalamiento tenga métricas reales
"""

import asyncio
import sys
import os
from pathlib import Path
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'services' / 'core-api'))

from tortoise import Tortoise


async def init_db():
    """Initialize database connection"""
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_db",
        modules={"models": ["models.user", "models.geografia", "models.solicitud", "models.oferta", "models.analytics"]}
    )


async def generate_historical_data():
    """Generate historical data for asesores"""
    from models.user import Asesor
    from models.analytics import HistorialRespuestaOferta, OfertaHistorica, AuditoriaTienda
    
    print("🚀 Generando datos históricos para asesores...")
    
    # Get all asesores
    asesores = await Asesor.all()
    print(f"   📊 Encontrados {len(asesores)} asesores")
    
    if not asesores:
        print("   ⚠️  No hay asesores en la base de datos. Ejecuta generate_fake_asesores.py primero.")
        return
    
    total_historial = 0
    total_ofertas = 0
    total_auditorias = 0
    
    for i, asesor in enumerate(asesores, 1):
        try:
            # Generar historial de respuestas (últimos 30 días)
            num_respuestas = random.randint(5, 20)
            for _ in range(num_respuestas):
                fecha_envio = datetime.now() - timedelta(days=random.randint(1, 30))
                respondio = random.random() > 0.3  # 70% responde
                
                await HistorialRespuestaOferta.create(
                    asesor_id=str(asesor.id),
                    fecha_envio=fecha_envio,
                    respondio=respondio,
                    tiempo_respuesta_seg=random.randint(300, 7200) if respondio else None
                )
                total_historial += 1
            
            # Generar ofertas históricas (últimos 6 meses)
            num_ofertas = random.randint(10, 50)
            for _ in range(num_ofertas):
                fecha = (datetime.now() - timedelta(days=random.randint(1, 180))).date()
                adjudicada = random.random() > 0.7  # 30% gana
                aceptada = adjudicada and random.random() > 0.2  # 80% de ganadoras son aceptadas
                exitosa = aceptada and random.random() > 0.1  # 90% de aceptadas son exitosas
                
                await OfertaHistorica.create(
                    asesor_id=str(asesor.id),
                    fecha=fecha,
                    monto=Decimal(str(random.randint(100000, 5000000))),
                    adjudicada=adjudicada,
                    aceptada_cliente=aceptada,
                    entrega_exitosa=exitosa,
                    tiempo_respuesta_seg=random.randint(300, 7200)
                )
                total_ofertas += 1
            
            # Generar auditoría de confianza (50% de asesores tienen auditoría reciente)
            if random.random() > 0.5:
                fecha_revision = datetime.now() - timedelta(days=random.randint(1, 25))
                puntaje = Decimal(str(round(random.uniform(2.5, 5.0), 2)))
                
                await AuditoriaTienda.create(
                    asesor_id=str(asesor.id),
                    fecha_revision=fecha_revision,
                    puntaje_confianza=puntaje,
                    vigencia_dias=30,
                    observaciones=f"Auditoría automática - Puntaje: {puntaje}"
                )
                total_auditorias += 1
            
            if i % 50 == 0:
                print(f"   ✓ Procesados {i}/{len(asesores)} asesores...")
                
        except Exception as e:
            print(f"   ✗ Error procesando asesor {asesor.id}: {e}")
    
    print(f"\n✅ Datos históricos generados:")
    print(f"   • Historial respuestas: {total_historial}")
    print(f"   • Ofertas históricas: {total_ofertas}")
    print(f"   • Auditorías: {total_auditorias}")


async def main():
    """Main execution"""
    try:
        await init_db()
        await generate_historical_data()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
