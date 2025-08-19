import os
import logging
import argparse
import sys
from datetime import datetime

from scraper import PrefeituraScraper
from uploader import FileUploader0x0st  
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
        logger.info("🔍 Iniciando scraping do site da prefeitura")
        scraper = PrefeituraScraper(headless=headless)
        publications = scraper.run()
        
        if not publications:
            logger.warning("⚠️ Nenhuma publicação encontrada")
            return True
        
        logger.info(f"✅ Scraping concluído. {len(publications)} publicações encontradas")

        logger.info("📤 Iniciando upload dos arquivos para 0x0.st")
        uploader = FileUploader0x0st()
        
        file_paths = [pub.get('file_path') for pub in publications if pub.get('file_path')]
        
        if not file_paths:
            logger.warning("⚠️ Nenhum arquivo encontrado para upload")
            return False
 
        uploaded_urls = uploader.upload_multiple_files(file_paths)
        
        if not uploaded_urls:
            logger.warning("⚠️ Nenhum arquivo foi enviado com sucesso para 0x0.st")
            return False

        for i, pub in enumerate(publications):
            if i < len(uploaded_urls):
                pub['file_url'] = uploaded_urls[i]
        
        logger.info(f"✅ Upload concluído. {len(uploaded_urls)} arquivos enviados para 0x0.st")

        logger.info("💾 Iniciando armazenamento no banco de dados")
        try:
            db_manager = DatabaseManager()
            saved_count = db_manager.save_publications(publications)
            logger.info(f"✅ Armazenamento concluído. {saved_count} publicações salvas")
        except Exception as db_error:
            logger.warning(f"⚠️ Erro no banco de dados: {str(db_error)}")
            logger.info("📋 Continuando sem salvar no banco - dados disponíveis em memória")
            saved_count = len(publications)

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"🎉 Processo concluído com sucesso em {duration}")
        
        return True
                
    except Exception as e:
        logger.error(f"❌ Erro durante a execução do processo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_api_only():
    try:
        logger.info("🌐 Iniciando apenas a API")

        try:
            import uvicorn
            port = int(os.environ.get("PORT", "8000"))
            uvicorn.run("api:app", host="0.0.0.0", port=port)  # Formato correto: "module:app"
        except ImportError:
            logger.warning("⚠️ Uvicorn não encontrado, tentando executar com servidor simples")
            print("Para executar a API, instale uvicorn: pip install uvicorn")
            print("Então execute: uvicorn api:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar a API: {str(e)}")
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
        success = run_full_process(headless=not args.no_headless)
        if success:
            print("\n🎉 PROCESSO CONCLUÍDO COM SUCESSO! 🎉")
        else:
            print("\n❌ PROCESSO FALHOU - Verifique os logs acima")
            sys.exit(1)