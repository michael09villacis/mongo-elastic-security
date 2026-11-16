# Actividad 1 (individual): Seguridad en NoSQL (MongoDB y Elasticsearch) con FastAPI

Este repositorio implementa un entorno de tienda deliberadamente inseguro (*baseline*) para comprobar su funcionamiento antes de realizar pruebas controladas de seguridad y aplicar contramedidas.

> **A tener en cuenta:** entorno exclusivamente educativo. Utiliza datos ficticios.

## 1. Requisitos previos

- Windows 11 con PowerShell.
- Docker Desktop con motor Linux y Docker Compose V2.
- Postman.
- Python 3.11 (la imagen de FastAPI ya lo incorpora; no es imprescindible instalarlo localmente para ejecutar el contenedor).
- Opcional: `mongosh` local. En los pasos siguientes se utiliza el incluido en el contenedor MongoDB.

Comprobar Docker:

```powershell
docker version
docker compose version
```

## 2. Estructura del repositorio

```text
mongo-elastic-security/
├── evidencias/
├── fastapi-app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── scripts/
│   ├── init_mongo.js
│   └── init_elastic.sh
├── docker-compose.yml
└── README.md
```

## 3. Servicios y configuración inicial

| Servicio | Imagen | Puerto local | Función |
| --- | --- | --- | --- |
| MongoDB | `mongo:7` | `127.0.0.1:27017` | Base de datos `tienda` (colecciones `usuarios` y `pedidos`) |
| Elasticsearch | `elasticsearch:7.17.10` | `127.0.0.1:9200` | Índice `articulos` |
| FastAPI | Construida desde `./fastapi-app` | `127.0.0.1:8000` | API de consulta y autenticación de prueba |


En el *baseline*, MongoDB no exige autenticación y Elasticsearch utiliza `xpack.security.enabled: "false"`. Los puertos se publican solo en `127.0.0.1` para reducir la exposición desde otros equipos.

Variables de entorno del servicio `fastapi-app`:

```yaml
environment:
  MONGO_HOST: mongo
  MONGO_DATABASE: tienda
  ELASTIC_HOST: elasticsearch
```

## 4. Despliegue del entorno vulnerable

Abrir PowerShell en la carpeta del proyecto. Si la ruta contiene espacios, usar comillas:

```powershell
cd 'C:\Michael_docs\Unir\2027\Seguridad en BBDD\mongo-elastic-security'
```

Validar la configuración y arrancar:

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

Deben aparecer los servicios `mongo`, `elasticsearch` y `fastapi-app` en ejecución. Para ver también los detenidos:

```powershell
docker compose ps -a
```

Si FastAPI no arranca, consultar sus registros:

```powershell
docker compose logs fastapi-app --tail 50
```

La API incorpora `GET /health`, `GET /pedidos`, `POST /login_mongo` y `GET /articulos`. La documentación interactiva se encuentra en <http://localhost:8000/docs>.

## 5. Inicialización y comprobación de MongoDB

El archivo `scripts/init_mongo.js` selecciona la base de datos `tienda` y crea datos ficticios en las colecciones `usuarios` y `pedidos`.

Usuarios de laboratorio:

| Usuario | Contraseña ficticia | Rol de ejemplo |
| --- | --- | --- |
| `admin` | `admin123` | administrador |
| `peter` | `peter123` | cliente |
| `maria` | `maria123` | cliente |

Pedidos de ejemplo: un portátil ASUS para `peter` y dos ratones Logitech para `maria`.

Comprobar las colecciones y documentos:

```powershell
docker compose exec mongo mongosh tienda
```

Dentro de `mongosh`:

```javascript
show collections
db.usuarios.find().pretty()
db.pedidos.find().pretty()
exit
```

**Nota:** los scripts de `/docker-entrypoint-initdb.d/` se ejecutan durante la inicialización de una base de datos nueva; no se vuelven a aplicar automáticamente si ya existen datos persistentes. No ejecutar `docker compose down -v` sin querer eliminar volúmenes y datos.

## 6. Inicialización de Elasticsearch

**Estado:** el servicio Elasticsearch respondió correctamente, pero la primera consulta de índices solo mostró `.geoip_databases`; el índice `articulos` todavía no estaba creado en esa comprobación. La carga posterior queda pendiente de confirmación.

El archivo `scripts/init_elastic.sh` contiene peticiones HTTP que insertan tres artículos ficticios en el índice `articulos`:

- Portátil ASUS — Informática — 799 €.
- Ratón Logitech — Accesorios — 25 €.
- Teclado mecánico — Accesorios — 65 €.

A diferencia del script de MongoDB, **Compose no ejecuta automáticamente** `init_elastic.sh`. Para lanzarlo con un contenedor temporal que dispone de `curl`, identificar primero la red del proyecto:

```powershell
docker network ls
```

Si la red se llama `mongo-elastic-security_default`, ejecutar desde la raíz del repositorio:

```powershell
docker run --rm `
  --network mongo-elastic-security_default `
  -v "${PWD}/scripts/init_elastic.sh:/init_elastic.sh:ro" `
  --entrypoint sh `
  curlimages/curl:8.11.1 /init_elastic.sh
```

Sustituir el nombre de la red si es diferente. **Si se utiliza Windows y el script se guardó con finales de línea CRLF, convertirlo a LF antes de ejecutarlo en Linux.**

Verificar el índice y el número de artículos:

```powershell
curl.exe "http://localhost:9200/_cat/indices?v"
curl.exe "http://localhost:9200/articulos/_count"
```

Tras una carga correcta, el índice `articulos` debería existir y su recuento ser `3`.

## 7. Smoke tests con Postman

Crear una colección de Postman llamada `Laboratorio - Aplicación NoSQL`. Para todas estas pruebas seleccionar **Authorization → No Auth**.

### 7.1. GET /pedidos

- Método: `GET`.
- URL: `http://localhost:8000/pedidos`.
- Body: ninguno.
- Resultado esperado: **200 OK**, con los pedidos ficticios de MongoDB.

### 7.2. POST /login_mongo — credenciales correctas

- Método: `POST`.
- URL: `http://localhost:8000/login_mongo`.
- Body → raw → JSON:

```json
{
  "username": "peter",
  "password": "peter123"
}
```

Resultado esperado: **200 OK** y `{"msg":"ok"}`.

### 7.3. POST /login_mongo — credenciales incorrectas

Repetir la petición con:

```json
{
  "username": "peter",
  "password": "incorrecta"
}
```

Resultado esperado: **401 Unauthorized** y `{"detail":"Bad creds"}`.

### 7.4. GET /articulos

**Requisito previo:** haber cargado y comprobado el índice `articulos`.

- Método: `GET`.
- URL: `http://localhost:8000/articulos?q=*`.
- Body: ninguno.
- Resultado esperado: **200 OK** y los tres artículos en `hits.hits`.

Prueba adicional de búsqueda: `http://localhost:8000/articulos?q=ASUS`.

Guardar capturas de Postman con método, URL, código HTTP y respuesta para incorporarlas al informe PDF. Los códigos indicados son **resultados esperados**, no afirmaciones de que todas las pruebas ya se hayan ejecutado satisfactoriamente.

## 8. Estado y siguientes fases

| Actividad | Estado |
| --- | --- |
| Docker Desktop y motor Linux operativos | Comprobado |
| Contenedores MongoDB, Elasticsearch y FastAPI | Arranque de FastAPI y Swagger confirmado |
| Base de datos `tienda` y consultas de pedidos en `mongosh` | Trabajado en el laboratorio; conservar evidencia |
| Endpoint `GET /pedidos` | Implementado; documentar resultado de Postman |
| Endpoint `POST /login_mongo` | Implementado; documentar ambas respuestas de Postman |
| Script `init_elastic.sh` | Preparado; ejecución y carga pendientes de confirmar |
| Endpoint `GET /articulos` | Pendiente de comprobar con índice cargado |
| Reconocimiento y ataques controlados | Próxima fase |
| Validación Pydantic, autenticación/RBAC, restricciones ES, puertos y logging | Próxima fase |
| Verificación antes/después | Próxima fase |

Las siguientes fases se documentarán aquí conforme se implementen y verifiquen. El informe PDF separado recogerá metodología, evidencias, riesgos, defensas y relación con Zero Trust, mínimo privilegio, RGPD y NIS2.

## 9. Detener el laboratorio

```powershell
docker compose down
```

Este comando detiene y elimina los contenedores y redes del proyecto, sin solicitar la eliminación de volúmenes. Evitar `docker compose down -v` salvo que se quiera reinicializar y perder los datos persistentes.
