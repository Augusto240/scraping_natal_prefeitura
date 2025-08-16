"""
Módulos core do sistema de scraping da Prefeitura de Natal.

Este pacote contém as funcionalidades fundamentais do sistema:
- database: Conexão e operações com PostgreSQL
- Configurações e utilitários base
"""

from .database import DatabaseManager

__all__ = [
    'DatabaseManager',
]

__version__ = '1.0.0'
__author__ = 'Augusto'
__description__ = 'Core modules for Natal Prefecture scraping system'
