import os
import re
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class PrefeituraScraper:
    BASE_URL = "https://www.natal.rn.gov.br/dom"
    DOWNLOAD_PATH = Path("downloads")

    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_download_path()
        
    def setup_download_path(self):
        self.DOWNLOAD_PATH.mkdir(exist_ok=True)
        logger.info(f"Diretório de downloads configurado: {self.DOWNLOAD_PATH}")

    def init_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        prefs = {
            "download.default_directory": str(self.DOWNLOAD_PATH.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Driver do Selenium inicializado com sucesso")

    def get_last_month_date_range(self):
        today = datetime.now()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
        
        return first_day_of_previous_month, last_day_of_previous_month

    def navigate_to_site(self):
        try:
            self.driver.get(self.BASE_URL)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.container"))
            )
            logger.info(f"Navegação para {self.BASE_URL} realizada com sucesso")
        except TimeoutException:
            logger.error("Timeout ao carregar a página principal")
            raise

    def set_date_filter(self, start_date, end_date):
        try:
            start_date_str = start_date.strftime("%d/%m/%Y")
            end_date_str = end_date.strftime("%d/%m/%Y")
            start_date_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "dataInicial"))
            )
            start_date_input.clear()
            start_date_input.send_keys(start_date_str)
            
            end_date_input = self.driver.find_element(By.ID, "dataFinal")
            end_date_input.clear()
            end_date_input.send_keys(end_date_str)
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
            search_button.click()
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table"))
            )
            
            logger.info(f"Filtro de datas configurado: {start_date_str} a {end_date_str}")
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Erro ao configurar filtro de datas: {str(e)}")
            raise

    def get_publication_links(self):
        publications = []
        try:
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table"))
            )
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        date_str = cells[0].text.strip()
                        title = cells[1].text.strip()

                        link_element = cells[2].find_element(By.TAG_NAME, "a")
                        link = link_element.get_attribute("href")
                        
                        publication_date = datetime.strptime(date_str, "%d/%m/%Y")
                        
                        publications.append({
                            "date": publication_date,
                            "competence": publication_date.strftime("%Y-%m"),
                            "title": title,
                            "link": link
                        })
                except Exception as e:
                    logger.warning(f"Erro ao processar linha da tabela: {str(e)}")
                    continue
            
            logger.info(f"Extraídos {len(publications)} links de publicações")
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Erro ao extrair links de publicações: {str(e)}")
        
        return publications

    def navigate_pagination(self):
        all_publications = []
        page = 1
        
        while True:
            logger.info(f"Processando página {page}")

            publications = self.get_publication_links()
            all_publications.extend(publications)
            
            try:
                next_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Próximo')]")
                if "disabled" in next_button.get_attribute("class"):
                    logger.info("Atingida a última página")
                    break
                
                next_button.click()
                WebDriverWait(self.driver, 10).until(
                    EC.staleness_of(next_button)
                )
                
                page += 1
                time.sleep(2) 
            except (TimeoutException, NoSuchElementException):
                logger.info("Não há mais páginas para navegar")
                break
        
        logger.info(f"Total de {len(all_publications)} publicações encontradas em {page} páginas")
        return all_publications

    def download_publication(self, publication):
        try:
            date_str = publication["date"].strftime("%Y-%m-%d")
            sanitized_title = re.sub(r'[^\w\s-]', '', publication["title"])
            sanitized_title = re.sub(r'[\s]+', '_', sanitized_title)
            filename = f"{date_str}_{sanitized_title[:50]}.pdf"
            file_path = self.DOWNLOAD_PATH / filename

            if file_path.exists():
                logger.info(f"Arquivo já existe: {filename}")
                return str(file_path)

            self.driver.get(publication["link"])

            time.sleep(3)

            downloads = list(self.DOWNLOAD_PATH.glob("*.pdf"))
            
            if downloads:
                latest_download = max(downloads, key=os.path.getctime)

                new_path = self.DOWNLOAD_PATH / filename
                latest_download.rename(new_path)
                
                logger.info(f"Download concluído: {filename}")
                return str(new_path)
            
            logger.warning(f"Não foi possível confirmar o download: {publication['title']}")
            return None
        except Exception as e:
            logger.error(f"Erro ao baixar publicação: {str(e)}")
            return None

    def run(self):
        try:
            self.init_driver()
            self.navigate_to_site()
            first_day, last_day = self.get_last_month_date_range()
            self.set_date_filter(first_day, last_day)

            publications = self.navigate_pagination()

            result = []
            for i, pub in enumerate(publications):
                logger.info(f"Baixando publicação {i+1}/{len(publications)}: {pub['title']}")
                file_path = self.download_publication(pub)
                
                if file_path:
                    pub["file_path"] = file_path
                    result.append(pub)
                
                time.sleep(1)
            
            logger.info(f"Processo de scraping concluído. {len(result)} arquivos baixados.")
            return result
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver do Selenium encerrado")

if __name__ == "__main__":
    scraper = PrefeituraScraper(headless=False)
    publications = scraper.run()

    for pub in publications:
        print(f"Data: {pub['date'].strftime('%d/%m/%Y')}")
        print(f"Título: {pub['title']}")
        print(f"Arquivo: {pub['file_path']}")
        print("-" * 50)