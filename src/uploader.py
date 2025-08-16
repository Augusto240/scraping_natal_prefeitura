import os
import logging
from pathlib import Path
import time
import random

import requests
from requests.exceptions import RequestException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class FileUploader:
    UPLOAD_URL = "https://0x0.st"
    
    def __init__(self, max_retries=3, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return None
        
        file_size = os.path.getsize(file_path) / (1024 * 1024) 
        logger.info(f"Iniciando upload do arquivo: {os.path.basename(file_path)} ({file_size:.2f} MB)")
        file_name = os.path.basename(file_path)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                with open(file_path, 'rb') as file:
                    files = {'file': (file_name, file, 'application/pdf')}
                    response = requests.post(
                        self.UPLOAD_URL,
                        files=files,
                        timeout=120
                    )

                    response.raise_for_status()
                    file_url = response.text.strip()
                    
                    logger.info(f"Upload bem-sucedido: {file_url}")
                    return file_url
                    
            except RequestException as e:
                logger.warning(f"Tentativa {attempt}/{self.max_retries} falhou: {str(e)}")
                
                if attempt < self.max_retries:
                    jitter = random.uniform(0.5, 1.5)
                    wait_time = self.retry_delay * jitter
                    logger.info(f"Aguardando {wait_time:.2f}s antes de tentar novamente")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Falha no upload após {self.max_retries} tentativas: {file_path}")
                    return None
    
    def upload_multiple_files(self, publications):
        result = []
        
        for i, pub in enumerate(publications):
            if "file_path" not in pub:
                logger.warning(f"Publicação sem caminho de arquivo: {pub.get('title', 'Unknown')}")
                continue
                
            logger.info(f"Processando upload {i+1}/{len(publications)}: {os.path.basename(pub['file_path'])}")
            file_url = self.upload_file(pub["file_path"])
            
            if file_url:
                pub_copy = pub.copy()
                pub_copy["file_url"] = file_url
                result.append(pub_copy)

                print(f"Arquivo: {os.path.basename(pub['file_path'])}")
                print(f"URL: {file_url}")
                print("-" * 50)
            
            time.sleep(1)
        
        logger.info(f"Upload concluído para {len(result)}/{len(publications)} arquivos")
        return result

if __name__ == "__main__":
    uploader = FileUploader()
    test_file = Path("downloads/exemplo.pdf")
    
    if test_file.exists():
        url = uploader.upload_file(str(test_file))
        print(f"URL do arquivo: {url}")
    else:
        print(f"Arquivo de teste não encontrado: {test_file}")