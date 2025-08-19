import logging
import re
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from core.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API de Publicações da Prefeitura de Natal",
    description="API para acesso às publicações do Diário Oficial da Prefeitura de Natal",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = DatabaseManager()

@app.get("/")
async def root():
    return {
        "message": "API de Publicações da Prefeitura de Natal",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/arquivos", "description": "Lista todas as publicações"},
            {"path": "/arquivos/{competencia}", "description": "Lista publicações por competência (YYYY-MM)"}
        ]
    }

@app.get("/arquivos")
async def list_publications():
    try:
        publications = db_manager.get_all_publications()
        return {
            "total": len(publications),
            "publicacoes": publications
        }
    except Exception as e:
        logger.error(f"Erro ao listar publicações: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar publicações")

@app.get("/arquivos/{competencia}")
async def get_publications_by_competence(competencia: str):
    if not re.match(r"^\d{4}-\d{2}$", competencia):
        raise HTTPException(
            status_code=400, 
            detail="Formato de competência inválido. Use o formato YYYY-MM (ex: 2025-07)"
        )
    
    try:
        year, month = map(int, competencia.split("-"))
        datetime(year, month, 1)
        
        publications = db_manager.get_publications_by_competence(competencia)
        return {
            "competencia": competencia,
            "total": len(publications),
            "publicacoes": publications
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida")
    except Exception as e:
        logger.error(f"Erro ao buscar publicações por competência: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar publicações")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)