import os
import logging
import argparse
import sys
from datetime import datetime

from scraper import PrefeituraScraper
from uploader import FileUploader
from database import DatabaseManager

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
    logger.info(f"🚀 Iniciando processo completo às {start_time}")
    
    try:
        logger.info("🤖 Iniciando scraping do site da prefeitura...")
        scraper = PrefeituraScraper(headless=headless)
        publications = scraper.run()
        
        if not publications:
            logger.warning("⚠️ Nenhuma publicação encontrada. O processo será encerrado com sucesso, mas sem novos dados.")
            return True
        
        logger.info(f"✅ Scraping concluído. {len(publications)} publicações encontradas.")

        logger.info("☁️ Iniciando upload dos arquivos...")
        uploader = FileUploader()
        uploaded_publications = uploader.upload_multiple_files(publications)
        
        if not uploaded_publications:
            logger.error("❌ Nenhum arquivo foi enviado com sucesso. Encerrando com falha.")
            return False
        
        logger.info(f"✅ Upload concluído. {len(uploaded_publications)} arquivos enviados.")

        logger.info("💾 Iniciando armazenamento no banco de dados...")
        db_manager = DatabaseManager()
        saved_count = db_manager.save_publications(uploaded_publications)
        
        logger.info(f"✅ Armazenamento concluído. {saved_count} novas publicações salvas.")

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"🎉 Processo concluído com sucesso em {duration}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Erro fatal durante a execução do processo: {str(e)}", exc_info=True)
        sys.exit(1) # Garante que o contêiner Docker pare com um código de erro

def run_api_only():
    from api import app
    import uvicorn
    
    logger.info("🚀 Iniciando apenas a API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraping de publicações da Prefeitura de Natal")
    parser.add_argument("--api-only", action="store_true", help="Executa apenas a API")
    parser.add_argument("--no-headless", action="store_true", help="Executa o navegador em modo visível para depuração")
    
    args = parser.parse_args()
    
    if args.api_only:
        run_api_only()
    else:
        success = run_full_process(headless=not args.no_headless)
        if not success:
             logger.error("O processo de scraping falhou. Verifique os logs.")
             sys.exit(1)