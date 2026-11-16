from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import os
import requests

app = FastAPI(title="API NoSQL (vulnerable)")

mongo_host = os.getenv("MONGO_HOST", "mongo")
mongo_database = os.getenv("MONGO_DATABASE", "tienda")

mongo = MongoClient(
    host=mongo_host,
    port=27017,
    serverSelectionTimeoutMS=5000
)
db = mongo[mongo_database]

# Conexión con Elasticsearch
elastic_host = os.getenv("ELASTIC_HOST", "elasticsearch")
elastic_url = f"http://{elastic_host}:9200"

# Modelos de datos 
class Login(BaseModel):
    username: str
    password: str


class Pedido(BaseModel):
    producto: str
    cantidad: int
    
# Endpoint de comprobación de MongoDB
@app.get("/health")
def health():
    mongo.admin.command("ping")
    return {"status": "ok"}

# Endpoint de login vulnerable a NoSQL Injection
@app.post("/login_mongo")
async def login(req: Request):

    data = await req.json()

    user = db.usuarios.find_one(
        {
            "username": data.get("username"),
            "password": data.get("password")
        },
        {"_id": 0}
    )

    if user:
        return {"msg": "ok"}

    raise HTTPException(
        status_code=401,
        detail="Bad creds"
    )


# Endpoint de búsqueda en Elasticsearch
@app.get("/articulos")
def art_search(q: str = "*"):

    response = requests.get(
        f"{elastic_url}/articulos/_search",
        params={"q": q},
        timeout=10
    )

    response.raise_for_status()
    return response.json()
    
# Endpoint de consulta de pedidos    
@app.get("/pedidos")
def obtener_pedidos():
    pedidos = list(
        db.pedidos.find({}, {"_id": 0})
    )
    return {"pedidos": pedidos}