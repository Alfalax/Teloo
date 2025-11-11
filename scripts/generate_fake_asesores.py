"""
Script para generar 250 asesores ficticios para pruebas del sistema de escalamiento
Distribuidos en ciudades principales y secundarias de Colombia
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'services' / 'core-api'))

from tortoise import Tortoise
from passlib.context import CryptContext
import random
from datetime import datetime, timedelta

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


async def init_db():
    """Initialize database connection"""
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_db",
        modules={"models": ["models.user", "models.geografia", "models.solicitud", "models.oferta", "models.analytics"]}
    )
    await Tortoise.generate_schemas()


async def generate_asesores():
    """Generate 250 fake asesores"""
    from models.user import Usuario, Asesor
    from models.enums import RolUsuario, EstadoUsuario, EstadoAsesor
    from models.geografia import Municipio
    
    print("🚀 Iniciando generación de 250 asesores ficticios...")
    
    # Password única para todos
    password_hash = pwd_context.hash("Teloo2024!")
    
    # Distribuir asesores
    num_principales = int(250 * 0.6)  # 150 asesores
    num_secundarias = 250 - num_principales  # 100 asesores
    
    asesores_creados = 0
    errores = 0
    
    # Generar asesores para ciudades principales
    print(f"\n📍 Generando {num_principales} asesores en ciudades principales...")
    for i in range(num_principales):
        try:
            ciudad, departamento = random.choice(CIUDADES_PRINCIPALES)
            await create_asesor(i + 1, ciudad, departamento, password_hash)
            asesores_creados += 1
            if (i + 1) % 50 == 0:
                print(f"   ✓ {i + 1} asesores creados...")
        except Exception as e:
            print(f"   ✗ Error creando asesor {i + 1}: {e}")
            errores += 1
    
    # Generar asesores para ciudades secundarias
    print(f"\n📍 Generando {num_secundarias} asesores en ciudades secundarias...")
    for i in range(num_secundarias):
        try:
            ciudad, departamento = random.choice(CIUDADES_SECUNDARIAS)
            await create_asesor(num_principales + i + 1, ciudad, departamento, password_hash)
            asesores_creados += 1
            if (i + 1) % 50 == 0:
                print(f"   ✓ {num_principales + i + 1} asesores creados...")
        except Exception as e:
            print(f"   ✗ Error creando asesor {num_principales + i + 1}: {e}")
            errores += 1
    
    print(f"\n✅ Proceso completado:")
    print(f"   • Asesores creados: {asesores_creados}")
    print(f"   • Errores: {errores}")
    print(f"   • Contraseña para todos: Teloo2024!")


async def create_asesor(numero: int, ciudad: str, departamento: str, password_hash: str):
    """Create a single asesor"""
    from models.user import Usuario, Asesor
    from models.enums import RolUsuario, EstadoUsuario, EstadoAsesor
    from models.geografia import Municipio
    
    # Generar datos
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    email = f"asesor{numero:03d}@teloo.com"
    telefono = f"+57300{1234000 + numero}"
    
    # Normalizar ciudad para búsqueda
    ciudad_norm = Municipio.normalizar_ciudad(ciudad)
    
    # Punto de venta
    punto_venta_template = random.choice(PUNTOS_VENTA)
    punto_venta = punto_venta_template.format(nombre=nombre, apellido=apellido)
    
    # Dirección ficticia
    direccion = f"Calle {random.randint(10, 100)} #{random.randint(10, 50)}-{random.randint(10, 99)}"
    
    # Crear usuario
    usuario = await Usuario.create(
        email=email,
        password_hash=password_hash,
        nombre=nombre,
        apellido=apellido,
        telefono=telefono,
        rol=RolUsuario.ADVISOR,
        estado=EstadoUsuario.ACTIVO
    )
    
    # Crear asesor
    asesor = await Asesor.create(
        usuario=usuario,
        ciudad=ciudad_norm,
        departamento=departamento,
        punto_venta=punto_venta,
        direccion_punto_venta=direccion,
        estado=EstadoAsesor.ACTIVO
    )
    
    return asesor


async def main():
    """Main execution"""
    try:
        await init_db()
        await generate_asesores()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
