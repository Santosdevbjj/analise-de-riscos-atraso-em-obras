from fastapi import FastAPI
from typing import Union

app = FastAPI(title="Minha API Render 2026")

@app.get("/")
async def root():
    return {
        "status": "online",
        "python_version": "3.14.3",
        "message": "Rodando com performance máxima no Render em 2026!"
    }

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    # Exemplo simples de rota com parâmetros
    return {"item_id": item_id, "query": q}
