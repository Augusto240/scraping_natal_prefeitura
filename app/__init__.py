"""
Sistema de Scraping da Prefeitura de Natal

Sistema completo para coleta automática de publicações do Diário Oficial
da Prefeitura de Natal, upload para 0x0.st e armazenamento em PostgreSQL.

Desenvolvido como parte do Desafio Técnico para Desenvolvedor Python na Conthabil.

Módulos principais:
- main: Orquestrador principal do sistema
- api: API REST com FastAPI
- core: Módulos fundamentais (database)
- services: Serviços de negócio (scraper, uploader)

Exemplo de uso:
    from services import PrefeituraScraper, FileUploader0x0st
    from core import DatabaseManager
    
    scraper = PrefeituraScraper()
    uploader = FileUploader0x0st()
    db = DatabaseManager()
"""

__title__ = 'Scraper Prefeitura Natal'
__version__ = '1.0.0'
__author__ = 'Augusto'
__email__ = 'augusto@example.com'
__description__ = 'Automated scraping system for Natal Prefecture publications'
__url__ = 'https://github.com/Augusto240/scraping_natal_prefeitura'

# Facilitar imports principais
from .core import DatabaseManager
from .services import PrefeituraScraper, FileUploader0x0st

__all__ = [
    'DatabaseManager',
    'PrefeituraScraper', 
    'FileUploader0x0st',
]
