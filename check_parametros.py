import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='teloo_db',
    user='teloo_user',
    password='teloo_password'
)

cur = conn.cursor()
cur.execute("""
    SELECT clave, categoria, nombre, tipo_dato 
    FROM parametros_configuracion 
    ORDER BY categoria, clave
""")

print("PARAMETROS EXISTENTES EN LA BASE DE DATOS:")
print("=" * 80)

current_category = None
for row in cur.fetchall():
    clave, categoria, nombre, tipo_dato = row
    if categoria != current_category:
        print(f"\n[{categoria}]")
        current_category = categoria
    print(f"  - {clave} ({tipo_dato}): {nombre}")

cur.close()
conn.close()
