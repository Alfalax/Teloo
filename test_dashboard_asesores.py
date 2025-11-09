"""
Script para probar el Dashboard de Análisis de Asesores
"""
import requests
import json
from datetime import datetime, timedelta

ANALYTICS_URL = "http://localhost:8002"

def test_dashboard_asesores():
    """Probar el endpoint del dashboard de asesores"""
    
    # Calcular fechas (últimos 30 días)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    print("\n" + "="*80)
    print("👥 PROBANDO DASHBOARD ANÁLISIS DE ASESORES")
    print("="*80)
    print(f"Período: {fecha_inicio.date()} a {fecha_fin.date()}")
    print()
    
    # Llamar al endpoint
    url = f"{ANALYTICS_URL}/v1/dashboards/asesores"
    params = {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat()
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            # Mostrar estructura de respuesta
            print("✅ RESPUESTA EXITOSA")
            print("-" * 80)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print("-" * 80)
            
            # Validar estructura
            print("\n📊 VALIDACIÓN DE ESTRUCTURA (13 KPIs):")
            print("-" * 80)
            
            metricas = data.get('metricas', {})
            kpis_esperados = [
                'total_asesores_activos',
                'tasa_respuesta_promedio',
                'tiempo_respuesta_promedio',
                'ofertas_por_asesor',
                'tasa_adjudicacion_por_asesor',
                'ranking_top_10',
                'especializacion_repuestos',
                'distribucion_geografica',
                'nivel_confianza_promedio',
                'asesores_nuevos',
                'tasa_retencion',
                'satisfaccion_cliente',
                'valor_promedio_oferta'
            ]
            
            kpis_encontrados = 0
            for kpi in kpis_esperados:
                if kpi in metricas:
                    print(f"✅ {kpi}")
                    kpis_encontrados += 1
                else:
                    print(f"❌ Falta: {kpi}")
            
            print("-" * 80)
            print(f"\nKPIs Implementados: {kpis_encontrados}/13")
            
            # Detalles de métricas clave
            print("\n📈 DETALLES DE MÉTRICAS CLAVE:")
            print("-" * 80)
            
            if 'total_asesores_activos' in metricas:
                print(f"Total Asesores Activos: {metricas['total_asesores_activos']}")
            
            if 'tasa_respuesta_promedio' in metricas:
                tasa = metricas['tasa_respuesta_promedio']
                print(f"Tasa de Respuesta: {tasa.get('tasa_promedio', 0)}%")
            
            if 'tiempo_respuesta_promedio' in metricas:
                tiempo = metricas['tiempo_respuesta_promedio']
                print(f"Tiempo de Respuesta: {tiempo.get('tiempo_promedio_minutos', 0)} min")
            
            if 'ofertas_por_asesor' in metricas:
                ofertas = metricas['ofertas_por_asesor']
                print(f"Ofertas por Asesor: {ofertas.get('ofertas_promedio', 0)} (promedio)")
            
            if 'tasa_adjudicacion_por_asesor' in metricas:
                adj = metricas['tasa_adjudicacion_por_asesor']
                print(f"Tasa de Adjudicación: {adj.get('tasa_promedio', 0)}%")
            
            if 'ranking_top_10' in metricas:
                ranking = metricas['ranking_top_10']
                print(f"Top Asesores: {len(ranking)} en ranking")
                if ranking:
                    print(f"  #1: {ranking[0].get('nombre_comercial', 'N/A')} - {ranking[0].get('ofertas_ganadoras', 0)} ganadoras")
            
            if 'nivel_confianza_promedio' in metricas:
                confianza = metricas['nivel_confianza_promedio']
                print(f"Nivel de Confianza: {confianza.get('nivel_promedio', 0)}/5.0")
            
            if 'tasa_retencion' in metricas:
                retencion = metricas['tasa_retencion']
                print(f"Tasa de Retención: {retencion.get('tasa_retencion', 0)}%")
            
            if 'satisfaccion_cliente' in metricas:
                satisfaccion = metricas['satisfaccion_cliente']
                print(f"Satisfacción Cliente: {satisfaccion.get('calificacion_promedio', 0)}/5.0")
            
            print("-" * 80)
            
            # Análisis de salud
            print("\n👥 ANÁLISIS DE DESEMPEÑO:")
            print("-" * 80)
            
            if 'tasa_respuesta_promedio' in metricas:
                tasa_val = metricas['tasa_respuesta_promedio'].get('tasa_promedio', 0)
                if tasa_val < 60:
                    print(f"🔴 CRÍTICO: Tasa de respuesta baja ({tasa_val}%)")
                elif tasa_val < 75:
                    print(f"🟡 ADVERTENCIA: Tasa de respuesta mejorable ({tasa_val}%)")
                else:
                    print(f"🟢 SALUDABLE: Buena tasa de respuesta ({tasa_val}%)")
            
            if 'tiempo_respuesta_promedio' in metricas:
                tiempo_val = metricas['tiempo_respuesta_promedio'].get('tiempo_promedio_minutos', 0)
                if tiempo_val > 60:
                    print(f"🔴 CRÍTICO: Tiempo de respuesta lento ({tiempo_val} min)")
                elif tiempo_val > 30:
                    print(f"🟡 ADVERTENCIA: Tiempo de respuesta aceptable ({tiempo_val} min)")
                elif tiempo_val > 0:
                    print(f"🟢 SALUDABLE: Tiempo de respuesta óptimo ({tiempo_val} min)")
            
            if 'tasa_adjudicacion_por_asesor' in metricas:
                adj_val = metricas['tasa_adjudicacion_por_asesor'].get('tasa_promedio', 0)
                if adj_val < 25:
                    print(f"🔴 CRÍTICO: Tasa de adjudicación baja ({adj_val}%)")
                elif adj_val < 40:
                    print(f"🟡 ADVERTENCIA: Tasa de adjudicación buena ({adj_val}%)")
                elif adj_val > 0:
                    print(f"🟢 SALUDABLE: Tasa de adjudicación excelente ({adj_val}%)")
            
            if 'tasa_retencion' in metricas:
                ret_val = metricas['tasa_retencion'].get('tasa_retencion', 0)
                if ret_val < 60:
                    print(f"🔴 CRÍTICO: Retención crítica ({ret_val}%)")
                elif ret_val < 75:
                    print(f"🟡 ADVERTENCIA: Retención preocupante ({ret_val}%)")
                elif ret_val < 85:
                    print(f"🟢 SALUDABLE: Retención aceptable ({ret_val}%)")
                elif ret_val > 0:
                    print(f"🟢 EXCELENTE: Retención saludable ({ret_val}%)")
            
            print("-" * 80)
            print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar al servicio de analytics")
        print("   Verifica que el contenedor teloo-analytics esté corriendo")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_asesores()
