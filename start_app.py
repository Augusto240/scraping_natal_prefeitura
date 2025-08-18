import os
import sys
import traceback
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("startup")

logger.info(f"Python version: {sys.version}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Directory listing: {os.listdir('.')}")
if os.path.exists("app"):
    logger.info(f"App directory contents: {os.listdir('app')}")

sys.path.insert(0, os.getcwd())
logger.info(f"Python path: {sys.path}")

try:
    logger.info("Tentando importar a aplicação FastAPI...")
    from app.api import app
    logger.info("Importação bem-sucedida!")
    
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Iniciando servidor na porta {port}...")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
    
except Exception as e:
    logger.error(f"ERRO AO INICIAR APLICAÇÃO: {str(e)}")
    logger.error(traceback.format_exc())
    logger.info("Tentando abordagem alternativa com módulo uvicorn...")
    try:
        import uvicorn
        uvicorn.run("app.api:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
    except Exception as e2:
        logger.error(f"ERRO NA ABORDAGEM ALTERNATIVA: {str(e2)}")
        logger.error(traceback.format_exc())
        sys.exit(1)