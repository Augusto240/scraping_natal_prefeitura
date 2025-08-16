import os
import logging
import argparse
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("natal_scraping.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_full_process(headless=True):
    start_time = datetime.now()
    logger.info(f"Iniciando processo completo às {start_time}")
    
    try:
        try:
            from scraper_fix import PrefeituraScraper
            from uploader_fix import FileUploader
            from database import DatabaseManager
        except ImportError as e:
            logger.error(f"Erro ao importar módulos: {str(e)}")
            return False
        logger.info("Iniciando scraping do site da prefeitura")
        scraper = PrefeituraScraper(headless=headless)
        publications = scraper.run()
        
        if not publications:
            logger.warning("Nenhuma publicação encontrada")
            return False
        
        logger.info(f"Scraping concluído. {len(publications)} publicações encontradas")
        
        logger.info("Iniciando upload dos arquivos")
        uploader = FileUploader(simulate_success=True)  
        uploaded_publications = uploader.upload_multiple_files(publications)
        
        if not uploaded_publications:
            logger.warning("Nenhum arquivo foi enviado com sucesso")
            return False
        
        logger.info(f"Upload concluído. {len(uploaded_publications)} arquivos enviados")

        logger.info("Iniciando armazenamento no banco de dados")
        db_manager = DatabaseManager()
        saved_count = db_manager.save_publications(uploaded_publications)
        
        logger.info(f"Armazenamento concluído. {saved_count} publicações salvas")

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Processo concluído com sucesso em {duration}")
        
        return True
    
    except Exception as e:
        logger.error(f"Erro durante a execução do processo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_api_only():
    try:
        from api import app
        import uvicorn
        
        logger.info("Iniciando apenas a API")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Erro ao iniciar a API: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraping de publicações da Prefeitura de Natal")
    parser.add_argument("--api-only", action="store_true", help="Executa apenas a API")
    parser.add_argument("--no-headless", action="store_true", help="Executa o navegador em modo visível")
    
    args = parser.parse_args()
    
    if args.api_only:
        run_api_only()
    else:
        run_full_process(headless=not args.no_headless)