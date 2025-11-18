"""
Simulación del flujo del job para la solicitud 91269925
"""

# DATOS REALES
solicitud_id = "91269925-529b-496e-974d-37c228c06bbd"
fecha_escalamiento = "2025-11-14 17:12:58.036517+00"
fecha_oferta = "2025-11-14 17:14:35.258359+00"
fecha_evaluacion = "2025-11-14 17:15:34.972822+00"

nivel_actual = 4
ofertas_minimas_deseadas = 2
tiempos_espera_nivel = {1: 2, 2: 2, 3: 2, 4: 2, 5: 2}

# Datos de ofertas
total_repuestos = 5
ofertas_recibidas = 1
repuestos_cubiertos_por_oferta = 3  # 60% cobertura

print("="*80)
print("SIMULACIÓN DEL FLUJO DEL JOB")
print("="*80)

print(f"\n1. SOLICITUD CREADA Y ESCALADA")
print(f"   - Nivel actual: {nivel_actual}")
print(f"   - Fecha escalamiento: {fecha_escalamiento}")
print(f"   - Ofertas mínimas deseadas: {ofertas_minimas_deseadas}")
print(f"   - Tiempo de espera nivel {nivel_actual}: {tiempos_espera_nivel[nivel_actual]} minutos")

print(f"\n2. OFERTA RECIBIDA")
print(f"   - Fecha: {fecha_oferta}")
print(f"   - Minutos desde escalamiento: 1.62 min")
print(f"   - Repuestos cubiertos: {repuestos_cubiertos_por_oferta}/{total_repuestos} (60%)")

print(f"\n3. JOB EJECUTÁNDOSE (cada minuto)")
print(f"   Verificando si timeout alcanzado...")

# Simular ejecuciones del job
from datetime import datetime, timezone, timedelta

fecha_esc = datetime.fromisoformat(fecha_escalamiento.replace('+00', '+00:00'))
fecha_eval = datetime.fromisoformat(fecha_evaluacion.replace('+00', '+00:00'))

print(f"\n   Ejecuciones del job:")
current_time = fecha_esc
execution = 0
while current_time <= fecha_eval:
    execution += 1
    tiempo_transcurrido = current_time - fecha_esc
    minutos_transcurridos = int(tiempo_transcurrido.total_seconds() / 60)
    tiempo_espera = tiempos_espera_nivel[nivel_actual]
    
    print(f"\n   Ejecución #{execution} - {current_time.strftime('%H:%M:%S')}")
    print(f"      Minutos transcurridos: {minutos_transcurridos}")
    print(f"      Tiempo espera requerido: {tiempo_espera}")
    
    if minutos_transcurridos < tiempo_espera:
        print(f"      ❌ Timeout NO alcanzado ({minutos_transcurridos} < {tiempo_espera})")
        print(f"      Acción: continue (no hace nada)")
    else:
        print(f"      ✅ Timeout ALCANZADO ({minutos_transcurridos} >= {tiempo_espera})")
        
        # Verificar ofertas completas
        ofertas_completas = 0  # Ninguna oferta cubre 100%
        print(f"      Ofertas completas (100% cobertura): {ofertas_completas}")
        print(f"      Ofertas mínimas deseadas: {ofertas_minimas_deseadas}")
        
        if ofertas_completas >= ofertas_minimas_deseadas:
            print(f"      ✅ Condición cumplida: {ofertas_completas} >= {ofertas_minimas_deseadas}")
            print(f"      Acción: EVALUAR Y CERRAR")
            break
        else:
            print(f"      ❌ Condición NO cumplida: {ofertas_completas} < {ofertas_minimas_deseadas}")
            print(f"      Verificando si puede escalar...")
            
            NIVEL_MAXIMO = 5
            if nivel_actual >= NIVEL_MAXIMO:
                print(f"      ⚠️ Nivel máximo alcanzado ({nivel_actual} >= {NIVEL_MAXIMO})")
                print(f"      Hay ofertas: {ofertas_recibidas > 0}")
                if ofertas_recibidas > 0:
                    print(f"      Acción: EVALUAR CON OFERTAS DISPONIBLES")
                    break
                else:
                    print(f"      Acción: CERRAR SIN OFERTAS")
                    break
            else:
                print(f"      ✅ Puede escalar ({nivel_actual} < {NIVEL_MAXIMO})")
                print(f"      Acción: ESCALAR A NIVEL {nivel_actual + 1}")
                # En la realidad, aquí escalaría y actualizaría fecha_escalamiento
                # Pero en este caso, se evaluó en lugar de escalar
                break
    
    current_time += timedelta(minutes=1)

print(f"\n4. RESULTADO REAL")
print(f"   - Fecha evaluación: {fecha_evaluacion}")
print(f"   - Minutos desde escalamiento: 2.62 min")
print(f"   - Estado final: EVALUADA")
print(f"   - Nivel final: {nivel_actual} (NO escaló a nivel 5)")

print(f"\n" + "="*80)
print("CONCLUSIÓN")
print("="*80)
print(f"La solicitud se evaluó a los 2.62 minutos, cuando el timeout era de 2 minutos.")
print(f"Según el código, debería haber:")
print(f"1. Detectado timeout a los 2 minutos")
print(f"2. Verificado ofertas completas: 0 < 2 (NO cumple)")
print(f"3. Verificado nivel: 4 < 5 (puede escalar)")
print(f"4. ESCALADO a nivel 5")
print(f"\nPero en lugar de eso, se EVALUÓ directamente.")
print(f"\n¿Por qué? Necesito revisar si hay otro código que evalúa solicitudes...")
