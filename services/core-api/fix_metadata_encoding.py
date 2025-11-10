#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir la codificación UTF-8 en metadata_json
Ejecutar desde el contenedor core-api
"""

import asyncio
from tortoise import Tortoise
from models.analytics import ParametroConfig
import json

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
    print("="*80 + "\n")
    
    # Inicializar Tortoise ORM
    await Tortoise.init(
        db_url='postgres://teloo_user:teloo_password@postgres:5432/teloo_v3',
        modules={'models': ['models']}
    )
    
    try:
        updated_count = 0
        
        for clave, metadata in METADATA_CORRECTIONS.items():
            param = await ParametroConfig.get_or_none(clave=clave)
            
            if param:
                param.metadata_json = metadata
                await param.save()
                updated_count += 1
                print(f"✅ {clave}: Actualizado")
            else:
                print(f"⚠️  {clave}: No encontrado")
        
        print(f"\n📊 Total actualizado: {updated_count}/{len(METADATA_CORRECTIONS)}")
        
        # Verificar resultados
        print("\n" + "="*80)
        print("📋 VERIFICACIÓN DE RESULTADOS")
        print("="*80 + "\n")
        
        params = await ParametroConfig.filter(metadata_json__contains={'description': ''}).all()
        
        for param in params:
            if param.metadata_json and 'description' in param.metadata_json:
                print(f"{param.clave:<35} {param.metadata_json['description']}")
        
        print("\n✅ Corrección completada exitosamente")
        
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(fix_encoding())
