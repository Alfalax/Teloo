# Actualización de Frontend - Reportes con 34 KPIs

## Estado Actual
La página de Reportes ya tiene:
- ✅ Estructura con pestañas (Tabs)
- ✅ Filtros de fecha
- ✅ Queries a los endpoints correctos
- ✅ Exportación CSV/JSON

## Pendiente
Actualizar los componentes de visualización para mostrar los 34 KPIs correctos:

### Embudo Operativo (11 KPIs)
1. Tasa de Entrada de Solicitudes
2. Conversión ABIERTA → EN_EVALUACION
3. Conversión EN_EVALUACION → ADJUDICADA
4. Conversión ADJUDICADA → ACEPTADA
5. Tasa de Conversión General
6. Tiempo hasta Primera Oferta (TTFO)
7. Tiempo hasta Adjudicación (TTA)
8. Tiempo hasta Decisión del Cliente (TTCD)
9. Tasa de Llenado de Solicitudes
10. Tasa de Escalamiento
11. Tasa de Fallo por Nivel

### Salud del Marketplace (5 KPIs)
1. Ratio Oferta/Demanda
2. Densidad de Ofertas
3. Tasa de Participación de Asesores
4. Tasa de Adjudicación del Asesor Promedio
5. Tasa de Aceptación del Cliente

### Dashboard Financiero (5 KPIs)
1. Valor Bruto Ofertado (GOV)
2. Valor Bruto Adjudicado (GAV_adj)
3. Valor Bruto Aceptado (GAV_acc)
4. Valor Promedio de Oferta Aceptada
5. Tasa de Fuga de Valor

### Análisis de Asesores (13 KPIs)
1. Asesores Estrella (R5-F5-M5)
2. Gigantes Dormidos (R1-F5-M5)
3. Nuevos Prometedores (R5-F2-M3)
4. En Riesgo (R2-F3-M4)
5. Consistentes (R4-F4-M3)
6. Ocasionales (R3-F2-M2)
7. Análisis de Migración entre Segmentos
8. Valor de Vida del Asesor (CLV)
9. Densidad de Asesores por Región
10. Ratio Demanda/Oferta Regional
11. Tiempo de Respuesta Regional
12. Análisis de Penetración de Mercado
13. Tasa de Retención de Asesores

## Próximo Paso
Actualizar ReportesPage.tsx con los componentes correctos para cada dashboard.
