import os
import logging
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from api import app

if __name__ == "__main__":
    logger.info("🌐 Iniciando API no ambiente Fly.io")
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"🔌 Escutando em 0.0.0.0:{port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")