"""
Script para importar datos DIVIPOLA desde Excel
Importa todos los municipios de Colombia con su información geográfica
"""

import asyncio
import pandas as pd
from pathlib import Path
import sys

# Agregar el directorio padre al path para importar modelos
sys.path.append(str(Path(__file__).parent.parent))

from tortoise import Tortoise
from models.geografia import Municipio


async def import_divipola_from_excel(excel_path: str):
    """
    Importa datos DIVIPOLA desde archivo Excel
    
    Args:
        excel_path: Ruta al archivo DIVIPOLA_Municipios.xlsx
    """
    
    print(f"📂 Leyendo archivo: {excel_path}")
    
    # Leer Excel
    df = pd.read_excel(excel_path)
    
    print(f"✅ Archivo leído: {len(df)} registros encontrados")
    
    # Mapear nombres de columnas del Excel a nombres esperados
    column_mapping = {
        'Municipio': 'municipio',
        'Nombre Departamento': 'departamento',
        'Hub Logistico que pertenece': 'hub_logistico',
        'pertenece Area metropolitana': 'area_metropolitana',
        ' Codigo': 'codigo_dane'
    }
    
    # Renombrar columnas
    df = df.rename(columns=column_mapping)
    
    # Validar columnas requeridas
    required_columns = ['municipio', 'departamento', 'hub_logistico']
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        print(f"❌ Error: Columnas faltantes: {', '.join(missing)}")
        print(f"   Columnas disponibles: {', '.join(df.columns)}")
        return False
    
    # Limpiar y preparar datos
    print("🔄 Limpiando y normalizando datos...")
    
    df = df.dropna(subset=required_columns)
    df['municipio'] = df['municipio'].str.strip()
    df['municipio_norm'] = df['municipio'].str.strip().str.upper()
    df['departamento'] = df['departamento'].str.strip()
    df['hub_logistico'] = df['hub_logistico'].str.strip().str.upper()
    
    # Normalizar área metropolitana
    if 'area_metropolitana' in df.columns:
        df['area_metropolitana'] = df['area_metropolitana'].str.strip()
        df.loc[df['area_metropolitana'].isna(), 'area_metropolitana'] = None
    else:
        df['area_metropolitana'] = None
    
    # Normalizar código DANE
    if 'codigo_dane' in df.columns:
        df['codigo_dane'] = df['codigo_dane'].astype(str).str.strip()
        # Limpiar valores nan
        df.loc[df['codigo_dane'] == 'nan', 'codigo_dane'] = None
    else:
        df['codigo_dane'] = None
    
    # Validar duplicados por código DANE (no por nombre)
    if 'codigo_dane' in df.columns and df['codigo_dane'].notna().any():
        duplicados = df.duplicated(subset=['codigo_dane'], keep=False)
        if duplicados.any():
            print(f"⚠️  Advertencia: {duplicados.sum()} registros con código DANE duplicado")
            print(f"   Códigos duplicados: {df[duplicados]['codigo_dane'].unique().tolist()[:5]}")
            df = df.drop_duplicates(subset=['codigo_dane'], keep='first')
            print(f"   Manteniendo primera ocurrencia, total: {len(df)} registros")
    
    # Informar sobre municipios con mismo nombre en diferentes departamentos
    nombres_duplicados = df.duplicated(subset=['municipio_norm'], keep=False)
    if nombres_duplicados.any():
        print(f"ℹ️  Info: {nombres_duplicados.sum()} municipios con nombres repetidos en diferentes departamentos")
        print(f"   Ejemplos: {df[nombres_duplicados][['municipio', 'departamento']].head(5).to_dict('records')}")
    
    # Conectar a base de datos
    print("🔌 Conectando a base de datos...")
    
    # Detectar si estamos en Docker o desarrollo local
    import os
    db_host = os.getenv("DB_HOST", "localhost")
    if Path("/app").exists():  # Estamos en Docker
        db_host = "postgres"
    
    db_url = f"postgres://teloo_user:teloo_password@{db_host}:5432/teloo_v3"
    
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["models"]}
    )
    
    await Tortoise.generate_schemas()
    
    # Limpiar tabla existente
    print("🗑️  Limpiando datos existentes...")
    await Municipio.all().delete()
    
    # Insertar nuevos datos
    print(f"💾 Insertando {len(df)} municipios...")
    
    municipios_creados = 0
    errores = 0
    
    for idx, row in df.iterrows():
        try:
            await Municipio.create(
                codigo_dane=row.get('codigo_dane'),
                municipio=row['municipio'],
                municipio_norm=row['municipio_norm'],
                departamento=row['departamento'],
                area_metropolitana=row.get('area_metropolitana'),
                hub_logistico=row['hub_logistico']
            )
            municipios_creados += 1
            
            if (municipios_creados % 100) == 0:
                print(f"   Progreso: {municipios_creados}/{len(df)} municipios...")
                
        except Exception as e:
            errores += 1
            print(f"   ❌ Error en fila {idx}: {str(e)}")
    
    # Estadísticas finales
    print("\n" + "="*60)
    print("📊 RESUMEN DE IMPORTACIÓN")
    print("="*60)
    print(f"✅ Municipios importados: {municipios_creados}")
    print(f"❌ Errores: {errores}")
    print(f"📍 Departamentos únicos: {df['departamento'].nunique()}")
    print(f"🏙️  Áreas metropolitanas: {df['area_metropolitana'].dropna().nunique()}")
    print(f"📦 Hubs logísticos: {df['hub_logistico'].nunique()}")
    print(f"🌆 Municipios con área metropolitana: {df['area_metropolitana'].notna().sum()}")
    print("="*60)
    
    # Mostrar distribución por hub
    print("\n📦 DISTRIBUCIÓN POR HUB LOGÍSTICO:")
    print("-"*60)
    for hub, count in df['hub_logistico'].value_counts().items():
        print(f"   {hub}: {count} municipios")
    
    # Mostrar áreas metropolitanas
    if df['area_metropolitana'].notna().any():
        print("\n🏙️  ÁREAS METROPOLITANAS:")
        print("-"*60)
        for area, count in df['area_metropolitana'].value_counts().items():
            print(f"   {area}: {count} municipios")
    
    # Cerrar conexión
    await Tortoise.close_connections()
    
    return municipios_creados > 0


async def main():
    """
    Función principal
    """
    
    print("\n" + "="*60)
    print("🇨🇴 IMPORTADOR DE DATOS DIVIPOLA - TeLOO V3")
    print("="*60 + "\n")
    
    # Buscar archivo Excel (primero en /app dentro del contenedor, luego en raíz del proyecto)
    excel_paths = [
        Path("/app/DIVIPOLA_Municipios.xlsx"),  # Dentro del contenedor Docker
        Path(__file__).parent.parent.parent.parent / "DIVIPOLA_Municipios.xlsx"  # Desarrollo local
    ]
    
    excel_path = None
    for path in excel_paths:
        if path.exists():
            excel_path = path
            break
    
    if not excel_path:
        print(f"❌ Error: Archivo no encontrado")
        print(f"   Rutas buscadas:")
        for path in excel_paths:
            print(f"   - {path}")
        print(f"   Por favor coloca el archivo DIVIPOLA_Municipios.xlsx en una de estas ubicaciones")
        return
    
    # Importar datos
    success = await import_divipola_from_excel(str(excel_path))
    
    if success:
        print("\n✅ Importación completada exitosamente!")
    else:
        print("\n❌ Importación fallida")


if __name__ == "__main__":
    asyncio.run(main())
