from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="Natal Prefeitura API - Versão Mínima")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "API do Sistema de Scraping da Prefeitura de Natal",
        "nota": "Esta é uma versão simplificada para verificar o deploy."
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)