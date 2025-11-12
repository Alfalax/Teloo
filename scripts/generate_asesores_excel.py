"""
Script para generar archivo Excel con 250 asesores ficticios
Para importar desde el dashboard administrativo
"""

import pandas as pd
import random
from pathlib import Path
from datetime import datetime

# Ciudades principales (60% de asesores)
CIUDADES_PRINCIPALES = [
    ("Bogotá", "Bogotá D.C."),
    ("Medellín", "Antioquia"),
    ("Cali", "Valle del Cauca"),
    ("Barranquilla", "Atlántico"),
    ("Cartagena", "Bolívar"),
]

# Ciudades secundarias (40% de asesores)
CIUDADES_SECUNDARIAS = [
    ("Bucaramanga", "Santander"),
    ("Pereira", "Risaralda"),
    ("Manizales", "Caldas"),
    ("Ibagué", "Tolima"),
    ("Cúcuta", "Norte de Santander"),
    ("Villavicencio", "Meta"),
    ("Pasto", "Nariño"),
    ("Santa Marta", "Magdalena"),
    ("Montería", "Córdoba"),
    ("Neiva", "Huila"),
]

# Nombres colombianos comunes
NOMBRES = [
    "Juan", "Carlos", "Luis", "José", "Miguel", "Pedro", "Jorge", "Andrés", "David", "Daniel",
    "María", "Ana", "Laura", "Carolina", "Claudia", "Diana", "Paula", "Sandra", "Mónica", "Andrea",
    "Alejandro", "Fernando", "Ricardo", "Roberto", "Francisco", "Javier", "Sergio", "Camilo", "Santiago", "Sebastián",
    "Valentina", "Isabella", "Sofía", "Camila", "Daniela", "Natalia", "Juliana", "Paola", "Marcela", "Adriana"
]

APELLIDOS = [
    "García", "Rodríguez", "Martínez", "Hernández", "López", "González", "Pérez", "Sánchez", "Ramírez", "Torres",
    "Flores", "Rivera", "Gómez", "Díaz", "Cruz", "Morales", "Reyes", "Gutiérrez", "Ortiz", "Jiménez",
    "Vargas", "Castro", "Romero", "Álvarez", "Ruiz", "Mendoza", "Moreno", "Castillo", "Herrera", "Medina"
]

# Puntos de venta típicos
PUNTOS_VENTA = [
    "Repuestos {apellido}",
    "Autopartes {apellido}",
    "Almacén {nombre}",
    "Repuestos y Accesorios {apellido}",
    "Casa de Repuestos {nombre}",
    "Distribuidora {apellido}",
    "Autorepuestos {nombre}",
    "Comercializadora {apellido}",
]


def generate_asesores_data(num_asesores=250):
    """Generate data for asesores"""
    data = []
    
    # Distribuir asesores
    num_principales = int(num_asesores * 0.6)  # 150 asesores
    num_secundarias = num_asesores - num_principales  # 100 asesores
    
    # Generar asesores para ciudades principales
    for i in range(num_principales):
        ciudad, departamento = random.choice(CIUDADES_PRINCIPALES)
        asesor = generate_asesor(i + 1, ciudad, departamento)
        data.append(asesor)
    
    # Generar asesores para ciudades secundarias
    for i in range(num_secundarias):
        ciudad, departamento = random.choice(CIUDADES_SECUNDARIAS)
        asesor = generate_asesor(num_principales + i + 1, ciudad, departamento)
        data.append(asesor)
    
    return data


def generate_asesor(numero, ciudad, departamento):
    """Generate a single asesor"""
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    # Use timestamp to make emails unique
    timestamp = int(datetime.now().timestamp())
    email = f"asesor{numero:03d}_{timestamp}@teloo.com"
    # Colombian phone format: +57 + 10 digits (3XXXXXXXXX)
    # Generate 10-digit number starting with 3
    phone_number = 3000000000 + numero
    telefono = f"+57{phone_number}"
    
    # Punto de venta
    punto_venta_template = random.choice(PUNTOS_VENTA)
    punto_venta = punto_venta_template.format(nombre=nombre, apellido=apellido)
    
    # Dirección ficticia
    direccion = f"Calle {random.randint(10, 100)} #{random.randint(10, 50)}-{random.randint(10, 99)}"
    
    # Password (opcional - si no se proporciona, el sistema genera una)
    password = "Teloo2024!"
    
    return {
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "telefono": telefono,
        "ciudad": ciudad,
        "departamento": departamento,
        "punto_venta": punto_venta,
        "direccion_punto_venta": direccion,
        "password": password
    }


def main():
    """Main execution"""
    print("🚀 Generando archivo Excel con 250 asesores ficticios...")
    
    # Generate data
    asesores_data = generate_asesores_data(250)
    
    # Create DataFrame
    df = pd.DataFrame(asesores_data)
    
    # Define output path
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "asesores_250_ficticios.xlsx"
    
    # Save to Excel with proper formatting for phone numbers
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Asesores")
        
        # Format phone column as text to preserve leading +
        worksheet = writer.sheets['Asesores']
        for row in range(2, len(df) + 2):  # Start from row 2 (after header)
            cell = worksheet[f'D{row}']  # Column D is telefono
            cell.number_format = '@'  # Text format
    
    print(f"\n✅ Archivo generado exitosamente:")
    print(f"   📁 Ubicación: {output_file}")
    print(f"   📊 Total asesores: {len(asesores_data)}")
    print(f"\n📋 Columnas incluidas:")
    print(f"   • nombre, apellido, email, telefono")
    print(f"   • ciudad, departamento")
    print(f"   • punto_venta, direccion_punto_venta")
    print(f"   • password (Teloo2024! para todos)")
    print(f"\n🎯 Próximos pasos:")
    print(f"   1. Abre el dashboard administrativo")
    print(f"   2. Ve a la sección 'Asesores'")
    print(f"   3. Haz clic en 'Importar desde Excel'")
    print(f"   4. Selecciona el archivo: {output_file.name}")
    print(f"   5. ¡Listo! Los 250 asesores se importarán automáticamente")
    print(f"\n🔑 Credenciales de acceso:")
    print(f"   • Emails: asesor001@teloo.com hasta asesor250@teloo.com")
    print(f"   • Contraseña: Teloo2024!")


if __name__ == "__main__":
    main()
