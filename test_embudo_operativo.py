"""
Script para probar el Dashboard de Embudo Operativo
"""
import requests
import json
from datetime import datetime, timedelta

ANALYTICS_URL = "http://localhost:8002"

def test_embudo_operativo():
    """Probar el endpoint de embudo operativo"""
    
    # Calcular fechas (últimos 30 días)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    print("\n" + "="*80)
    print("🔍 PROBANDO DASHBOARD EMBUDO OPERATIVO")
    print("="*80)
    print(f"Período: {fecha_inicio.date()} a {fecha_fin.date()}")
    print()
    
    # Llamar al endpoint
    url = f"{ANALYTICS_URL}/v1/dashboards/embudo-operativo"
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
            
            # 1. Tasa de Entrada
            if 'tasa_entrada' in metricas:
                tasa_entrada = metricas['tasa_entrada']
                dias_con_datos = len(tasa_entrada.get('por_dia', []))
                print(f"✅ Tasa de Entrada: {dias_con_datos} días con datos")
            else:
                print("❌ Falta: tasa_entrada")
            
            # 2-5. Conversiones
            if 'conversiones' in metricas:
                conv = metricas['conversiones']
                print(f"✅ Conversiones:")
                print(f"   - ABIERTA → EVALUACION: {conv.get('abierta_a_evaluacion', 0)}%")
                print(f"   - EVALUACION → ADJUDICADA: {conv.get('evaluacion_a_adjudicada', 0)}%")
                print(f"   - ADJUDICADA → ACEPTADA: {conv.get('adjudicada_a_aceptada', 0)}%")
                print(f"   - Conversión General: {conv.get('conversion_general', 0)}%")
            else:
                print("❌ Falta: conversiones")
            
            # 6-8. Tiempos
            if 'tiempos' in metricas:
                tiempos = metricas['tiempos']
                print(f"✅ Tiempos:")
                ttfo = tiempos.get('ttfo', {})
                tta = tiempos.get('tta', {})
                ttcd = tiempos.get('ttcd', {})
                print(f"   - TTFO (mediana): {ttfo.get('mediana_horas', 0)} horas")
                print(f"   - TTA (mediana): {tta.get('mediana_horas', 0)} horas")
                print(f"   - TTCD (mediana): {ttcd.get('mediana_horas', 0)} horas")
            else:
                print("❌ Falta: tiempos")
            
            # 9-11. Fallos
            if 'fallos' in metricas:
                fallos = metricas['fallos']
                print(f"✅ Fallos:")
                print(f"   - Tasa de Llenado: {fallos.get('tasa_llenado', 0)}%")
                print(f"   - Tasa de Escalamiento: {fallos.get('tasa_escalamiento', 0)}%")
                fallo_nivel = fallos.get('fallo_por_nivel', {})
                print(f"   - Fallo por Nivel: {len(fallo_nivel)} niveles")
                for nivel, tasa in fallo_nivel.items():
                    print(f"     * Nivel {nivel}: {tasa}%")
            else:
                print("❌ Falta: fallos")
            
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
    test_embudo_operativo()
