"""
Script para probar el Dashboard Financiero
"""
import requests
import json
from datetime import datetime, timedelta

ANALYTICS_URL = "http://localhost:8002"

def format_currency(value):
    """Formatear valor como moneda COP"""
    return f"${value:,.0f} COP"

def test_dashboard_financiero():
    """Probar el endpoint del dashboard financiero"""
    
    # Calcular fechas (últimos 30 días)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    print("\n" + "="*80)
    print("💰 PROBANDO DASHBOARD FINANCIERO")
    print("="*80)
    print(f"Período: {fecha_inicio.date()} a {fecha_fin.date()}")
    print()
    
    # Llamar al endpoint
    url = f"{ANALYTICS_URL}/v1/dashboards/financiero"
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
            
            # 1. Valor Bruto Ofertado (GOV)
            if 'valor_bruto_ofertado' in metricas:
                gov = metricas['valor_bruto_ofertado']
                print(f"✅ Valor Bruto Ofertado (GOV):")
                print(f"   - Total Ofertas: {gov.get('total_ofertas', 0)}")
                print(f"   - Valor Total: {format_currency(gov.get('valor_total', 0))}")
                print(f"   - Valor Promedio: {format_currency(gov.get('valor_promedio', 0))}")
                print(f"   - Rango: {format_currency(gov.get('valor_minimo', 0))} - {format_currency(gov.get('valor_maximo', 0))}")
            else:
                print("❌ Falta: valor_bruto_ofertado")
            
            # 2. Valor Bruto Adjudicado (GAV_adj)
            if 'valor_bruto_adjudicado' in metricas:
                gav_adj = metricas['valor_bruto_adjudicado']
                print(f"✅ Valor Bruto Adjudicado (GAV_adj):")
                print(f"   - Total Adjudicadas: {gav_adj.get('total_adjudicadas', 0)}")
                print(f"   - Valor Total: {format_currency(gav_adj.get('valor_total', 0))}")
                print(f"   - Valor Promedio: {format_currency(gav_adj.get('valor_promedio', 0))}")
                print(f"   - Rango: {format_currency(gav_adj.get('valor_minimo', 0))} - {format_currency(gav_adj.get('valor_maximo', 0))}")
            else:
                print("❌ Falta: valor_bruto_adjudicado")
            
            # 3. Valor Bruto Aceptado (GAV_acc)
            if 'valor_bruto_aceptado' in metricas:
                gav_acc = metricas['valor_bruto_aceptado']
                print(f"✅ Valor Bruto Aceptado (GAV_acc):")
                print(f"   - Total Aceptadas: {gav_acc.get('total_aceptadas', 0)}")
                print(f"   - Valor Total: {format_currency(gav_acc.get('valor_total', 0))}")
                print(f"   - Valor Promedio: {format_currency(gav_acc.get('valor_promedio', 0))}")
                print(f"   - Rango: {format_currency(gav_acc.get('valor_minimo', 0))} - {format_currency(gav_acc.get('valor_maximo', 0))}")
            else:
                print("❌ Falta: valor_bruto_aceptado")
            
            # 4. Valor Promedio por Solicitud
            if 'valor_promedio_solicitud' in metricas:
                promedio = metricas['valor_promedio_solicitud']
                print(f"✅ Valor Promedio por Solicitud:")
                print(f"   - Solicitudes Aceptadas: {promedio.get('solicitudes_aceptadas', 0)}")
                print(f"   - Valor Total: {format_currency(promedio.get('valor_total_aceptado', 0))}")
                print(f"   - Promedio: {format_currency(promedio.get('valor_promedio_por_solicitud', 0))}")
            else:
                print("❌ Falta: valor_promedio_solicitud")
            
            # 5. Tasa de Fuga de Valor
            if 'tasa_fuga_valor' in metricas:
                fuga = metricas['tasa_fuga_valor']
                print(f"✅ Tasa de Fuga de Valor:")
                print(f"   - Valor Adjudicado: {format_currency(fuga.get('valor_adjudicado', 0))}")
                print(f"   - Valor Aceptado: {format_currency(fuga.get('valor_aceptado', 0))}")
                print(f"   - Valor Fugado: {format_currency(fuga.get('valor_fugado', 0))}")
                print(f"   - Tasa de Fuga: {fuga.get('tasa_fuga_porcentaje', 0)}%")
            else:
                print("❌ Falta: tasa_fuga_valor")
            
            # 6. Resumen Financiero
            if 'resumen_financiero' in metricas:
                resumen = metricas['resumen_financiero']
                print(f"✅ Resumen Financiero:")
                print(f"   - Conversión Oferta→Adjudicación: {resumen.get('conversion_oferta_adjudicacion', 0)}%")
                print(f"   - Conversión Adjudicación→Aceptación: {resumen.get('conversion_adjudicacion_aceptacion', 0)}%")
                print(f"   - Conversión General: {resumen.get('conversion_general_financiera', 0)}%")
                print(f"   - Ticket Promedio: {format_currency(resumen.get('ticket_promedio_marketplace', 0))}")
            else:
                print("❌ Falta: resumen_financiero")
            
            print("-" * 80)
            
            # Análisis financiero
            print("\n💰 ANÁLISIS FINANCIERO:")
            print("-" * 80)
            
            if 'valor_bruto_ofertado' in metricas and 'valor_bruto_adjudicado' in metricas:
                gov_val = metricas['valor_bruto_ofertado'].get('valor_total', 0)
                gav_adj_val = metricas['valor_bruto_adjudicado'].get('valor_total', 0)
                
                if gov_val > 0:
                    ratio_adj = (gav_adj_val / gov_val) * 100
                    if ratio_adj < 20:
                        print(f"🔴 CRÍTICO: Ratio GAV_adj/GOV muy bajo ({ratio_adj:.1f}%) - Algoritmo restrictivo")
                    elif ratio_adj > 35:
                        print(f"🟡 ADVERTENCIA: Ratio GAV_adj/GOV alto ({ratio_adj:.1f}%) - Revisar calidad")
                    else:
                        print(f"🟢 SALUDABLE: Ratio GAV_adj/GOV óptimo ({ratio_adj:.1f}%)")
            
            if 'tasa_fuga_valor' in metricas:
                fuga_val = metricas['tasa_fuga_valor'].get('tasa_fuga_porcentaje', 0)
                if fuga_val > 40:
                    print(f"🔴 CRÍTICO: Tasa de fuga muy alta ({fuga_val}%) - Revisar matching")
                elif fuga_val > 30:
                    print(f"🟡 ADVERTENCIA: Tasa de fuga alta ({fuga_val}%)")
                elif fuga_val > 0:
                    print(f"🟢 SALUDABLE: Tasa de fuga aceptable ({fuga_val}%)")
            
            if 'valor_bruto_aceptado' in metricas:
                gav_acc_val = metricas['valor_bruto_aceptado'].get('valor_total', 0)
                if gav_acc_val > 0:
                    print(f"💵 Valor Real Generado: {format_currency(gav_acc_val)}")
            
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
    test_dashboard_financiero()
