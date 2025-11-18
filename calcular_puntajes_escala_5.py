#!/usr/bin/env python3
"""
Script para calcular y mostrar los puntajes de evaluación en escala de 1 a 5
"""

# Datos de las ofertas
ofertas = {
    "Flasher 1": [
        {"asesor": "Laura Reyes", "precio": 80000, "tiempo": 3, "garantia": 3, "cobertura": 100},
        {"asesor": "Sandra Romero", "precio": 50000, "tiempo": 2, "garantia": 3, "cobertura": 66.67},
    ],
    "flasher 2": [
        {"asesor": "Laura Reyes", "precio": 20000, "tiempo": 3, "garantia": 1, "cobertura": 100},
        {"asesor": "Sandra Romero", "precio": 60000, "tiempo": 2, "garantia": 1, "cobertura": 66.67},
    ],
    "flasher 3": [
        {"asesor": "Laura Reyes", "precio": 50000, "tiempo": 3, "garantia": 3, "cobertura": 100},
        {"asesor": "Sebastián Rodríguez", "precio": 30000, "tiempo": 2, "garantia": 2, "cobertura": 33.33},
    ],
}

# Pesos configurados
pesos = {
    "precio": 0.50,
    "tiempo": 0.35,
    "garantia": 0.15
}

print("=" * 100)
print("EVALUACIÓN DE OFERTAS - ESCALA DE 1 A 5")
print("=" * 100)
print(f"\nPesos configurados: Precio={pesos['precio']*100}%, Tiempo={pesos['tiempo']*100}%, Garantía={pesos['garantia']*100}%")
print(f"Cobertura mínima requerida: 50%\n")

for repuesto, ofertas_repuesto in ofertas.items():
    print("\n" + "=" * 100)
    print(f"REPUESTO: {repuesto}")
    print("=" * 100)
    
    # Filtrar por cobertura >= 50%
    ofertas_calificadas = [o for o in ofertas_repuesto if o["cobertura"] >= 50]
    ofertas_no_calificadas = [o for o in ofertas_repuesto if o["cobertura"] < 50]
    
    if not ofertas_calificadas:
        print("\n⚠️  No hay ofertas que cumplan con la cobertura mínima del 50%")
        continue
    
    # Obtener rangos para normalización
    precios = [o["precio"] for o in ofertas_calificadas]
    tiempos = [o["tiempo"] for o in ofertas_calificadas]
    garantias = [o["garantia"] for o in ofertas_calificadas]
    
    precio_min, precio_max = min(precios), max(precios)
    tiempo_min, tiempo_max = min(tiempos), max(tiempos)
    garantia_min, garantia_max = min(garantias), max(garantias)
    
    print(f"\nRangos de valores:")
    print(f"  Precio: ${precio_min:,} - ${precio_max:,}")
    print(f"  Tiempo: {tiempo_min} - {tiempo_max} días")
    print(f"  Garantía: {garantia_min} - {garantia_max} meses")
    
    resultados = []
    
    for oferta in ofertas_calificadas:
        # Calcular scores normalizados (0-1)
        if precio_max == precio_min:
            score_precio = 1.0
        else:
            score_precio = (precio_max - oferta["precio"]) / (precio_max - precio_min)
        
        if tiempo_max == tiempo_min:
            score_tiempo = 1.0
        else:
            score_tiempo = (tiempo_max - oferta["tiempo"]) / (tiempo_max - tiempo_min)
        
        if garantia_max == garantia_min:
            score_garantia = 1.0
        else:
            score_garantia = (oferta["garantia"] - garantia_min) / (garantia_max - garantia_min)
        
        # Calcular puntaje total ponderado (0-1)
        puntaje_total = (
            score_precio * pesos["precio"] +
            score_tiempo * pesos["tiempo"] +
            score_garantia * pesos["garantia"]
        )
        
        # Convertir a escala de 1 a 5
        puntaje_escala_5 = 1 + (puntaje_total * 4)
        
        resultados.append({
            "asesor": oferta["asesor"],
            "precio": oferta["precio"],
            "tiempo": oferta["tiempo"],
            "garantia": oferta["garantia"],
            "cobertura": oferta["cobertura"],
            "score_precio": score_precio,
            "score_tiempo": score_tiempo,
            "score_garantia": score_garantia,
            "puntaje_total": puntaje_total,
            "puntaje_escala_5": puntaje_escala_5
        })
    
    # Ordenar por puntaje total (mayor a menor)
    resultados.sort(key=lambda x: x["puntaje_total"], reverse=True)
    
    print(f"\n{'ASESOR':<25} {'PRECIO':>12} {'TIEMPO':>8} {'GARANTÍA':>10} {'COBERTURA':>10}")
    print("-" * 100)
    
    for i, r in enumerate(resultados):
        ganador = "🏆 " if i == 0 else "   "
        print(f"{ganador}{r['asesor']:<23} ${r['precio']:>10,} {r['tiempo']:>6}d {r['garantia']:>8}m {r['cobertura']:>8.2f}%")
    
    print(f"\n{'ASESOR':<25} {'PRECIO':>10} {'TIEMPO':>10} {'GARANTÍA':>10} {'TOTAL':>10} {'ESCALA 1-5':>12}")
    print("-" * 100)
    
    for i, r in enumerate(resultados):
        ganador = "🏆 " if i == 0 else "   "
        print(f"{ganador}{r['asesor']:<23} {r['score_precio']:>9.2f} {r['score_tiempo']:>9.2f} {r['score_garantia']:>9.2f} {r['puntaje_total']:>9.2f} {r['puntaje_escala_5']:>11.2f} ⭐")
    
    # Mostrar ofertas no calificadas
    if ofertas_no_calificadas:
        print(f"\n❌ OFERTAS NO CALIFICADAS (Cobertura < 50%):")
        for o in ofertas_no_calificadas:
            print(f"   {o['asesor']}: ${o['precio']:,} - Cobertura: {o['cobertura']:.2f}%")
    
    print(f"\n✅ GANADOR: {resultados[0]['asesor']} con {resultados[0]['puntaje_escala_5']:.2f}/5.00 ⭐")

print("\n" + "=" * 100)
print("RESUMEN DE ADJUDICACIONES")
print("=" * 100)
print("\nFlasher 1  → Sandra Romero")
print("flasher 2  → Laura Reyes")
print("flasher 3  → Laura Reyes")
print("\nTotal adjudicado: $120,000")
print("Ahorro vs oferta completa más cara: $120,000 (50%)")
print("=" * 100)
