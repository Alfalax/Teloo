# Plan de Actualización - Reportes Frontend

## Situación Actual
- El backend YA tiene los 34 KPIs correctos implementados (rama develop merged)
- El frontend tiene pestañas pero muestra KPIs antiguos
- Necesitamos actualizar SOLO la visualización en el frontend

## KPIs Correctos por Dashboard

### 1. Embudo Operativo (11 KPIs) - Del archivo Indicadores.txt
Los KPIs que el backend devuelve en `metricas`:
1. `tasa_entrada` - Tasa de Entrada de Solicitudes (por hora/día/semana)
2. `conversion_abierta_evaluacion` - % ABIERTA → EN_EVALUACION
3. `conversion_evaluacion_adjudicada` - % EN_EVALUACION → ADJUDICADA
4. `conversion_adjudicada_aceptada` - % ADJUDICADA → ACEPTADA
5. `tasa_conversion_general` - Tasa de Conversión General
6. `ttfo_mediana_horas` - Tiempo hasta Primera Oferta (TTFO)
7. `tta_mediana_horas` - Tiempo hasta Adjudicación (TTA)
8. `ttcd_mediana_horas` - Tiempo hasta Decisión Cliente (TTCD)
9. `tasa_llenado` - Tasa de Llenado de Solicitudes
10. `tasa_escalamiento` - Tasa de Escalamiento
11. `fallo_por_nivel` - Tasa de Fallo por Nivel

### 2. Salud del Marketplace (5 KPIs)
1. `ratio_oferta_demanda` - Ratio Oferta/Demanda
2. `densidad_ofertas` - Densidad de Ofertas
3. `tasa_participacion_asesores` - Tasa de Participación de Asesores
4. `tasa_adjudicacion_asesor_promedio` - Tasa de Adjudicación del Asesor Promedio
5. `tasa_aceptacion_cliente` - Tasa de Aceptación del Cliente

### 3. Dashboard Financiero (5 KPIs)
1. `gov` - Valor Bruto Ofertado (GOV)
2. `gav_adj` - Valor Bruto Adjudicado (GAV_adj)
3. `gav_acc` - Valor Bruto Aceptado (GAV_acc)
4. `valor_promedio_oferta_aceptada` - Valor Promedio de Oferta Aceptada
5. `tasa_fuga_valor` - Tasa de Fuga de Valor

### 4. Análisis de Asesores (13 KPIs)
Segmentos RFM:
1. `asesores_estrella` - Asesores Estrella (R5-F5-M5)
2. `gigantes_dormidos` - Gigantes Dormidos (R1-F5-M5)
3. `nuevos_prometedores` - Nuevos Prometedores (R5-F2-M3)
4. `en_riesgo` - En Riesgo (R2-F3-M4)
5. `consistentes` - Consistentes (R4-F4-M3)
6. `ocasionales` - Ocasionales (R3-F2-M2)

Análisis:
7. `migracion_segmentos` - Análisis de Migración entre Segmentos
8. `clv` - Valor de Vida del Asesor (CLV)
9. `densidad_asesores_region` - Densidad de Asesores por Región
10. `ratio_demanda_oferta_regional` - Ratio Demanda/Oferta Regional
11. `tiempo_respuesta_regional` - Tiempo de Respuesta Regional
12. `penetracion_mercado` - Análisis de Penetración de Mercado
13. `tasa_retencion` - Tasa de Retención de Asesores

## Acción Requerida
Actualizar los 4 componentes de visualización en ReportesPage.tsx para mostrar estos KPIs con sus nombres correctos.

El backend YA devuelve estos datos correctamente, solo necesitamos actualizar cómo los mostramos en el frontend.
