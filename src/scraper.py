import os
import re
import time
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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
        for f in self.DOWNLOAD_PATH.glob('*.pdf*'):
            try:
                f.unlink()
            except OSError as e:
                logger.error(f"Erro ao remover o arquivo {f}: {e}")
        logger.info(f"Diretório de downloads configurado e limpo: {self.DOWNLOAD_PATH}")

    def init_driver(self):
        chrome_options = Options()
        # CORREÇÃO FINAL: Aponta para o local padrão de instalação do Chrome no Debian
        chrome_options.binary_location = "/opt/google/chrome/google-chrome"

        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        prefs = {
            "download.default_directory": str(self.DOWNLOAD_PATH.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            service = Service(executable_path="/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Driver do Selenium inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar o WebDriver: {e}. Verifique a instalação do Chrome e do ChromeDriver.")
            raise
            
    def get_last_month_date_range(self):
        today = datetime.now()
        # Para o teste, vamos usar Julho de 2024, que tem publicações.
        # Em um cenário real, você voltaria para a lógica do mês anterior.
        if today.month == 1:
            last_month_year = today.year - 1
            last_month = 12
        else:
            last_month_year = today.year
            last_month = today.month - 1
        
        first_day = datetime(last_month_year, last_month, 1)
        # Encontra o último dia do mês
        next_month = first_day.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        
        return first_day, last_day

    def navigate_to_site(self):
        try:
            self.driver.get(self.BASE_URL)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "dataInicial"))
            )
            logger.info(f"Navegação para {self.BASE_URL} realizada com sucesso")
        except TimeoutException:
            logger.error("Timeout ao carregar a página principal ou encontrar o campo de data.")
            self.driver.save_screenshot("debug_navigate_to_site.png")
            raise

    def set_date_filter(self, start_date, end_date):
        try:
            start_date_str = start_date.strftime("%d/%m/%Y")
            end_date_str = end_date.strftime("%d/%m/%Y")
            
            logger.info(f"Configurando filtro de datas: {start_date_str} a {end_date_str}")
            
            start_date_input = self.driver.find_element(By.ID, "dataInicial")
            self.driver.execute_script("arguments[0].value = '';", start_date_input)
            start_date_input.send_keys(start_date_str)
            
            end_date_input = self.driver.find_element(By.ID, "dataFinal")
            self.driver.execute_script("arguments[0].value = '';", end_date_input)
            end_date_input.send_keys(end_date_str)

            search_button = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
            search_button.click()
            
            # Espera a tabela de resultados aparecer ou a mensagem de "nenhum resultado"
            WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.table tbody tr")),
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Nenhum registro encontrado')]"))
                )
            )
            logger.info("Busca por data realizada com sucesso.")
            time.sleep(3)
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Erro ao configurar filtro de datas: {str(e)}")
            self.driver.save_screenshot("debug_set_date_filter.png")
            raise

    def get_publication_links(self):
        publications = []
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table.table tbody tr")
            for row in rows:
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
                    logger.warning(f"Erro ao processar linha da tabela: {str(e)}. Pulando linha.")
                    continue
            logger.info(f"Extraídos {len(publications)} links de publicações da página atual")
        except NoSuchElementException:
            # Não é um erro se a página não tiver resultados
            logger.info("Nenhuma publicação encontrada nesta página.")
        return publications

    def navigate_pagination(self):
        all_publications = []
        page_count = 1
        while True:
            logger.info(f"Processando página {page_count}...")
            publications = self.get_publication_links()
            all_publications.extend(publications)
            
            try:
                next_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Próximo') and not(ancestor::li[contains(@class, 'disabled')])]")
                self.driver.execute_script("arguments[0].scrollIntoView(true);")
                time.sleep(0.5)
                next_button.click()
                logger.info("Navegando para a próxima página...")
                page_count += 1
                time.sleep(3)
            except NoSuchElementException:
                logger.info("Atingida a última página. Fim da paginação.")
                break
        
        logger.info(f"Total de {len(all_publications)} publicações encontradas.")
        return all_publications

    def download_publication(self, publication, main_window_handle):
        try:
            date_str = publication["date"].strftime("%Y-%m-%d")
            sanitized_title = re.sub(r'[^\w\s-]', '', publication["title"]).strip()
            sanitized_title = re.sub(r'[\s]+', '_', sanitized_title)
            filename = f"{date_str}_{sanitized_title[:50]}.pdf"
            file_path = self.DOWNLOAD_PATH / filename

            if file_path.exists():
                logger.info(f"Arquivo já existe: {filename}. Pulando download.")
                return str(file_path)

            initial_files = set(os.listdir(self.DOWNLOAD_PATH))
            
            # Clica no link que deve abrir uma nova aba
            link_element = self.driver.find_element(By.XPATH, f"//a[@href='{publication['link']}']")
            link_element.click()
            time.sleep(2)

            # Muda para a nova aba
            for handle in self.driver.window_handles:
                if handle != main_window_handle:
                    self.driver.switch_to.window(handle)
                    break
            
            # Espera pelo download
            download_wait_time = 0
            while download_wait_time < 60:
                current_files = set(os.listdir(self.DOWNLOAD_PATH))
                new_files = current_files - initial_files
                if new_files:
                    downloaded_filename = new_files.pop()
                    if downloaded_filename.endswith('.crdownload'):
                        time.sleep(1)
                        download_wait_time += 1
                        continue
                    
                    original_path = self.DOWNLOAD_PATH / downloaded_filename
                    new_file_path = self.DOWNLOAD_PATH / filename
                    original_path.rename(new_file_path)
                    logger.info(f"Download concluído e renomeado para: {filename}")
                    
                    # Fecha a aba de download e volta para a principal
                    self.driver.close()
                    self.driver.switch_to.window(main_window_handle)
                    
                    return str(new_file_path)
                
                time.sleep(1)
                download_wait_time += 1

            logger.warning(f"Timeout ao esperar pelo download do arquivo: {publication['title']}")
            # Fecha a aba extra mesmo se falhar
            self.driver.close()
            self.driver.switch_to.window(main_window_handle)
            return None
            
        except Exception as e:
            logger.error(f"Erro ao baixar a publicação '{publication['title']}': {str(e)}")
            # Garante que voltamos para a aba principal em caso de erro
            if self.driver.current_window_handle != main_window_handle:
                try:
                    self.driver.close()
                except:
                    pass
                finally:
                    self.driver.switch_to.window(main_window_handle)
            return None

    def run(self):
        try:
            self.init_driver()
            self.navigate_to_site()
            first_day, last_day = self.get_last_month_date_range()
            self.set_date_filter(first_day, last_day)

            publications_metadata = self.navigate_pagination()

            if not publications_metadata:
                logger.warning("Nenhuma publicação encontrada no período especificado.")
                return []

            result = []
            main_window = self.driver.current_window_handle
            for i, pub in enumerate(publications_metadata):
                logger.info(f"Processando publicação {i+1}/{len(publications_metadata)}: {pub['title']}")
                
                file_path = self.download_publication(pub, main_window)
                
                if file_path:
                    pub["file_path"] = file_path
                    result.append(pub)
                
                time.sleep(1) # Pausa entre os downloads
            
            logger.info(f"Processo de scraping concluído. {len(result)} arquivos baixados.")
            return result
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver do Selenium encerrado.")