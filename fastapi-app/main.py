from fastapi import FastAPI, Request, HTTPException
#from pydantic import BaseModel
from pydantic import BaseModel, StrictStr, ConfigDict
from pymongo import MongoClient
import os
import requests

import logging
import time
from fastapi import Request

app = FastAPI(title="API NoSQL - mecanismos de Seguridad")

# Validación con logs para la mejora de trazabilidad
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

security_logger = logging.getLogger("security")


@app.middleware("http")
async def security_logging(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        security_logger.exception(
            "request_error method=%s path=%s",
            request.method,
            request.url.path
        )
        raise

    duration_ms = round(
        (time.perf_counter() - start_time) * 1000,
        2
    )

    security_logger.info(
        "request method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms
    )

    return response

mongo_host = os.getenv("MONGO_HOST", "mongo")
mongo_database = os.getenv("MONGO_DATABASE", "tienda")
#Se añade validación con credenciales
mongo_user = os.getenv("MONGO_USER")
mongo_password = os.getenv("MONGO_PASSWORD")

mongo_client = MongoClient(
    host=mongo_host,
    port=27017,
    username=os.getenv("MONGO_USER"),
    password=os.getenv("MONGO_PASSWORD"),
    authSource="tienda",
    tls=True,
    tlsCAFile="/app/certs/mongodb-ca.crt",
    serverSelectionTimeoutMS=5000
)
db = mongo_client[mongo_database]

# Conexión con Elasticsearch
elastic_host = os.getenv("ELASTIC_HOST", "elasticsearch")
elastic_url = f"https://{elastic_host}:9200"

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
    auth=(elastic_user, elastic_password),
    verify="/app/certs/ca.crt",
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