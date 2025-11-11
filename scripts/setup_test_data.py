"""
Script maestro para configurar datos de prueba completos
Ejecuta generación de asesores y datos históricos
"""

import asyncio
import subprocess
import sys
from pathlib import Path

def run_script(script_name: str) -> bool:
    """Run a Python script and return success status"""
    script_path = Path(__file__).parent / script_name
    
    print(f"\n{'='*60}")
    print(f"Ejecutando: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error ejecutando {script_name}")
        return False


def main():
    """Main execution"""
    print("🎯 CONFIGURACIÓN DE DATOS DE PRUEBA PARA ESCALAMIENTO")
    print("="*60)
    print("Este script generará:")
    print("  • 250 asesores ficticios")
    print("  • Datos históricos de actividad")
    print("  • Métricas para algoritmo de escalamiento")
    print("="*60)
    
    input("\n⏸️  Presiona ENTER para continuar o Ctrl+C para cancelar...")
    
    # Step 1: Generate asesores
    if not run_script("generate_fake_asesores.py"):
        print("\n❌ Falló la generación de asesores. Abortando.")
        return
    
    # Step 2: Generate historical data
    if not run_script("generate_historical_data.py"):
        print("\n⚠️  Falló la generación de datos históricos, pero asesores fueron creados.")
        print("   Puedes continuar, pero las métricas de escalamiento serán limitadas.")
    
    print("\n" + "="*60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("="*60)
    print("\n📋 Credenciales de acceso:")
    print("   • Emails: asesor001@teloo.com hasta asesor250@teloo.com")
    print("   • Contraseña: Teloo2024!")
    print("\n🎯 Próximos pasos:")
    print("   1. Crea una solicitud desde el admin")
    print("   2. El sistema ejecutará escalamiento automático")
    print("   3. Los asesores verán la solicitud en su dashboard")
    print("   4. Podrán hacer ofertas según su nivel asignado")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
