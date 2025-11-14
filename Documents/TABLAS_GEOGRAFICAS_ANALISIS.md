# Análisis de Tablas Geográficas - TeLOO V3

## 1. Tabla: AREAS_METROPOLITANAS

### Estructura

```sql
CREATE TABLE areas_metropolitanas (
    id                 UUID PRIMARY KEY,
    created_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    area_metropolitana VARCHAR(100) NOT NULL,
    ciudad_nucleo      VARCHAR(100) NOT NULL,
    municipio_norm     VARCHAR(100) NOT NULL,
    departamento       VARCHAR(100),
    poblacion          INTEGER,
    
    CONSTRAINT uid_areas_metro_area_me_3dfd2f 
        UNIQUE (area_metropolitana, municipio_norm)
);
```

### Propósito

Esta tabla almacena las **áreas metropolitanas de Colombia** y sus municipios asociados. Se utiliza para el **algoritmo de escalamiento** para determinar la proximidad geográfica entre asesores y solicitudes.

### Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `created_at` | TIMESTAMP | Fecha de creación |
| `updated_at` | TIMESTAMP | Fecha de actualización |
| `area_metropolitana` | VARCHAR(100) | Nombre del área metropolitana |
| `ciudad_nucleo` | VARCHAR(100) | Ciudad principal del área metropolitana |
| `municipio_norm` | VARCHAR(100) | Municipio normalizado (UPPERCASE, sin tildes) |
| `departamento` | VARCHAR(100) | Departamento (opcional) |
| `poblacion` | INTEGER | Población del municipio (opcional) |

### Datos Actuales (4 registros)

| Área Metropolitana | Ciudad Núcleo | Municipio Norm |
|-------------------|---------------|----------------|
| Área Metropolitana de Bogotá | Bogotá | BOGOTA |
| Área Metropolitana del Valle de Aburrá | Medellín | MEDELLIN |
| Área Metropolitana de Cali | Cali | CALI |
| Área Metropolitana de Barranquilla | Barranquilla | BARRANQUILLA |

### Uso en el Sistema

**Algoritmo de Escalamiento - Criterio de Proximidad:**

1. **Nivel 1 (Proximidad 5.0)**: Misma ciudad
2. **Nivel 2 (Proximidad 4.0)**: Misma área metropolitana
3. **Nivel 3 (Proximidad 3.5)**: Mismo hub logístico
4. **Nivel 4 (Proximidad 3.0)**: Otros

**Ejemplo de uso:**
- Si una solicitud viene de **BOGOTA**, el sistema busca asesores en:
  1. BOGOTA (proximidad 5.0)
  2. Otros municipios del Área Metropolitana de Bogotá (proximidad 4.0)
  3. Municipios del HUB_CENTRO (proximidad 3.5)
  4. Resto del país (proximidad 3.0)

### Constraint Único

`UNIQUE (area_metropolitana, municipio_norm)` - Evita duplicados de municipios en la misma área metropolitana.

---

## 2. Tabla: HUBS_LOGISTICOS

### Estructura

```sql
CREATE TABLE hubs_logisticos (
    id                    UUID PRIMARY KEY,
    created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    municipio_norm        VARCHAR(100) NOT NULL,
    hub_asignado_norm     VARCHAR(100) NOT NULL,
    distancia_km          INTEGER,
    tiempo_estimado_horas NUMERIC(4,1),
    
    CONSTRAINT uid_hubs_logist_municip_c349e9 
        UNIQUE (municipio_norm, hub_asignado_norm)
);
```

### Propósito

Esta tabla asigna **hubs logísticos** a cada municipio de Colombia basándose en criterios de distancia (200km). Se utiliza para el **algoritmo de escalamiento** cuando no hay asesores en la misma ciudad o área metropolitana.

### Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID | Identificador único |
| `created_at` | TIMESTAMP | Fecha de creación |
| `updated_at` | TIMESTAMP | Fecha de actualización |
| `municipio_norm` | VARCHAR(100) | Municipio normalizado (UPPERCASE, sin tildes) |
| `hub_asignado_norm` | VARCHAR(100) | Hub logístico asignado (normalizado) |
| `distancia_km` | INTEGER | Distancia al hub en kilómetros (opcional) |
| `tiempo_estimado_horas` | NUMERIC(4,1) | Tiempo estimado de entrega en horas (opcional) |

### Datos Actuales (4 registros)

| Municipio Norm | Hub Asignado Norm | Distancia KM | Tiempo Estimado |
|----------------|-------------------|--------------|-----------------|
| BOGOTA | HUB_CENTRO | NULL | NULL |
| MEDELLIN | HUB_ANTIOQUIA | NULL | NULL |
| CALI | HUB_VALLE | NULL | NULL |
| BARRANQUILLA | HUB_ATLANTICO | NULL | NULL |

### Hubs Logísticos Definidos

1. **HUB_CENTRO** - Bogotá y región central
2. **HUB_ANTIOQUIA** - Medellín y región antioqueña
3. **HUB_VALLE** - Cali y región del Valle del Cauca
4. **HUB_ATLANTICO** - Barranquilla y región Caribe

### Uso en el Sistema

**Algoritmo de Escalamiento - Nivel 3:**

Cuando no hay asesores en la misma ciudad o área metropolitana, el sistema busca asesores en el mismo hub logístico con proximidad 3.5.

**Ejemplo de uso:**
- Solicitud de **BUCARAMANGA** (HUB_CENTRO)
- Busca asesores en:
  1. BUCARAMANGA (proximidad 5.0)
  2. Área metropolitana de Bucaramanga si existe (proximidad 4.0)
  3. Otros municipios del HUB_CENTRO: BOGOTA, TUNJA, etc. (proximidad 3.5)
  4. Resto del país (proximidad 3.0)

### Constraint Único

`UNIQUE (municipio_norm, hub_asignado_norm)` - Evita duplicados de asignación municipio-hub.

---

## 3. Integración con el Algoritmo de Escalamiento

### Flujo de Cálculo de Proximidad

```python
def calcular_proximidad(ciudad_solicitud: str, ciudad_asesor: str) -> tuple[float, str]:
    """
    Calcula la proximidad geográfica entre solicitud y asesor
    
    Returns:
        (puntaje_proximidad, criterio_usado)
    """
    
    # Normalizar ciudades
    ciudad_sol_norm = normalizar_ciudad(ciudad_solicitud)
    ciudad_ase_norm = normalizar_ciudad(ciudad_asesor)
    
    # 1. Misma ciudad (Proximidad 5.0)
    if ciudad_sol_norm == ciudad_ase_norm:
        return (5.0, "misma_ciudad")
    
    # 2. Misma área metropolitana (Proximidad 4.0)
    municipios_am = get_municipios_area_metropolitana(ciudad_sol_norm)
    if ciudad_ase_norm in municipios_am:
        return (4.0, "area_metropolitana")
    
    # 3. Mismo hub logístico (Proximidad 3.5)
    hub_solicitud = get_hub_ciudad(ciudad_sol_norm)
    hub_asesor = get_hub_ciudad(ciudad_ase_norm)
    if hub_solicitud and hub_asesor and hub_solicitud == hub_asesor:
        return (3.5, "hub_logistico")
    
    # 4. Otros (Proximidad 3.0)
    return (3.0, "otros")
```

### Puntaje Total de Escalamiento

El puntaje de proximidad se combina con otras métricas:

```
Puntaje Total = (Proximidad × 0.40) + 
                (Actividad Reciente × 0.25) + 
                (Desempeño Histórico × 0.20) + 
                (Confianza × 0.15)
```

**Peso de Proximidad: 40%** - Es el factor más importante

---

## 4. Estado Actual de los Datos

### Observaciones

1. **Datos Mínimos**: Solo 4 registros en cada tabla (ciudades principales)
2. **Campos Opcionales Vacíos**: 
   - `departamento` y `poblacion` en `areas_metropolitanas`
   - `distancia_km` y `tiempo_estimado_horas` en `hubs_logisticos`
3. **Falta Información**: 
   - No hay municipios secundarios en las áreas metropolitanas
   - No hay asignaciones de hubs para ciudades intermedias

### Datos Faltantes Importantes

**Áreas Metropolitanas que deberían incluirse:**

- **Área Metropolitana de Bogotá**: Soacha, Chía, Zipaquirá, Facatativá, etc.
- **Área Metropolitana del Valle de Aburrá**: Envigado, Itagüí, Bello, Sabaneta, etc.
- **Área Metropolitana de Cali**: Yumbo, Palmira, Jamundí, etc.
- **Área Metropolitana de Barranquilla**: Soledad, Malambo, Puerto Colombia, etc.

**Hubs Logísticos que deberían incluirse:**

- Ciudades intermedias: Bucaramanga, Cartagena, Cúcuta, Pereira, Manizales, etc.
- Municipios cercanos a cada hub (radio de 200km)

---

## 5. Recomendaciones

### Datos a Completar

1. **Áreas Metropolitanas**:
   - Agregar todos los municipios de cada área metropolitana
   - Completar campos `departamento` y `poblacion`
   - Incluir áreas metropolitanas secundarias

2. **Hubs Logísticos**:
   - Asignar hubs a todas las ciudades de Colombia
   - Completar `distancia_km` y `tiempo_estimado_horas`
   - Definir criterios claros de asignación (200km de radio)

3. **Archivos de Origen**:
   - Crear/importar `Areas_Metropolitanas_TeLOO.xlsx`
   - Crear/importar `Asignacion_Hubs_200km.xlsx`

### Script de Importación

Debería existir un script para importar datos desde Excel:

```python
# services/core-api/scripts/import_geografia.py

async def import_areas_metropolitanas(file_path: str):
    """Importa áreas metropolitanas desde Excel"""
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        await AreaMetropolitana.create(
            area_metropolitana=row['area_metropolitana'],
            ciudad_nucleo=row['ciudad_nucleo'],
            municipio_norm=normalizar_ciudad(row['municipio']),
            departamento=row['departamento'],
            poblacion=row['poblacion']
        )

async def import_hubs_logisticos(file_path: str):
    """Importa hubs logísticos desde Excel"""
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        await HubLogistico.create(
            municipio_norm=normalizar_ciudad(row['municipio']),
            hub_asignado_norm=row['hub_asignado'],
            distancia_km=row['distancia_km'],
            tiempo_estimado_horas=row['tiempo_estimado_horas']
        )
```

---

## 6. Impacto en el Sistema

### Sin Datos Completos

- El algoritmo de escalamiento solo funciona correctamente para las 4 ciudades principales
- Solicitudes de otras ciudades siempre tendrán proximidad 3.0 (otros)
- No se aprovecha el criterio de área metropolitana ni hub logístico

### Con Datos Completos

- Escalamiento más preciso y eficiente
- Mejor distribución de solicitudes a asesores cercanos
- Tiempos de entrega más realistas
- Mayor cobertura geográfica

---

**Fecha de análisis:** 2025-11-08  
**Base de datos:** teloo_v3  
**Registros actuales:** 4 áreas metropolitanas, 4 hubs logísticos
