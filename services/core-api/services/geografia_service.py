"""
Geographic data import service for TeLOO V3
Handles Excel import for metropolitan areas and logistics hubs
"""

import pandas as pd
from typing import List, Dict, Tuple
from fastapi import UploadFile, HTTPException
import io
from models.geografia import AreaMetropolitana, HubLogistico
from tortoise.transactions import in_transaction


class GeografiaService:
    """
    Service for importing and managing geographic data
    """
    
    @staticmethod
    async def importar_areas_metropolitanas_excel(file: UploadFile) -> Dict:
        """
        Importa áreas metropolitanas desde archivo Excel
        Procesa Areas_Metropolitanas_TeLOO.xlsx
        
        Expected columns:
        - area_metropolitana: Nombre del área metropolitana
        - ciudad_nucleo: Ciudad núcleo del área
        - municipio_norm: Municipio normalizado
        """
        
        # Validar archivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Archivo debe ser formato Excel (.xlsx o .xls)"
            )
            
        try:
            # Leer archivo Excel
            contents = await file.read()
            df = pd.read_excel(io.BytesIO(contents))
            
            # Validar columnas requeridas
            required_columns = ['area_metropolitana', 'ciudad_nucleo', 'municipio_norm']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Columnas faltantes: {', '.join(missing_columns)}"
                )
            
            # Limpiar y validar datos
            df = df.dropna(subset=required_columns)
            df['area_metropolitana'] = df['area_metropolitana'].str.strip()
            df['ciudad_nucleo'] = df['ciudad_nucleo'].str.strip()
            df['municipio_norm'] = df['municipio_norm'].str.strip().str.upper()
            
            # Validar datos duplicados
            duplicados = df.duplicated(subset=['area_metropolitana', 'municipio_norm'])
            if duplicados.any():
                filas_duplicadas = df[duplicados].index.tolist()
                raise HTTPException(
                    status_code=400,
                    detail=f"Datos duplicados encontrados en filas: {filas_duplicadas}"
                )
            
            # Importar datos en transacción
            async with in_transaction() as conn:
                # Limpiar datos existentes
                await AreaMetropolitana.all().using_db(conn).delete()
                
                # Insertar nuevos datos
                areas_creadas = []
                for _, row in df.iterrows():
                    area = await AreaMetropolitana.create(
                        area_metropolitana=row['area_metropolitana'],
                        ciudad_nucleo=row['ciudad_nucleo'],
                        municipio_norm=row['municipio_norm'],
                        departamento=row.get('departamento'),
                        poblacion=row.get('poblacion'),
                        using_db=conn
                    )
                    areas_creadas.append(area)
            
            return {
                "success": True,
                "message": f"Importadas {len(areas_creadas)} áreas metropolitanas",
                "total_registros": len(areas_creadas),
                "areas_metropolitanas": len(df['area_metropolitana'].unique()),
                "municipios": len(df['municipio_norm'].unique())
            }
            
        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=400,
                detail="Archivo Excel está vacío"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error procesando archivo: {str(e)}"
            )
    
    @staticmethod
    async def importar_hubs_logisticos_excel(file: UploadFile) -> Dict:
        """
        Importa hubs logísticos desde archivo Excel
        Procesa Asignacion_Hubs_200km.xlsx
        
        Expected columns:
        - municipio_norm: Municipio normalizado
        - hub_asignado_norm: Hub logístico asignado normalizado
        """
        
        # Validar archivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Archivo debe ser formato Excel (.xlsx o .xls)"
            )
            
        try:
            # Leer archivo Excel
            contents = await file.read()
            df = pd.read_excel(io.BytesIO(contents))
            
            # Validar columnas requeridas
            required_columns = ['municipio_norm', 'hub_asignado_norm']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Columnas faltantes: {', '.join(missing_columns)}"
                )
            
            # Limpiar y validar datos
            df = df.dropna(subset=required_columns)
            df['municipio_norm'] = df['municipio_norm'].str.strip().str.upper()
            df['hub_asignado_norm'] = df['hub_asignado_norm'].str.strip().str.upper()
            
            # Validar datos duplicados
            duplicados = df.duplicated(subset=['municipio_norm', 'hub_asignado_norm'])
            if duplicados.any():
                filas_duplicadas = df[duplicados].index.tolist()
                raise HTTPException(
                    status_code=400,
                    detail=f"Datos duplicados encontrados en filas: {filas_duplicadas}"
                )
            
            # Validar integridad: verificar que los hubs existan como municipios
            hubs_unicos = df['hub_asignado_norm'].unique()
            municipios_existentes = df['municipio_norm'].unique()
            
            hubs_inexistentes = []
            for hub in hubs_unicos:
                if hub not in municipios_existentes:
                    # Verificar si existe en áreas metropolitanas
                    area_exists = await AreaMetropolitana.filter(municipio_norm=hub).exists()
                    if not area_exists:
                        hubs_inexistentes.append(hub)
            
            if hubs_inexistentes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Hubs inexistentes como municipios: {', '.join(hubs_inexistentes)}"
                )
            
            # Importar datos en transacción
            async with in_transaction() as conn:
                # Limpiar datos existentes
                await HubLogistico.all().using_db(conn).delete()
                
                # Insertar nuevos datos
                hubs_creados = []
                for _, row in df.iterrows():
                    hub = await HubLogistico.create(
                        municipio_norm=row['municipio_norm'],
                        hub_asignado_norm=row['hub_asignado_norm'],
                        distancia_km=row.get('distancia_km'),
                        tiempo_estimado_horas=row.get('tiempo_estimado_horas'),
                        using_db=conn
                    )
                    hubs_creados.append(hub)
            
            return {
                "success": True,
                "message": f"Importados {len(hubs_creados)} registros de hubs logísticos",
                "total_registros": len(hubs_creados),
                "municipios": len(df['municipio_norm'].unique()),
                "hubs_unicos": len(df['hub_asignado_norm'].unique())
            }
            
        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=400,
                detail="Archivo Excel está vacío"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error procesando archivo: {str(e)}"
            )
    
    @staticmethod
    async def validar_integridad_geografica() -> Dict:
        """
        Valida la integridad de los datos geográficos
        Verifica consistencia entre áreas metropolitanas y hubs
        """
        
        # Obtener todos los municipios de áreas metropolitanas
        municipios_am = await AreaMetropolitana.all().values_list('municipio_norm', flat=True)
        municipios_am_set = set(municipios_am)
        
        # Obtener todos los municipios de hubs
        municipios_hub = await HubLogistico.all().values_list('municipio_norm', flat=True)
        municipios_hub_set = set(municipios_hub)
        
        # Obtener todos los hubs asignados
        hubs_asignados = await HubLogistico.all().values_list('hub_asignado_norm', flat=True)
        hubs_asignados_set = set(hubs_asignados)
        
        # Análisis de integridad
        municipios_solo_am = municipios_am_set - municipios_hub_set
        municipios_solo_hub = municipios_hub_set - municipios_am_set
        municipios_comunes = municipios_am_set & municipios_hub_set
        
        # Verificar hubs que no existen como municipios
        hubs_sin_municipio = hubs_asignados_set - municipios_am_set - municipios_hub_set
        
        return {
            "total_municipios_am": len(municipios_am_set),
            "total_municipios_hub": len(municipios_hub_set),
            "municipios_comunes": len(municipios_comunes),
            "municipios_solo_am": len(municipios_solo_am),
            "municipios_solo_hub": len(municipios_solo_hub),
            "hubs_unicos": len(hubs_asignados_set),
            "hubs_sin_municipio": list(hubs_sin_municipio),
            "integridad_ok": len(hubs_sin_municipio) == 0,
            "cobertura_geografica": {
                "areas_metropolitanas": len(set(await AreaMetropolitana.all().values_list('area_metropolitana', flat=True))),
                "hubs_logisticos": len(hubs_asignados_set)
            }
        }
    
    @staticmethod
    async def get_estadisticas_geograficas() -> Dict:
        """
        Obtiene estadísticas generales de los datos geográficos
        """
        
        # Estadísticas de áreas metropolitanas
        total_areas = await AreaMetropolitana.all().count()
        areas_unicas = len(set(await AreaMetropolitana.all().values_list('area_metropolitana', flat=True)))
        municipios_am = len(set(await AreaMetropolitana.all().values_list('municipio_norm', flat=True)))
        
        # Estadísticas de hubs logísticos
        total_hubs_registros = await HubLogistico.all().count()
        municipios_hub = len(set(await HubLogistico.all().values_list('municipio_norm', flat=True)))
        hubs_unicos = len(set(await HubLogistico.all().values_list('hub_asignado_norm', flat=True)))
        
        return {
            "areas_metropolitanas": {
                "total_registros": total_areas,
                "areas_unicas": areas_unicas,
                "municipios_cubiertos": municipios_am
            },
            "hubs_logisticos": {
                "total_registros": total_hubs_registros,
                "municipios_cubiertos": municipios_hub,
                "hubs_unicos": hubs_unicos
            },
            "cobertura_total": {
                "municipios_con_am": municipios_am,
                "municipios_con_hub": municipios_hub,
                "total_municipios_sistema": len(set(
                    await AreaMetropolitana.all().values_list('municipio_norm', flat=True) +
                    await HubLogistico.all().values_list('municipio_norm', flat=True)
                ))
            }
        }