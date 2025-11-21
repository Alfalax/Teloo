"""
Script para iniciar Telegram Long Polling
Ejecutar: python start_polling.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.telegram_polling import polling_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("🤖 TeLOO V3 - Telegram Bot (Long Polling Mode)")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📝 Instrucciones:")
    logger.info("   1. Asegúrate de tener TELEGRAM_BOT_TOKEN en .env")
    logger.info("   2. Envía mensajes a tu bot en Telegram")
    logger.info("   3. Presiona Ctrl+C para detener")
    logger.info("")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        await polling_service.start()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Stopping bot...")
        await polling_service.stop()
        logger.info("✅ Bot stopped successfully")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        await polling_service.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
