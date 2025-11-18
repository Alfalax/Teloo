#!/usr/bin/env python3
"""
Cálculo detallado paso a paso de la calificación de Sandra Romero para Flasher 1
"""

print("=" * 100)
print("CÁLCULO DETALLADO: SANDRA ROMERO - FLASHER 1")
print("=" * 100)

# Datos de las ofertas para Flasher 1
print("\n📋 PASO 1: DATOS DE LAS OFERTAS")
print("-" * 100)
print("\nOfertas recibidas para Flasher 1:")
print("  • Laura Reyes:    $80,000 | 3 días | 3 meses garantía | Cobertura: 100%")
print("  • Sandra Romero:  $50,000 | 2 días | 3 meses garantía | Cobertura: 66.67%")

# Filtro por cobertura
print("\n🔍 PASO 2: FILTRO POR COBERTURA MÍNIMA (50%)")
print("-" * 100)
print("  • Laura Reyes:   100% ≥ 50% ✅ CALIFICA")
print("  • Sandra Romero: 66.67% ≥ 50% ✅ CALIFICA")
print("\nAmbas ofertas califican para la evaluación")

# Rangos para normalización
print("\n📊 PASO 3: IDENTIFICAR RANGOS PARA NORMALIZACIÓN")
print("-" * 100)
print("Entre las ofertas calificadas:")
print("  • Precio mínimo:    $50,000 (Sandra)")
print("  • Precio máximo:    $80,000 (Laura)")
print("  • Tiempo mínimo:    2 días (Sandra)")
print("  • Tiempo máximo:    3 días (Laura)")
print("  • Garantía mínima:  3 meses (ambas)")
print("  • Garantía máxima:  3 meses (ambas)")

# Pesos configurados
print("\n⚖️  PASO 4: PESOS CONFIGURADOS EN EL SISTEMA")
print("-" * 100)
peso_precio = 0.50
peso_tiempo = 0.35
peso_garantia = 0.15
print(f"  • Peso Precio:    {peso_precio} (50%)")
print(f"  • Peso Tiempo:    {peso_tiempo} (35%)")
print(f"  • Peso Garantía:  {peso_garantia} (15%)")
print(f"  • Total:          {peso_precio + peso_tiempo + peso_garantia} (100%)")

# Cálculo para Sandra
print("\n🧮 PASO 5: NORMALIZACIÓN DE SCORES (Escala 0-1) - SANDRA ROMERO")
print("-" * 100)

# Score Precio
precio_sandra = 50000
precio_min = 50000
precio_max = 80000
print(f"\n5.1) Score Precio (menor es mejor - invertido):")
print(f"     Fórmula: (precio_max - precio_oferta) / (precio_max - precio_min)")
print(f"     Cálculo: ({precio_max} - {precio_sandra}) / ({precio_max} - {precio_min})")
print(f"     Cálculo: {precio_max - precio_sandra} / {precio_max - precio_min}")
score_precio_sandra = (precio_max - precio_sandra) / (precio_max - precio_min)
print(f"     Resultado: {score_precio_sandra:.4f}")
print(f"     ✅ Sandra tiene el MEJOR precio → Score = 1.0")

# Score Tiempo
tiempo_sandra = 2
tiempo_min = 2
tiempo_max = 3
print(f"\n5.2) Score Tiempo (menor es mejor - invertido):")
print(f"     Fórmula: (tiempo_max - tiempo_oferta) / (tiempo_max - tiempo_min)")
print(f"     Cálculo: ({tiempo_max} - {tiempo_sandra}) / ({tiempo_max} - {tiempo_min})")
print(f"     Cálculo: {tiempo_max - tiempo_sandra} / {tiempo_max - tiempo_min}")
score_tiempo_sandra = (tiempo_max - tiempo_sandra) / (tiempo_max - tiempo_min)
print(f"     Resultado: {score_tiempo_sandra:.4f}")
print(f"     ✅ Sandra tiene el MEJOR tiempo → Score = 1.0")

# Score Garantía
garantia_sandra = 3
garantia_min = 3
garantia_max = 3
print(f"\n5.3) Score Garantía (mayor es mejor):")
print(f"     Fórmula: (garantia_oferta - garantia_min) / (garantia_max - garantia_min)")
print(f"     Cálculo: ({garantia_sandra} - {garantia_min}) / ({garantia_max} - {garantia_min})")
print(f"     Cálculo: {garantia_sandra - garantia_min} / {garantia_max - garantia_min}")
if garantia_max == garantia_min:
    score_garantia_sandra = 1.0
    print(f"     ⚠️  Ambas ofertas tienen la misma garantía → Score = 1.0 (por defecto)")
else:
    score_garantia_sandra = (garantia_sandra - garantia_min) / (garantia_max - garantia_min)
    print(f"     Resultado: {score_garantia_sandra:.4f}")

# Puntaje total ponderado
print("\n🎯 PASO 6: CÁLCULO DEL PUNTAJE TOTAL PONDERADO (Escala 0-1)")
print("-" * 100)
print(f"Fórmula: (Score_Precio × Peso_Precio) + (Score_Tiempo × Peso_Tiempo) + (Score_Garantía × Peso_Garantía)")
print(f"\nCálculo para Sandra:")
print(f"  = ({score_precio_sandra:.4f} × {peso_precio}) + ({score_tiempo_sandra:.4f} × {peso_tiempo}) + ({score_garantia_sandra:.4f} × {peso_garantia})")

componente_precio = score_precio_sandra * peso_precio
componente_tiempo = score_tiempo_sandra * peso_tiempo
componente_garantia = score_garantia_sandra * peso_garantia

print(f"  = {componente_precio:.4f} + {componente_tiempo:.4f} + {componente_garantia:.4f}")

puntaje_total_sandra = componente_precio + componente_tiempo + componente_garantia
print(f"  = {puntaje_total_sandra:.4f}")

print(f"\nDesglose de contribución:")
print(f"  • Precio:    {componente_precio:.4f} ({componente_precio/puntaje_total_sandra*100:.1f}%)")
print(f"  • Tiempo:    {componente_tiempo:.4f} ({componente_tiempo/puntaje_total_sandra*100:.1f}%)")
print(f"  • Garantía:  {componente_garantia:.4f} ({componente_garantia/puntaje_total_sandra*100:.1f}%)")

# Conversión a escala 1-5
print("\n⭐ PASO 7: CONVERSIÓN A ESCALA DE 1 A 5")
print("-" * 100)
print(f"Fórmula: 1 + (puntaje_total × 4)")
print(f"Cálculo: 1 + ({puntaje_total_sandra:.4f} × 4)")
print(f"Cálculo: 1 + {puntaje_total_sandra * 4:.4f}")
puntaje_escala_5 = 1 + (puntaje_total_sandra * 4)
print(f"Resultado: {puntaje_escala_5:.2f}/5.00")

# Comparación con Laura
print("\n📊 PASO 8: COMPARACIÓN CON LAURA REYES")
print("-" * 100)

# Laura
precio_laura = 80000
tiempo_laura = 3
garantia_laura = 3

score_precio_laura = (precio_max - precio_laura) / (precio_max - precio_min)
score_tiempo_laura = (tiempo_max - tiempo_laura) / (tiempo_max - tiempo_min)
score_garantia_laura = 1.0

componente_precio_laura = score_precio_laura * peso_precio
componente_tiempo_laura = score_tiempo_laura * peso_tiempo
componente_garantia_laura = score_garantia_laura * peso_garantia

puntaje_total_laura = componente_precio_laura + componente_tiempo_laura + componente_garantia_laura
puntaje_escala_5_laura = 1 + (puntaje_total_laura * 4)

print(f"\nLaura Reyes:")
print(f"  • Score Precio:    {score_precio_laura:.4f} (peor precio)")
print(f"  • Score Tiempo:    {score_tiempo_laura:.4f} (peor tiempo)")
print(f"  • Score Garantía:  {score_garantia_laura:.4f} (igual garantía)")
print(f"  • Puntaje Total:   {puntaje_total_laura:.4f}")
print(f"  • Escala 1-5:      {puntaje_escala_5_laura:.2f}/5.00")

print(f"\nSandra Romero:")
print(f"  • Score Precio:    {score_precio_sandra:.4f} (mejor precio)")
print(f"  • Score Tiempo:    {score_tiempo_sandra:.4f} (mejor tiempo)")
print(f"  • Score Garantía:  {score_garantia_sandra:.4f} (igual garantía)")
print(f"  • Puntaje Total:   {puntaje_total_sandra:.4f}")
print(f"  • Escala 1-5:      {puntaje_escala_5:.2f}/5.00")

# Conclusión
print("\n" + "=" * 100)
print("🏆 CONCLUSIÓN")
print("=" * 100)
print(f"\nSandra Romero obtuvo {puntaje_escala_5:.2f}/5.00 porque:")
print(f"  ✅ Tiene el MEJOR precio ($50,000 vs $80,000 de Laura)")
print(f"  ✅ Tiene el MEJOR tiempo de entrega (2 días vs 3 días de Laura)")
print(f"  ✅ Tiene la MISMA garantía (3 meses)")
print(f"  ✅ Su cobertura (66.67%) cumple con el mínimo requerido (50%)")
print(f"\nAl tener los mejores valores en TODOS los criterios evaluados,")
print(f"Sandra obtiene el puntaje máximo normalizado de 1.0, que equivale a 5.00/5.00")
print(f"\n💰 Ahorro: ${precio_laura - precio_sandra:,} (${precio_laura:,} - ${precio_sandra:,})")
print("=" * 100)
