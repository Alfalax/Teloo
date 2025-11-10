#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la codificación UTF-8 en metadata_json
"""

import asyncio
import asyncpg
import json
from datetime import datetime

# Metadatos correctos con tildes
METADATA_CORRECTIONS = {
    'ofertas_minimas_deseadas': {
        'min': 1,
        'max': 10,
        'default': 2,
        'unit': 'ofertas',
        'description': 'Número mínimo de ofertas antes de cierre anticipado'
    },
    'timeout_evaluacion_segundos': {
        'min': 1,
        'max': 30,
        'default': 5,
        'unit': 'segundos',
        'description': 'Tiempo máximo para completar evaluación'
    },
    'vigencia_auditoria_dias': {
        'min': 1,
        'max': 365,
        'default': 30,
        'unit': 'días',
        'description': 'Días de vigencia de auditorías de confianza'
    },
    'periodo_actividad_reciente_dias': {
        'min': 1,
        'max': 90,
        'default': 30,
        'unit': 'días',
        'description': 'Días para calcular actividad reciente'
    },
    'periodo_desempeno_historico_meses': {
        'min': 1,
        'max': 24,
        'default': 6,
        'unit': 'meses',
        'description': 'Meses para calcular desempeño histórico'
    },
    'confianza_minima_operar': {
        'min': 1.0,
        'max': 5.0,
        'default': 2.0,
        'unit': 'puntos',
        'description': 'Nivel mínimo de confianza requerido'
    },
    'cobertura_minima_porcentaje': {
        'min': 0,
        'max': 100,
        'default': 50,
        'unit': '%',
        'description': 'Porcentaje mínimo de cobertura de repuestos'
    },
    'timeout_ofertas_horas': {
        'min': 1,
        'max': 168,
        'default': 20,
        'unit': 'horas',
        'description': 'Horas antes de marcar ofertas como expiradas'
    },
    'notificacion_expiracion_horas_antes': {
        'min': 1,
        'max': 12,
        'default': 2,
        'unit': 'horas',
        'description': 'Horas antes de expiración para notificar'
    },
    'pesos_escalamiento': {
        'description': 'Pesos del algoritmo de escalamiento de asesores'
    },
    'umbrales_niveles': {
        'description': 'Umbrales para clasificación por niveles'
    },
    'tiempos_espera_minutos': {
        'description': 'Tiempos de espera por nivel antes de escalar'
    },
    'canales_notificacion': {
        'description': 'Canales de notificación por nivel'
    },
    'pesos_evaluacion': {
        'description': 'Pesos para evaluación de ofertas'
    }
}

async def fix_encoding():
    """Corrige la codificación de los metadatos"""
    print("\n" + "="*80)
    print("🔧 CORRECCIÓN DE CODIFICACIÓN UTF-8 EN METADATA")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Conectar a la base de datos
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='teloo_user',
        password='teloo_password',
        database='teloo_v3'
    )
    
    try:
        updated_count = 0
        
        for clave, metadata in METADATA_CORRECTIONS.items():
            # Convertir a JSON string
            metadata_json = json.dumps(metadata, ensure_ascii=False)
            
            # Actualizar en la base de datos
            result = await conn.execute(
                """
                UPDATE parametros_config 
                SET metadata_json = $1::jsonb
                WHERE clave = $2
                """,
                metadata_json,
                clave
            )
            
            if result == 'UPDATE 1':
                updated_count += 1
                print(f"✅ {clave}: Actualizado")
            else:
                print(f"⚠️  {clave}: No encontrado")
        
        print(f"\n📊 Total actualizado: {updated_count}/{len(METADATA_CORRECTIONS)}")
        
        # Verificar resultados
        print("\n" + "="*80)
        print("📋 VERIFICACIÓN DE RESULTADOS")
        print("="*80 + "\n")
        
        rows = await conn.fetch(
            """
            SELECT clave, metadata_json->>'description' as descripcion
            FROM parametros_config
            WHERE metadata_json ? 'description'
            ORDER BY clave
            """
        )
        
        for row in rows:
            print(f"{row['clave']:<35} {row['descripcion']}")
        
        print("\n✅ Corrección completada exitosamente")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_encoding())
