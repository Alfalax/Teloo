"""
Geographic data import service for TeLOO V3
Handles Excel import for DIVIPOLA municipalities data
"""

import pandas as pd
from typing import Dict
from fastapi import UploadFile, HTTPException
import io
from models.geografia import Municipio
from tortoise.transactions import in_transaction


class GeografiaService:
    """
    Service for importing and managing geographic data from unified municipios table
    """
    
    @staticmethod
    async def importar_divipola_excel(file: UploadFile) -> Dict:
        """
        Importa municipios desde archivo Excel DIVIPOLA_Municipios.xlsx
        
        Expected columns:
        - codigo_dane: Código DANE del municipio (opcional)
        - municipio: Nombre del municipio
        - departamento: Departamento
        - area_metropolitana: Área metropolitana (opcional, NULL si no aplica)
        - hub_logistico: Hub logístico asignado
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
            required_columns = ['municipio', 'departamento', 'hub_logistico']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Columnas faltantes: {', '.join(missing_columns)}"
                )
            
            # Limpiar y validar datos
            df = df.dropna(subset=required_columns)
            df['municipio'] = df['municipio'].str.strip()
            df['municipio_norm'] = df['municipio'].str.strip().str.upper()
            df['departamento'] = df['departamento'].str.strip()
            df['hub_logistico'] = df['hub_logistico'].str.strip().str.upper()
            
            # Normalizar área metropolitana (puede ser NULL)
            if 'area_metropolitana' in df.columns:
                df['area_metropolitana'] = df['area_metropolitana'].str.strip()
                df.loc[df['area_metropolitana'].isna(), 'area_metropolitana'] = None
            else:
                df['area_metropolitana'] = None
            
            # Normalizar código DANE
            if 'codigo_dane' in df.columns:
                df['codigo_dane'] = df['codigo_dane'].astype(str).str.strip()
            else:
                df['codigo_dane'] = None
            
            # Validar datos duplicados por municipio_norm
            duplicados = df.duplicated(subset=['municipio_norm'])
            if duplicados.any():
                filas_duplicadas = df[duplicados]['municipio'].tolist()
                raise HTTPException(
                    status_code=400,
                    detail=f"Municipios duplicados encontrados: {', '.join(filas_duplicadas[:5])}"
                )
            
            # Importar datos en transacción
            async with in_transaction() as conn:
                # Limpiar datos existentes
                await Municipio.all().using_db(conn).delete()
                
                # Insertar nuevos datos
                municipios_creados = []
                for _, row in df.iterrows():
                    municipio = await Municipio.create(
                        codigo_dane=row.get('codigo_dane'),
                        municipio=row['municipio'],
                        municipio_norm=row['municipio_norm'],
                        departamento=row['departamento'],
                        area_metropolitana=row.get('area_metropolitana'),
                        hub_logistico=row['hub_logistico'],
                        using_db=conn
                    )
                    municipios_creados.append(municipio)
            
            # Estadísticas de importación
            total_municipios = len(municipios_creados)
            total_departamentos = df['departamento'].nunique()
            total_areas_metro = df['area_metropolitana'].dropna().nunique()
            total_hubs = df['hub_logistico'].nunique()
            municipios_con_am = df['area_metropolitana'].notna().sum()
            
            return {
                "success": True,
                "message": f"Importados {total_municipios} municipios exitosamente",
                "estadisticas": {
                    "total_municipios": total_municipios,
                    "total_departamentos": total_departamentos,
                    "total_areas_metropolitanas": total_areas_metro,
                    "total_hubs_logisticos": total_hubs,
                    "municipios_con_area_metropolitana": int(municipios_con_am),
                    "municipios_sin_area_metropolitana": total_municipios - int(municipios_con_am)
                }
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
        Verifica consistencia de hubs y áreas metropolitanas
        """
        
        # Obtener todos los municipios
        municipios = await Municipio.all()
        
        if not municipios:
            return {
                "integridad_ok": False,
                "mensaje": "No hay datos geográficos en el sistema",
                "total_municipios": 0
            }
        
        # Análisis de integridad
        total_municipios = len(municipios)
        municipios_con_am = sum(1 for m in municipios if m.area_metropolitana)
        municipios_sin_am = total_municipios - municipios_con_am
        
        # Obtener hubs únicos
        hubs_unicos = set(m.hub_logistico for m in municipios)
        
        # Obtener áreas metropolitanas únicas
        areas_metro_unicas = set(m.area_metropolitana for m in municipios if m.area_metropolitana)
        
        # Verificar que cada hub tenga al menos un municipio
        hubs_con_municipios = {}
        for hub in hubs_unicos:
            count = sum(1 for m in municipios if m.hub_logistico == hub)
            hubs_con_municipios[hub] = count
        
        # Verificar que cada área metropolitana tenga al menos 2 municipios
        areas_con_municipios = {}
        for area in areas_metro_unicas:
            count = sum(1 for m in municipios if m.area_metropolitana == area)
            areas_con_municipios[area] = count
        
        areas_con_un_solo_municipio = [
            area for area, count in areas_con_municipios.items() if count == 1
        ]
        
        return {
            "integridad_ok": len(areas_con_un_solo_municipio) == 0,
            "total_municipios": total_municipios,
            "municipios_con_area_metropolitana": municipios_con_am,
            "municipios_sin_area_metropolitana": municipios_sin_am,
            "total_hubs": len(hubs_unicos),
            "total_areas_metropolitanas": len(areas_metro_unicas),
            "hubs_con_municipios": hubs_con_municipios,
            "areas_con_un_solo_municipio": areas_con_un_solo_municipio,
            "advertencias": [
                f"Área metropolitana '{area}' tiene solo 1 municipio"
                for area in areas_con_un_solo_municipio
            ] if areas_con_un_solo_municipio else []
        }
    
    @staticmethod
    async def validar_ciudad(ciudad: str, departamento: str = None) -> bool:
        """
        Valida si una ciudad existe en la base de datos geográfica
        
        Args:
            ciudad: Nombre de la ciudad a validar
            departamento: Departamento opcional para validación más específica
            
        Returns:
            bool: True si la ciudad existe, False en caso contrario
        """
        if not ciudad:
            return False
            
        # Normalizar ciudad para búsqueda
        ciudad_norm = Municipio.normalizar_ciudad(ciudad)
        
        # Buscar municipio
        query = Municipio.filter(municipio_norm=ciudad_norm)
        if departamento:
            query = query.filter(departamento__icontains=departamento)
        
        return await query.exists()
    
    @staticmethod
    async def get_estadisticas_geograficas() -> Dict:
        """
        Obtiene estadísticas generales de los datos geográficos
        """
        
        # Contar totales
        total_municipios = await Municipio.all().count()
        
        if total_municipios == 0:
            return {
                "total_municipios": 0,
                "mensaje": "No hay datos geográficos en el sistema"
            }
        
        # Obtener datos únicos
        municipios = await Municipio.all()
        
        departamentos = set(m.departamento for m in municipios)
        areas_metro = set(m.area_metropolitana for m in municipios if m.area_metropolitana)
        hubs = set(m.hub_logistico for m in municipios)
        
        municipios_con_am = sum(1 for m in municipios if m.area_metropolitana)
        
        # Distribución por hub
        distribucion_hubs = {}
        for hub in hubs:
            count = sum(1 for m in municipios if m.hub_logistico == hub)
            distribucion_hubs[hub] = count
        
        # Distribución por departamento (top 10)
        distribucion_deptos = {}
        for depto in departamentos:
            count = sum(1 for m in municipios if m.departamento == depto)
            distribucion_deptos[depto] = count
        
        top_10_deptos = dict(sorted(
            distribucion_deptos.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return {
            "total_municipios": total_municipios,
            "total_departamentos": len(departamentos),
            "total_areas_metropolitanas": len(areas_metro),
            "total_hubs_logisticos": len(hubs),
            "municipios_con_area_metropolitana": municipios_con_am,
            "municipios_sin_area_metropolitana": total_municipios - municipios_con_am,
            "porcentaje_con_area_metropolitana": round((municipios_con_am / total_municipios) * 100, 2),
            "distribucion_por_hub": distribucion_hubs,
            "top_10_departamentos": top_10_deptos
        }
    
    @staticmethod
    async def buscar_municipios(
        query: str = None,
        departamento: str = None,
        hub: str = None,
        area_metropolitana: str = None,
        limit: int = 50
    ) -> list:
        """
        Busca municipios con filtros opcionales
        
        Args:
            query: Texto a buscar en nombre de municipio
            departamento: Filtrar por departamento
            hub: Filtrar por hub logístico
            area_metropolitana: Filtrar por área metropolitana
            limit: Límite de resultados
            
        Returns:
            Lista de municipios que coinciden con los filtros
        """
        
        filters = Municipio.all()
        
        if query:
            query_norm = Municipio.normalizar_ciudad(query)
            filters = filters.filter(municipio_norm__icontains=query_norm)
        
        if departamento:
            filters = filters.filter(departamento__icontains=departamento)
        
        if hub:
            hub_norm = hub.strip().upper()
            filters = filters.filter(hub_logistico=hub_norm)
        
        if area_metropolitana:
            filters = filters.filter(area_metropolitana__icontains=area_metropolitana)
        
        municipios = await filters.limit(limit)
        
        return [
            {
                "id": str(m.id),
                "codigo_dane": m.codigo_dane,
                "municipio": m.municipio,
                "departamento": m.departamento,
                "area_metropolitana": m.area_metropolitana,
                "hub_logistico": m.hub_logistico
            }
            for m in municipios
        ]
