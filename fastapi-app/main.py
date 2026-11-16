from fastapi import FastAPI, Request, HTTPException
#from pydantic import BaseModel
from pydantic import BaseModel, StrictStr, ConfigDict
from pymongo import MongoClient
import os
import requests

app = FastAPI(title="API NoSQL - mecanismos de Seguridad")

mongo_host = os.getenv("MONGO_HOST", "mongo")
mongo_database = os.getenv("MONGO_DATABASE", "tienda")
#Se añade validación con credenciales
mongo_user = os.getenv("MONGO_USER")
mongo_password = os.getenv("MONGO_PASSWORD")

mongo = MongoClient(
    host=mongo_host,
    port=27017,
    username=mongo_user,
    password=mongo_password,
    authSource="tienda",
    serverSelectionTimeoutMS=5000
)
db = mongo[mongo_database]

# Conexión con Elasticsearch
elastic_host = os.getenv("ELASTIC_HOST", "elasticsearch")
elastic_url = f"http://{elastic_host}:9200"

#Se añaden credenciales de usuario para Elasticsearch
elastic_user = os.getenv("ELASTIC_USER")
elastic_password = os.getenv("ELASTIC_PASSWORD")


# Modelos de datos
""" 
#Vulnerable
class Login(BaseModel):
    username: str
    password: str
"""
#Implementación de la clase Login para que rechace un error de cualquier campo adicional que no esté definido explícitamente en la clase
class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: StrictStr
    password: StrictStr

class Pedido(BaseModel):
    producto: str
    cantidad: int
    
# Endpoint de comprobación de MongoDB
@app.get("/health")
def health():
    mongo.admin.command("ping")
    return {"status": "ok"}

# Endpoint de login protegido
@app.post("/login_mongo")
#async def login(req: Request):
async def login(data: Login):

    #data = await req.json()

    user = db.usuarios.find_one(
        {
          #  "username": data.get("username"),
          #  "password": data.get("password")
            "username": data.username,
            "password": data.password
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
        auth=(elastic_user, elastic_password), # Se añade la autorizacion
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