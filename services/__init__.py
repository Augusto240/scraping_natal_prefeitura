"""
Serviços do sistema de scraping da Prefeitura de Natal.

Este pacote contém os serviços principais:
- scraper: Web scraping com Selenium do site da prefeitura
- uploader: Upload de arquivos para 0x0.st conforme especificação do desafio
"""

from .scraper import PrefeituraScraper
from .uploader import FileUploader0x0st

__all__ = [
    'PrefeituraScraper',
    'FileUploader0x0st',
]

__version__ = '1.0.0'
__author__ = 'Augusto'
__description__ = 'Business services for Natal Prefecture scraping system'
