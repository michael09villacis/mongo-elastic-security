# Actividad 1 (individual): Seguridad en NoSQL con MongoDB, Elasticsearch y FastAPI

Laboratorio académico de seguridad en bases de datos NoSQL. Se parte de una aplicación de tienda **deliberadamente vulnerable** para reproducir ataques controlados y después aplicar contramedidas de validación, autenticación y control de acceso. El objetivo es comparar el comportamiento **antes y después** de las defensas.

> **Uso exclusivamente educativo.** Los datos de la tienda son ficticios. No desplegar la rama vulnerable en redes públicas ni reutilizar sus contraseñas de ejemplo.

## 1. Estado del proyecto y ramas

| Rama | Finalidad |
| --- | --- |
| `vulnerable` | Versión inicial: permite reproducir la inyección NoSQL y los accesos anónimos a MongoDB y Elasticsearch. |
| `main` | Versión securizada: validación con Pydantic, autenticación obligatoria y RBAC en MongoDB y Elasticsearch. TLS activado en MongoDB y Elasticsearch; pendientes las comprobaciones finales de logging y regresión. |

## 2. Requisitos previos

- Windows 11 y PowerShell (los comandos pueden adaptarse a otros sistemas).
- Docker Desktop con contenedores Linux y Docker Compose V2.
- Postman para pruebas HTTP.
- Git y una cuenta de GitHub.
- No es necesario instalar Python localmente: FastAPI se ejecuta en un contenedor con Python 3.11.

```powershell
docker version
docker compose version
git --version
```

## 3. Estructura del repositorio

```text
mongo-elastic-security/
├── evidencias/                 # Colección Postman exportada
├── fastapi-app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── scripts/
│   ├── init_mongo.js
│   └── init_elastic.sh
├── certs/                     # Certificados y claves locales; excluidos de Git
│   ├── mongodb/               # ca.crt, server.pem y claves
│   └── elasticsearch/         # CA y certificado de Elasticsearch
├── .env                       # Credenciales locales; excluido de Git
├── docker-compose.yml
├── .gitattributes
├── .gitignore
└── README.md
```

La carpeta `certs/` completa, el archivo `.env`, los archivos de respaldo y las claves privadas **no se han publicado por seguridad**. La memoria PDF de la actividad contiene las capturas y explicaciones de las pruebas.

## 4. Arquitectura y servicios

| Servicio | Imagen | Puerto publicado en el equipo | Función |
| --- | --- | --- | --- |
| MongoDB | `mongo:7` | `127.0.0.1:27017` | Base de datos `tienda`, colecciones `usuarios` y `pedidos` |
| Elasticsearch | `elasticsearch:7.17.10` | `127.0.0.1:9200` | Índice `articulos` |
| FastAPI | Construcción desde `./fastapi-app` | `127.0.0.1:8000` | API de autenticación y consultas |

Los nombres de servicio internos de Docker Compose son `mongo`, `elasticsearch` y `fastapi-app`. Los puertos están publicados únicamente en la interfaz local; esto limita la exposición desde otros equipos, pero **no sustituye** a la autenticación ni al cifrado.

Endpoints de FastAPI:

| Método | Ruta | Función |
| --- | --- | --- |
| `GET` | `/health` | Comprueba la conectividad con MongoDB |
| `POST` | `/login_mongo` | Verifica credenciales ficticias de la tienda |
| `GET` | `/pedidos` | Consulta los pedidos almacenados en MongoDB |
| `GET` | `/articulos?q=*` | Consulta el índice `articulos` de Elasticsearch |

Documentación interactiva: <http://localhost:8000/docs>.

## 5. Datos de laboratorio

El script `scripts/init_mongo.js` crea datos ficticios en la base de datos `tienda` durante la primera inicialización.

| Usuario de la aplicación | Contraseña de ejemplo | Tipo |
| --- | --- | --- |
| `admin` | `admin123` | Administrador ficticio de la tienda |
| `peter` | `peter123` | Cliente |
| `maria` | `maria123` | Cliente |

Estos usuarios de la colección `usuarios` **no son** cuentas administrativas de MongoDB ni sustituyen la autenticación de la base de datos. El laboratorio conserva las contraseñas ficticias de la aplicación en texto claro para reproducir el caso inicial; en una aplicación real deberían almacenarse mediante un algoritmo de hash de contraseñas.

Pedidos de ejemplo: un portátil ASUS para `peter` y dos ratones Logitech para `maria`.

El script `scripts/init_elastic.sh` carga tres artículos:

| Artículo | Categoría | Precio |
| --- | --- | ---: |
| Portátil ASUS | Informática | 799 € |
| Ratón Logitech | Accesorios | 25 € |
| Teclado mecánico | Accesorios | 65 € |

**Nota:** Docker Compose no ejecuta automáticamente `init_elastic.sh`. El índice se cargó inicialmente mediante un contenedor temporal con `curl`. Después se exportaron sus tres documentos, se creó un volumen persistente y se restauraron con la API `_bulk`.

## 6. Despliegue y caraterísticas de la configuración actual

Desde la raíz del proyecto:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Consultar los registros:

```powershell
docker compose logs --tail=50 fastapi-app
docker compose logs --tail=50 mongo
docker compose logs --tail=50 elasticsearch
```

### 6.1. Variables de entorno

La rama `main` utiliza credenciales de cuentas técnicas, definidas en un archivo `.env` **local y no versionado**:

```dotenv
MONGO_USER=fastapi_user
MONGO_PASSWORD=CONTRASEÑA_LOCAL
ELASTIC_USER=fastapi_elastic
ELASTIC_PASSWORD=CONTRASEÑA_LOCAL
```

El servicio `fastapi-app` recibe además `MONGO_HOST=mongo`, `MONGO_DATABASE=tienda` y `ELASTIC_HOST=elasticsearch`. En `main.py`, MongoDB utiliza `authSource="tienda"` y la conexión HTTPS a Elasticsearch utiliza autenticación Basic con la cuenta técnica y verificación de la CA. MongoDB usa `tls=True` y `tlsCAFile="/app/certs/mongodb-ca.crt"`.

No se incluyen contraseñas reales en este README. **No basta con crear `.env` para desplegar `main` desde cero:** antes deben existir las cuentas y los roles en las bases de datos, así como los certificados TLS montados por Docker Compose.

### 6.2. Persistencia y reproducibilidad

- **MongoDB:** en el laboratorio actual se reutiliza un volumen Docker externo ya existente para `/data/db`, identificado por un nombre largo generado localmente por Docker. Ese identificador **no es portable** a otro equipo.
- **Elasticsearch:** se utiliza el volumen con nombre `elastic_data`, montado en `/usr/share/elasticsearch/data` (por ejemplo, `mongo-elastic-security_elastic_data`).
- **Inicialización:** `init_mongo.js` solo se ejecuta automáticamente cuando el directorio de datos está vacío. Los usuarios administrativos y los roles RBAC se crearon posteriormente en la instancia del laboratorio.

**Advertencia para quien clone el repositorio:** la configuración actual de `main` refleja un entorno ya inicializado; no debe considerarse un despliegue seguro automatizado desde cero. Antes de distribuirlo como instalación reproducible hay que reemplazar el identificador del volumen externo de MongoDB y documentar o automatizar el aprovisionamiento inicial de cuentas, roles y contraseñas. No ejecutar `docker compose down -v` sin comprender sus efectos sobre los datos.

## 7. Ataques reproducidos en la rama `vulnerable`

Las pruebas se realizaron en un entorno local controlado y se documentaron en Postman y en la memoria PDF.

### 7.1. Inyección NoSQL en MongoDB

Petición a `POST http://localhost:8000/login_mongo`:

```json
{
  "username": "peter",
  "password": { "$ne": "x" }
}
```

**Antes:** `200 OK` con `{"msg":"ok"}`; el operador `$ne` permitía eludir la comprobación de contraseña.

### 7.2. Acceso anónimo a MongoDB

En la versión vulnerable se pudo consultar la colección `usuarios` sin autenticación. Se comprobó también la ausencia de usuarios autenticados en la sesión y que la conexión no exigía TLS.

### 7.3. Acceso anónimo a Elasticsearch

Sin credenciales se obtuvo `200 OK` al consultar `/_cat/indices` y `/articulos/_search`. También se comprobó que el servicio inicial no ofrecía HTTPS.

> Las pruebas de ataque deben ejecutarse únicamente sobre la rama vulnerable y el entorno autorizado. No exponer los servicios a Internet.

## 8. Contramedidas implementadas en `main`

### 8.1. Validación de entradas con Pydantic

El modelo `Login` utiliza `StrictStr` para `username` y `password`, y `ConfigDict(extra="forbid")` para rechazar campos adicionales. El endpoint accede a los atributos validados (`data.username`, `data.password`) en lugar de aceptar objetos JSON arbitrarios como filtros de MongoDB.

| Prueba en `POST /login_mongo` | Resultado verificado |
| --- | --- |
| `peter` / `peter123` | `200 OK` |
| `peter` / contraseña incorrecta | `401 Unauthorized` |
| `password` con `{ "$ne": "x" }` | `422 Unprocessable Entity` |

La validación bloquea **el vector de inyección ensayado**; no equivale a una auditoría exhaustiva de todas las entradas de la aplicación.

### 8.2. Autenticación y RBAC en MongoDB

Se activó `mongod --auth --bind_ip_all` y se crearon las siguientes identidades de base de datos:

| Identidad | Rol | Uso |
| --- | --- | --- |
| `mongo_admin` | `root` en `admin` | Administración de MongoDB |
| `fastapi_user` | `fastapi_reader` en `tienda` | Conexión de FastAPI |

El rol personalizado `fastapi_reader` solo concede la acción `find` sobre `tienda.usuarios` y `tienda.pedidos`. No concede escritura ni administración.

**Pruebas verificadas:**

- Consulta sin autenticación: rechazada.
- Lectura de `usuarios` y `pedidos` como `fastapi_user`: permitida.
- Inserción y eliminación como `fastapi_user`: rechazadas con `not authorized`.
- `/health`, `/login_mongo` y `/pedidos` de FastAPI: funcionamiento comprobado después de habilitar la autenticación.

Antes de activar `--auth`, la inserción con `fastapi_user` todavía se permitía, porque MongoDB no estaba aplicando autorización. Esa diferencia se utilizó como evidencia del efecto de RBAC.

### 8.3. Autenticación y RBAC en Elasticsearch

Se cambió `xpack.security.enabled=false` por `true`, se configuró la contraseña del usuario integrado `elastic` y se creó:

| Identidad | Rol | Permisos |
| --- | --- | --- |
| `elastic` | `superuser` | Administración del servicio |
| `fastapi_elastic` | `fastapi_reader` | `read` y `view_index_metadata` únicamente sobre `articulos` |

**Pruebas verificadas directamente contra Elasticsearch:**

| Operación | Resultado |
| --- | --- |
| Acceso anónimo a `/` | `401 Unauthorized` |
| Autenticación del administrador `elastic` | Correcta |
| Consulta de `articulos` como `fastapi_elastic` | `200 OK` |
| Consulta de `/_cat/indices` como `fastapi_elastic` | `403 Forbidden` |
| Inserción en `articulos` como `fastapi_elastic` | `403 Forbidden` |

FastAPI consulta Elasticsearch por HTTPS mediante `ELASTIC_USER` y `ELASTIC_PASSWORD`, sin usar la cuenta administrativa, y valida la CA montada en `/app/certs/ca.crt`. Se verificó una consulta a `/articulos?q=*` con tres documentos. Conviene repetir y registrar la búsqueda `/articulos?q=ASUS` como regresión final.

### 8.4. TLS en MongoDB: certificados y verificación

MongoDB 7 exige conexiones cifradas mediante `--tlsMode requireTLS`, con `--tlsCertificateKeyFile /etc/mongo/certs/server.pem` y `--tlsCAFile /etc/mongo/certs/ca.crt`. Los archivos se montan desde `./certs/mongodb/` (carpeta local excluida de Git).

Se generó una CA raíz propia de laboratorio (`MongoDB-Lab-CA-v2`) con RSA de 3072 bits y SHA-256, y se firmó el certificado de servidor con extensiones de servidor TLS y SAN para `mongo`, `localhost` y `127.0.0.1`. Durante el proceso se detectó una CA anterior con la extensión `Basic Constraints` duplicada; se sustituyó por una CA nueva, cuya verificación devolvió `OK`. También devolvió `OK` la validación del certificado del servidor con `-purpose sslserver`.

**Comprobación de certificados antes de instalarlos** (ejecutada dentro del contenedor de Elasticsearch, que dispone de OpenSSL):

```powershell
docker compose exec elasticsearch openssl verify -CAfile /tmp/mongo-ca-v2.crt -check_ss_sig /tmp/mongo-ca-v2.crt
docker compose exec elasticsearch openssl verify -CAfile /tmp/mongo-ca-v2.crt -purpose sslserver /tmp/mongo-server-v2.crt
```

Ambas comprobaciones devolvieron `OK` durante la configuración inicial. Las rutas `/tmp/` son **temporales** y no están garantizadas tras recrear el contenedor. Para nuevas instalaciones hay que generar certificados nuevos o utilizar los archivos locales autorizados.

El archivo `server.pem` contiene el certificado y la clave privada del servidor. En FastAPI, PyMongo usa `tls=True` y la CA local montada en `/app/certs/mongodb-ca.crt`; no se desactiva la validación del certificado.

MongoDB rechazó inicialmente a FastAPI con `No SSL certificate provided by peer; connection rejected`, pese a completarse el handshake TLS. Se añadió `--tlsAllowConnectionsWithoutCertificates` para admitir clientes que se autentican mediante usuario y contraseña **sin certificado de cliente**. Esto no desactiva TLS ni la autenticación/RBAC, pero **no implementa autenticación mutua mTLS**.

**Pruebas verificadas después del cambio:**

- `ping` desde FastAPI hacia MongoDB mediante TLS y credenciales técnicas: `{'ok': 1.0}`.
- Recuento de documentos de `tienda.usuarios` y `tienda.pedidos`: permitido.
- Intento de `insert_one` en `tienda.usuarios` con `fastapi_user`: denegado con código de autorización `13`.
- Reinicio de MongoDB y FastAPI con certificados nuevos: ambos servicios arrancaron sin errores.

### 8.5. HTTPS en Elasticsearch

Elasticsearch 7.17.10 tiene `xpack.security.enabled=true` y HTTPS en su interfaz HTTP (`xpack.security.http.ssl.enabled=true`), utilizando un certificado de servidor y una CA local. FastAPI dispone de la CA de Elasticsearch en `/app/certs/ca.crt` para verificar la conexión. La cuenta `fastapi_elastic` mantiene permisos de solo lectura sobre el índice `articulos`.

La configuración cifra el tráfico **HTTP de Elasticsearch**; no debe interpretarse como una verificación del cifrado TLS del transporte interno entre nodos, que no se ha documentado en esta práctica.

### 8.6. Restricción de puertos y registros

- **Puertos:** MongoDB (`27017`), Elasticsearch (`9200`) y FastAPI (`8000`) se publican solo en `127.0.0.1`.
- **Logging:** se consultaron los registros de los tres servicios; los de MongoDB permitieron identificar el rechazo del cliente sin certificado.
- **Logging adicional:** se ha trabajado en un middleware de FastAPI para registrar método, ruta, código HTTP y duración sin almacenar contraseñas ni cuerpos. Su cobertura y comprobación final deben confirmarse; los logs operativos no sustituyen una auditoría completa.
- **Límite de TLS:** el acceso del navegador/Postman a FastAPI continúa por `http://localhost:8000`; TLS se ha configurado en las conexiones de FastAPI con los servicios de datos, no en la interfaz pública de FastAPI.

## 9. Pruebas de regresión con Postman

Sobre FastAPI (`http://localhost:8000`), sin añadir autenticación Basic a las peticiones del cliente:

| Prueba | Resultado esperado / verificado |
| --- | --- |
| `GET /health` | `200 OK` — verificado tras RBAC de MongoDB |
| `GET /pedidos` | `200 OK` — verificado tras RBAC de MongoDB |
| `POST /login_mongo` con credenciales válidas | `200 OK` — verificado |
| `POST /login_mongo` con credenciales incorrectas | `401 Unauthorized` — verificado |
| `POST /login_mongo` con `$ne` en `password` | `422 Unprocessable Entity` — verificado |
| `GET /articulos?q=*` | `200 OK`, tres documentos — verificado con Elasticsearch securizado |
| `GET /articulos?q=ASUS` | `200 OK`, artículo ASUS — verificado en la fase inicial; repetir y registrar con HTTPS |

En Postman se han organizado pruebas de funcionamiento inicial, ataques y contramedidas. Antes de exportar la colección, **eliminar contraseñas reales, cabeceras `Authorization` y otros secretos**; si hace falta, sustituirlos por variables de entorno de Postman sin valores compartidos.

## 10. Comprobaciones útiles

### MongoDB: conexión TLS y autenticación desde FastAPI

El siguiente bloque de PowerShell evita problemas de comillas al ejecutar Python dentro del contenedor:

```powershell
@'
from pymongo import MongoClient
import os

client = MongoClient(
    host="mongo", port=27017,
    username=os.getenv("MONGO_USER"),
    password=os.getenv("MONGO_PASSWORD"),
    authSource="tienda",
    tls=True,
    tlsCAFile="/app/certs/mongodb-ca.crt",
    serverSelectionTimeoutMS=5000
)
print(client.admin.command("ping"))
print("Usuarios:", client["tienda"]["usuarios"].count_documents({}))
print("Pedidos:", client["tienda"]["pedidos"].count_documents({}))
client.close()
'@ | docker compose exec -T fastapi-app python -
```

Resultado verificado: `{'ok': 1.0}` y lecturas permitidas. El número de documentos depende del estado del volumen.

### MongoDB: escritura denegada por RBAC

```powershell
@'
from pymongo import MongoClient
from pymongo.errors import OperationFailure
import os

client = MongoClient(
    host="mongo", port=27017,
    username=os.getenv("MONGO_USER"),
    password=os.getenv("MONGO_PASSWORD"),
    authSource="tienda", tls=True,
    tlsCAFile="/app/certs/mongodb-ca.crt",
    serverSelectionTimeoutMS=5000
)
try:
    client["tienda"]["usuarios"].insert_one({"_id": "test_rbac_denegado"})
    print("ERROR: escritura permitida; revisar y eliminar el documento de prueba")
except OperationFailure as error:
    if error.code == 13:
        print("CORRECTO: escritura denegada por RBAC")
    else:
        print("ERROR inesperado:", error)
finally:
    client.close()
'@ | docker compose exec -T fastapi-app python -
```

Resultado verificado: `CORRECTO: escritura denegada por RBAC`. No se insertó el documento de prueba.

### Elasticsearch: acceso HTTPS sin credenciales

```powershell
curl.exe --cacert .\certs\elasticsearch\ca\ca.crt -i "https://localhost:9200/"
```

Resultado esperado: `401 Unauthorized` cuando el certificado sea válido para `localhost`. No utilizar `-k`/`--insecure` como prueba de validación TLS.

### Elasticsearch: consulta autenticada por HTTPS

```powershell
curl.exe --cacert .\certs\elasticsearch\ca\ca.crt -u fastapi_elastic "https://localhost:9200/articulos/_count"
```

`curl` solicitará la contraseña. Si el certificado no incluye `localhost` en sus SAN, el comando fallará por nombre de host; se debe corregir el certificado o usar un nombre cubierto por él, **no desactivar la verificación**. La presencia de HTTPS no elimina la necesidad de autenticación y RBAC.

### Estado y registros

```powershell
docker compose config --quiet
docker compose ps
docker compose logs --tail=30 fastapi-app
docker compose logs --tail=30 mongo
docker compose logs --tail=30 elasticsearch
```

## 11. Seguridad del repositorio público

El archivo `.gitignore` del proyecto excluye, entre otros:

```gitignore
.env
.env.*
!.env.example
certs/
*.key
*.pem
*.p12
*.pfx
*.csr
*.zip
*.archive
*.bson
__pycache__/
*.py[cod]
.venv/
```

Se comprobó que `git ls-files certs .env` no devuelve archivos rastreados tras ejecutar `git rm -r --cached -- certs/`. Se creó un commit con los cambios y se realizó el `push` a `main`. **Esto no garantiza que el historial anterior esté libre de secretos.**

`.gitignore` **no elimina secretos que ya estén incluidos en el historial**. Revisar las dos ramas (`main` y `vulnerable`) antes de publicar y sustituir cualquier credencial real comprometida. Los archivos de ejemplo deben contener únicamente valores ficticios.

## 12. Detener el laboratorio

```powershell
docker compose down
```

Este comando detiene y elimina los contenedores y redes del proyecto sin solicitar la eliminación de volúmenes.