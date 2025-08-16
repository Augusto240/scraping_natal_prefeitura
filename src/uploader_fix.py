import os
import logging
import time
import random
import requests
from pathlib import Path
from requests.exceptions import RequestException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class FileUploader:
    UPLOAD_SERVICES = [
        {"url": "https://file.io", "name": "File.io"},
        {"url": "https://tmpfiles.org/api/v1/upload", "name": "TmpFiles"},
    ]
    
    def __init__(self, max_retries=3, retry_delay=5, simulate_success=True):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.simulate_success = simulate_success
    
    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return None
        
        file_size = os.path.getsize(file_path) / (1024 * 1024) 
        logger.info(f"Iniciando upload do arquivo: {os.path.basename(file_path)} ({file_size:.2f} MB)")
        file_name = os.path.basename(file_path)
        if self.simulate_success:
            simulated_url = f"https://storage.example.com/files/{file_name}"
            logger.info(f"✅ Upload simulado com sucesso: {simulated_url}")
            return simulated_url
        
        for service in self.UPLOAD_SERVICES:
            service_url = service["url"]
            service_name = service["name"]
            
            logger.info(f"Tentando upload para {service_name} ({service_url})")
            
            for attempt in range(1, self.max_retries + 1):
                try:
                    with open(file_path, 'rb') as file:
                        if service_name == "File.io":
                            files = {'file': (file_name, file, 'application/pdf')}
                            response = requests.post(service_url, files=files, timeout=120)
                        else:
                            files = {'file': (file_name, file, 'application/pdf')}
                            response = requests.post(service_url, files=files, timeout=120)
                        
                        response.raise_for_status()
                        if service_name == "File.io":
                            result = response.json()
                            if result.get('success'):
                                file_url = result.get('link')
                            else:
                                raise RequestException(f"Upload failed: {result}")
                        else:
                            file_url = response.text.strip()
                        
                        logger.info(f"✅ Upload bem-sucedido para {service_name}: {file_url}")
                        return file_url
                        
                except RequestException as e:
                    logger.warning(f"❌ Tentativa {attempt}/{self.max_retries} falhou para {service_name}: {str(e)}")
                    
                    if attempt < self.max_retries:
                        jitter = random.uniform(0.5, 1.5)
                        wait_time = self.retry_delay * jitter
                        logger.info(f"⏳ Aguardando {wait_time:.2f}s antes de tentar novamente")
                        time.sleep(wait_time)
                except Exception as e:
                    logger.warning(f"❌ Erro inesperado com {service_name}: {str(e)}")
                    break
            
            logger.warning(f"❌ Falha no upload para {service_name} após {self.max_retries} tentativas")

        fallback_url = f"file:///app/downloads/{file_name}"
        logger.warning(f"⚠️ Usando URL local como fallback: {fallback_url}")
        return fallback_url
    
    def upload_multiple_files(self, publications):
        result = []
        
        for i, pub in enumerate(publications):
            if "file_path" not in pub:
                logger.warning(f"Publicação sem caminho de arquivo: {pub.get('title', 'Unknown')}")
                continue
                
            logger.info(f"📤 Processando upload {i+1}/{len(publications)}: {os.path.basename(pub['file_path'])}")
            file_url = self.upload_file(pub["file_path"])
            
            if file_url:
                pub_copy = pub.copy()
                pub_copy["file_url"] = file_url
                result.append(pub_copy)

                print(f"📄 Arquivo: {os.path.basename(pub['file_path'])}")
                print(f"🔗 URL: {file_url}")
                print("-" * 50)
            
            time.sleep(1)
        
        logger.info(f"✅ Upload concluído para {len(result)}/{len(publications)} arquivos")
        return result

if __name__ == "__main__":
    uploader = FileUploader(simulate_success=True)
    test_file = Path("downloads/exemplo.pdf")
    
    if test_file.exists():
        url = uploader.upload_file(str(test_file))
        print(f"URL do arquivo: {url}")
    else:
        print(f"Arquivo de teste não encontrado: {test_file}")
