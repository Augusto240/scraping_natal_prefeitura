from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
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

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
logger.info(f"Usando string de conexão: {DATABASE_URL.split('@')[0]}@******")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

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

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas ou verificadas com sucesso")
    except Exception as e:
        logger.warning(f"Não foi possível criar tabelas: {str(e)}")
        logger.info("Continuando sem persistência de dados")

except Exception as e:
    logger.warning(f"Erro ao configurar banco de dados: {str(e)}")
    logger.info("API funcionará sem persistência de dados")

def get_db():
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro de conexão com banco de dados")
    finally:
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
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        logger.error(f"Verificação de saúde falhou: {str(e)}")
        db_status = "error"
    
    return {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "production")
    }

@app.get("/arquivos")
async def list_publications(db: Session = Depends(get_db)):
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
            "message": "Modo de demonstração - sem conexão com banco de dados"
        }

@app.get("/arquivos/{competencia}")
async def get_publications_by_competence(competencia: str, db: Session = Depends(get_db)):
    import re
    if not re.match(r"^\d{4}-\d{2}$", competencia):
        raise HTTPException(
            status_code=400,
            detail="Formato de competência inválido. Use o formato YYYY-MM (ex: 2025-07)"
        )
    
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
                "message": "Modo de demonstração - sem conexão com banco de dados"
            }
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Iniciando servidor na porta {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)