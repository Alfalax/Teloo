"""
Script para probar el Dashboard de Salud del Marketplace
"""
import requests
import json
from datetime import datetime, timedelta

ANALYTICS_URL = "http://localhost:8002"

def test_salud_marketplace():
    """Probar el endpoint de salud del marketplace"""
    
    # Calcular fechas (últimos 7 días)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=7)
    
    print("\n" + "="*80)
    print("🏥 PROBANDO DASHBOARD SALUD DEL MARKETPLACE")
    print("="*80)
    print(f"Período: {fecha_inicio.date()} a {fecha_fin.date()}")
    print()
    
    # Llamar al endpoint
    url = f"{ANALYTICS_URL}/v1/dashboards/salud-marketplace"
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
            print("\n📊 VALIDACIÓN DE ESTRUCTURA:")
            print("-" * 80)
            
            metricas = data.get('metricas', {})
            
            # 1. Ratio Oferta/Demanda
            if 'ratio_oferta_demanda' in metricas:
                ratio = metricas['ratio_oferta_demanda']
                print(f"✅ Ratio Oferta/Demanda:")
                print(f"   - Asesores Activos: {ratio.get('asesores_activos', 0)}")
                print(f"   - Solicitudes Diarias: {ratio.get('solicitudes_diarias_promedio', 0)}")
                print(f"   - Ratio: {ratio.get('ratio', 0)}")
            else:
                print("❌ Falta: ratio_oferta_demanda")
            
            # 2. Densidad de Ofertas
            if 'densidad_ofertas' in metricas:
                densidad = metricas['densidad_ofertas']
                print(f"✅ Densidad de Ofertas:")
                print(f"   - Solicitudes Llenadas: {densidad.get('solicitudes_llenadas', 0)}")
                print(f"   - Total Ofertas: {densidad.get('total_ofertas', 0)}")
                print(f"   - Densidad Promedio: {densidad.get('densidad_promedio', 0)}")
                print(f"   - Rango: {densidad.get('min_ofertas', 0)} - {densidad.get('max_ofertas', 0)}")
            else:
                print("❌ Falta: densidad_ofertas")
            
            # 3. Tasa de Participación
            if 'tasa_participacion_asesores' in metricas:
                participacion = metricas['tasa_participacion_asesores']
                print(f"✅ Tasa de Participación:")
                print(f"   - Total Habilitados: {participacion.get('total_habilitados', 0)}")
                print(f"   - Total Participantes: {participacion.get('total_participantes', 0)}")
                print(f"   - Tasa: {participacion.get('tasa_participacion', 0)}%")
            else:
                print("❌ Falta: tasa_participacion_asesores")
            
            # 4. Tasa de Adjudicación Promedio
            if 'tasa_adjudicacion_promedio' in metricas:
                adjudicacion = metricas['tasa_adjudicacion_promedio']
                print(f"✅ Tasa de Adjudicación Promedio:")
                print(f"   - Asesores con Ofertas: {adjudicacion.get('asesores_con_ofertas', 0)}")
                print(f"   - Tasa Promedio: {adjudicacion.get('tasa_promedio', 0)}%")
                print(f"   - Mediana: {adjudicacion.get('mediana', 0)}%")
                print(f"   - Rango: {adjudicacion.get('min_tasa', 0)}% - {adjudicacion.get('max_tasa', 0)}%")
            else:
                print("❌ Falta: tasa_adjudicacion_promedio")
            
            # 5. Tasa de Aceptación del Cliente
            if 'tasa_aceptacion_cliente' in metricas:
                aceptacion = metricas['tasa_aceptacion_cliente']
                print(f"✅ Tasa de Aceptación del Cliente:")
                print(f"   - Total Adjudicadas: {aceptacion.get('total_adjudicadas', 0)}")
                print(f"   - Aceptadas: {aceptacion.get('aceptadas', 0)}")
                print(f"   - Tasa: {aceptacion.get('tasa_aceptacion', 0)}%")
            else:
                print("❌ Falta: tasa_aceptacion_cliente")
            
            print("-" * 80)
            
            # Análisis de salud
            print("\n🏥 ANÁLISIS DE SALUD DEL MARKETPLACE:")
            print("-" * 80)
            
            if 'ratio_oferta_demanda' in metricas:
                ratio_val = metricas['ratio_oferta_demanda'].get('ratio', 0)
                if ratio_val < 10:
                    print("🔴 CRÍTICO: Ratio Oferta/Demanda muy bajo - Riesgo de saturación")
                elif ratio_val > 30:
                    print("🟡 ADVERTENCIA: Ratio Oferta/Demanda alto - Exceso de oferta")
                else:
                    print("🟢 SALUDABLE: Ratio Oferta/Demanda en rango óptimo")
            
            if 'tasa_participacion_asesores' in metricas:
                participacion_val = metricas['tasa_participacion_asesores'].get('tasa_participacion', 0)
                if participacion_val < 50:
                    print("🔴 CRÍTICO: Baja participación de asesores")
                elif participacion_val < 70:
                    print("🟡 ADVERTENCIA: Participación de asesores mejorable")
                else:
                    print("🟢 SALUDABLE: Buena participación de asesores")
            
            if 'tasa_aceptacion_cliente' in metricas:
                aceptacion_val = metricas['tasa_aceptacion_cliente'].get('tasa_aceptacion', 0)
                if aceptacion_val < 60:
                    print("🔴 CRÍTICO: Baja aceptación del cliente - Revisar algoritmo")
                elif aceptacion_val < 80:
                    print("🟡 ADVERTENCIA: Aceptación del cliente mejorable")
                else:
                    print("🟢 SALUDABLE: Buena aceptación del cliente")
            
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
    test_salud_marketplace()
