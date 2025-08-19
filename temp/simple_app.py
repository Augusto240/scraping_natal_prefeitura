from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import os
import logging
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("api")

app = FastAPI(title="Natal Prefeitura API", description="API do Sistema de Scraping da Prefeitura de Natal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variável para controle de estado
has_database = False
SessionLocal = None
Publication = None

# Configuração do banco de dados
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
logger.info(f"Usando string de conexão: {DATABASE_URL.split('@')[0]}@******")

try:
    engine = create_engine(DATABASE_URL)
    
    # NOVO: Bloco de diagnóstico detalhado para depuração
    try:
        # Apenas para depuração
        import sqlalchemy
        test_engine = sqlalchemy.create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            # CORRIGIDO: Usando text() para criar um objeto SQL executável
            result = conn.execute(text("SELECT 1")).fetchone()
            logger.info(f"✅ TESTE DE CONEXÃO BEM SUCEDIDO: {result}")
    except Exception as e:
        logger.error(f"❌ ERRO DE CONEXÃO DETALHADO: {str(e)}")
        logger.error(f"TIPO DE ERRO: {type(e).__name__}")
        # Mais detalhes se for disponível
        if hasattr(e, 'orig'):
            logger.error(f"ERRO ORIGINAL: {e.orig}")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    # Definir modelo
    class Publication(Base):
        __tablename__ = "publications"
        
        id = Column(Integer, primary_key=True)
        title = Column(String(255), nullable=False)
        publication_date = Column(DateTime, nullable=False)
        competence = Column(String(7), nullable=False, index=True)
        original_link = Column(Text, nullable=True)
        file_url = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        def to_dict(self):
            return {
                "id": self.id,
                "title": self.title,
                "publication_date": self.publication_date.strftime("%Y-%m-%d"),
                "competence": self.competence,
                "original_link": self.original_link,
                "file_url": self.file_url,
                "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }

    # Testar conexão e criar tabelas
    try:
        # Testar conexão
        with engine.connect() as conn:
            # CORRIGIDO: Usando text() para criar um objeto SQL executável
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Conexão com banco de dados bem-sucedida e tabelas criadas")
        has_database = True
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível conectar ao banco ou criar tabelas: {str(e)}")
        logger.info("Continuando em modo demonstração sem persistência")

except Exception as e:
    logger.warning(f"⚠️ Erro ao configurar banco de dados: {str(e)}")
    logger.info("API funcionará em modo demonstração")

# Dependência para obter a sessão do DB
def get_db():
    if not has_database:
        # Corrigido: Sempre use yield em vez de return em dependências com yield
        yield None
        return
    
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API do Sistema de Scraping da Prefeitura de Natal",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/", "description": "Informações da API"},
            {"path": "/health", "description": "Verificação de saúde da API"},
            {"path": "/arquivos", "description": "Lista todas as publicações"},
            {"path": "/arquivos/{competencia}", "description": "Lista publicações por competência (YYYY-MM)"}
        ]
    }

@app.get("/health")
async def health_check():
    db_status = "ok" if has_database else "error"
    try:
        if has_database:
            db = SessionLocal()
            # CORRIGIDO: Usando text() para criar um objeto SQL executável
            db.execute(text("SELECT 1"))
            db.close()
    except Exception as e:
        logger.error(f"Verificação de saúde falhou: {str(e)}")
        db_status = "error"
    
    return {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "connection_string": DATABASE_URL.split('@')[0] + '@******',
        "modo": "demonstração" if not has_database else "produção"
    }

@app.get("/arquivos")
async def list_publications(db: Session = Depends(get_db)):
    if db is None:
        # Retornar dados de demonstração
        return {
            "total": 2,
            "publicacoes": [
                {
                    "id": 1,
                    "title": "Demonstrativo Financeiro - Agosto 2025",
                    "publication_date": "2025-08-15",
                    "competence": "2025-08",
                    "original_link": "https://exemplo.com/demo1",
                    "file_url": "https://exemplo.com/arquivo1.pdf",
                    "created_at": "2025-08-15 10:30:00"
                },
                {
                    "id": 2,
                    "title": "Relatório de Receitas - Julho 2025",
                    "publication_date": "2025-07-10",
                    "competence": "2025-07",
                    "original_link": "https://exemplo.com/demo2",
                    "file_url": "https://exemplo.com/arquivo2.pdf",
                    "created_at": "2025-07-10 14:45:00"
                }
            ],
            "modo": "demonstração - sem conexão com banco de dados"
        }
    
    try:
        publications = db.query(Publication).order_by(Publication.publication_date.desc()).all()
        return {
            "total": len(publications),
            "publicacoes": [pub.to_dict() for pub in publications]
        }
    except Exception as e:
        logger.error(f"Erro ao listar publicações: {str(e)}")
        return {
            "total": 0,
            "publicacoes": [],
            "erro": str(e),
            "modo": "erro - problema ao acessar banco de dados"
        }

@app.get("/arquivos/{competencia}")
async def get_publications_by_competence(competencia: str, db: Session = Depends(get_db)):
    # Validar formato da competência (YYYY-MM)
    import re
    if not re.match(r"^\d{4}-\d{2}$", competencia):
        raise HTTPException(
            status_code=400,
            detail="Formato de competência inválido. Use o formato YYYY-MM (ex: 2025-07)"
        )
    
    if db is None:
        # Retornar dados de demonstração filtrados
        demo_data = [
            {
                "id": 1,
                "title": "Demonstrativo Financeiro - Agosto 2025",
                "publication_date": "2025-08-15",
                "competence": "2025-08",
                "original_link": "https://exemplo.com/demo1",
                "file_url": "https://exemplo.com/arquivo1.pdf",
                "created_at": "2025-08-15 10:30:00"
            },
            {
                "id": 2,
                "title": "Relatório de Receitas - Julho 2025",
                "publication_date": "2025-07-10",
                "competence": "2025-07",
                "original_link": "https://exemplo.com/demo2",
                "file_url": "https://exemplo.com/arquivo2.pdf",
                "created_at": "2025-07-10 14:45:00"
            }
        ]
        
        filtered = [item for item in demo_data if item["competence"] == competencia]
        
        return {
            "competencia": competencia,
            "total": len(filtered),
            "publicacoes": filtered,
            "modo": "demonstração - sem conexão com banco de dados"
        }
    
    try:
        year, month = map(int, competencia.split("-"))
        datetime(year, month, 1)
        
        try:
            publications = db.query(Publication).filter(
                Publication.competence == competencia
            ).order_by(Publication.publication_date.desc()).all()
            
            return {
                "competencia": competencia,
                "total": len(publications),
                "publicacoes": [pub.to_dict() for pub in publications]
            }
        except Exception as e:
            logger.error(f"Erro ao buscar publicações por competência: {str(e)}")
            return {
                "competencia": competencia,
                "total": 0,
                "publicacoes": [],
                "erro": str(e),
                "modo": "erro - problema ao acessar banco de dados"
            }
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Iniciando servidor na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)