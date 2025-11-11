"""
Test what pandas is reading from Excel
"""
import pandas as pd

df = pd.read_excel("data/asesores_250_ficticios.xlsx")

print("📊 Primeras 5 filas:")
print(df.head())

print("\n📋 Tipos de datos:")
print(df.dtypes)

print("\n📞 Primeros 5 teléfonos:")
for i, tel in enumerate(df['telefono'].head(), 1):
    print(f"   {i}. Valor: {tel} | Tipo: {type(tel)} | Repr: {repr(tel)}")
