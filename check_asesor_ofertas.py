import asyncio
from tortoise import Tortoise
from models.user import Usuario, Asesor
from models.oferta import Oferta
from models.solicitud import Solicitud

async def check_ofertas():
    # Conectar a la base de datos
    await Tortoise.init(
        db_url="postgres://teloo_user:teloo_password@localhost:5432/teloo_marketplace",
        modules={"models": ["models.user", "models.oferta", "models.solicitud"]}
    )
    
    # Buscar el usuario
    email = "asesor006_1762827727@teloo.com"
    usuario = await Usuario.get_or_none(email=email)
    
    if not usuario:
        print(f"❌ Usuario {email} no encontrado")
        return
    
    print(f"✅ Usuario encontrado: {usuario.nombre} {usuario.apellido}")
    print(f"   ID: {usuario.id}")
    print(f"   Rol: {usuario.rol}")
    
    # Buscar el asesor
    asesor = await Asesor.get_or_none(usuario_id=usuario.id)
    
    if not asesor:
        print(f"❌ No es un asesor")
        return
    
    print(f"\n✅ Asesor encontrado:")
    print(f"   ID: {asesor.id}")
    print(f"   Nivel: {asesor.nivel}")
    
    # Buscar ofertas del asesor
    ofertas = await Oferta.filter(asesor_id=asesor.id).prefetch_related('solicitud')
    
    print(f"\n📊 Total de ofertas: {len(ofertas)}")
    
    for i, oferta in enumerate(ofertas, 1):
        print(f"\n--- Oferta {i} ---")
        print(f"ID: {oferta.id}")
        print(f"Estado oferta: {oferta.estado}")
        print(f"Solicitud ID: {oferta.solicitud_id}")
        print(f"Estado solicitud: {oferta.solicitud.estado}")
        print(f"Fecha creación: {oferta.created_at}")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_ofertas())
