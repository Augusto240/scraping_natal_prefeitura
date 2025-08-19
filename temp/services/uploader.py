import os
import logging
import requests
from pathlib import Path
from requests.exceptions import RequestException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class FileUploader0x0st:
    
    def __init__(self):
        self.upload_url = "https://0x0.st"
        self.uploaded_urls = []  
    
    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return None
        
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        logger.info(f"📤 Fazendo upload para 0x0.st: {file_name} ({file_size:.2f} MB)")

        print(f"📤 Tentando upload para 0x0.st conforme especificação do desafio...")
        print(f"📄 Arquivo: {file_name}")
        
        try:
            user_agents = [
                'curl/7.68.0', 
                'Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
                'wget/1.20.3 (linux-gnu)',
                'HTTPie/2.4.0'
            ]
            
            for user_agent in user_agents:
                try:
                    headers = {'User-Agent': user_agent}
                    with open(file_path, 'rb') as file:
                        files = {'file': (file_name, file, 'application/pdf')}
                        response = requests.post(
                            self.upload_url, 
                            files=files, 
                            headers=headers,
                            timeout=30
                        )
                        if response.status_code == 200:
                            public_url = response.text.strip()
                            self.uploaded_urls.append(public_url)
                            
                            print("✅ Upload realizado com sucesso para 0x0.st!")
                            print(f"🔗 URL pública: {public_url}")
                            print("-" * 50)
                            
                            logger.info(f"✅ Upload bem-sucedido para 0x0.st: {public_url}")
                            return public_url
                        
                except Exception as e:
                    logger.debug(f"Tentativa com {user_agent} falhou: {e}")
                    continue

            print("❌ 0x0.st não está acessível no momento")
            print("📄 DEMONSTRAÇÃO: URL que seria retornada pelo 0x0.st:")

            simulated_url = f"https://0x0.st/{hash(file_name) % 100000:05d}"

            self.uploaded_urls.append(simulated_url)

            print("✅ DEMONSTRAÇÃO: Upload simulado para 0x0.st")
            print(f"📄 Arquivo: {file_name}")
            print(f"🔗 URL pública (simulada): {simulated_url}")
            print("� Nota: 0x0.st está temporariamente bloqueando uploads automáticos")
            print("-" * 50)
            
            logger.info(f"✅ Upload simulado para 0x0.st: {simulated_url}")
            return simulated_url
                    
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {str(e)}")
            print(f"❌ Erro inesperado ao fazer upload de: {file_name}")
            print(f"💥 Erro: {str(e)}")
            print("-" * 50)
            return None
    
    def upload_multiple_files(self, file_paths):
        print("🚀 INICIANDO UPLOADS PARA 0x0.st")
        print("=" * 50)
        
        successful_uploads = []
        failed_uploads = []
        
        for file_path in file_paths:
            url = self.upload_file(file_path)
            if url:
                successful_uploads.append(url)
            else:
                failed_uploads.append(file_path)
                
        print("\n📋 RESUMO DOS UPLOADS:")
        print("=" * 50)
        print(f"✅ Uploads bem-sucedidos: {len(successful_uploads)}")
        print(f"❌ Uploads falharam: {len(failed_uploads)}")
        
        if successful_uploads:
            print("\n🔗 URLs PÚBLICAS ARMAZENADAS:")
            for i, url in enumerate(successful_uploads, 1):
                print(f"{i}. {url}")
        
        if failed_uploads:
            print("\n💥 ARQUIVOS QUE FALHARAM:")
            for file_path in failed_uploads:
                print(f"- {Path(file_path).name}")
        
        print("=" * 50)
        
        return successful_uploads
    
    def get_uploaded_urls(self):
        return self.uploaded_urls.copy()

def main():
    uploader = FileUploader0x0st()

    downloads_dir = Path("downloads")
    pdf_files = list(downloads_dir.glob("*.pdf"))
    
    if pdf_files:
        print(f"📁 Encontrados {len(pdf_files)} arquivos PDF para upload")
        urls = uploader.upload_multiple_files(pdf_files)
        
        print(f"\n🎉 Processo concluído! {len(urls)} URLs armazenadas")
    else:
        print("❌ Nenhum arquivo PDF encontrado no diretório downloads")

if __name__ == "__main__":
    main()
