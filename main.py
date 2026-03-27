import os
from fastapi import FastAPI, HTTPException
from supabase import create_client, Client

# Carregando as credenciais das variáveis de ambiente do Render
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Inicializa o cliente do Supabase
supabase: Client = create_client(url, key)

app = FastAPI(title="FastAPI + Supabase 2026")

@app.get("/")
async def root():
    return {"message": "Conectado ao Supabase via Render", "runtime": "Python 3.14.3"}

@app.get("/dados")
async def get_dados():
    # Exemplo de consulta em uma tabela chamada 'profiles'
    response = supabase.table("profiles").select("*").execute()
    
    # O SDK do Supabase em 2026 retorna um objeto com .data
    if hasattr(response, 'error') and response.error:
        raise HTTPException(status_code=400, detail=str(response.error))
        
    return {"data": response.data}

@app.post("/cadastrar")
async def cadastrar_usuario(nome: str, email: str):
    data = {"username": nome, "email": email}
    response = supabase.table("profiles").insert(data).execute()
    return {"status": "sucesso", "result": response.data}
