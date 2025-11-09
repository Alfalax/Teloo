#!/usr/bin/env python3
"""
Script para verificar puntos de venta en la base de datos
"""
import asyncio
import sys
import os

# Agregar el directorio services/core-api al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'core-api'))

from tortoise import Tortoise
from models.user import Asesor

async def check_puntos_venta():
    # Inicializar conexión
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_v3",
        modules={"models": ["services.core-api.models"]}
    )
    
    print("="*60)
    print("VERIFICACIÓN DE PUNTOS DE VENTA")
    print("="*60)
    
    # Total de asesores
    total_asesores = await Asesor.all().count()
    print(f"\n📊 Total Asesores: {total_asesores}")
    
    # Asesores activos
    asesores_activos = await Asesor.filter(estado='ACTIVO').count()
    print(f"✅ Asesores Activos: {asesores_activos}")
    
    # Obtener todos los asesores con sus puntos de venta
    asesores = await Asesor.all().prefetch_related('usuario')
    
    # Puntos de venta únicos
    puntos_venta = set()
    ciudades = set()
    departamentos = set()
    
    print(f"\n📍 LISTADO DE PUNTOS DE VENTA:")
    print("-"*60)
    
    for i, asesor in enumerate(asesores, 1):
        puntos_venta.add(asesor.punto_venta)
        ciudades.add(asesor.ciudad)
        departamentos.add(asesor.departamento)
        
        print(f"{i}. {asesor.punto_venta}")
        print(f"   Asesor: {asesor.usuario.nombre} {asesor.usuario.apellido}")
        print(f"   Ciudad: {asesor.ciudad}, {asesor.departamento}")
        print(f"   Estado: {asesor.estado}")
        print(f"   Email: {asesor.usuario.email}")
        print()
    
    print("="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Total Puntos de Venta: {len(puntos_venta)}")
    print(f"Total Ciudades: {len(ciudades)}")
    print(f"Total Departamentos: {len(departamentos)}")
    
    print(f"\n🏙️ Ciudades con cobertura:")
    for ciudad in sorted(ciudades):
        count = len([a for a in asesores if a.ciudad == ciudad])
        print(f"   - {ciudad}: {count} punto(s) de venta")
    
    print(f"\n📍 Departamentos con cobertura:")
    for dept in sorted(departamentos):
        count = len([a for a in asesores if a.departamento == dept])
        print(f"   - {dept}: {count} punto(s) de venta")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_puntos_venta())
