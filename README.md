# Actividad 1 (individual): Seguridad en NoSQL con MongoDB, Elasticsearch y FastAPI

Laboratorio académico de seguridad en bases de datos NoSQL. Se parte de una aplicación de tienda **deliberadamente vulnerable** para reproducir ataques controlados y después aplicar contramedidas de validación, autenticación y control de acceso. El objetivo es comparar el comportamiento **antes y después** de las defensas.

> **Uso exclusivamente educativo.** Los datos de la tienda son ficticios. No desplegar la rama vulnerable en redes públicas ni reutilizar sus contraseñas de ejemplo.

## 1. Estado del proyecto y ramas

| Rama | Finalidad |
| --- | --- |
| `vulnerable` | Versión inicial: permite reproducir la inyección NoSQL y los accesos anónimos a MongoDB y Elasticsearch. |
| `main` | Versión endurecida: validación con Pydantic, autenticación obligatoria y RBAC en MongoDB y Elasticsearch. Trabajo de logging/TLS en curso. |

**Estado de las medidas:**

| Medida | Estado |
| --- | --- |
| Despliegue Docker Compose y pruebas iniciales | Verificado |
| Inyección NoSQL y accesos anónimos en la versión vulnerable | Reproducidos |
| Validación estricta de entradas con Pydantic | Implementada y verificada |
| Autenticación y RBAC en MongoDB | Implementados y verificados |
| Autenticación y RBAC en Elasticsearch | Implementados y verificados directamente en Elasticsearch |
| Conexión autenticada FastAPI → Elasticsearch | Configurada; pendiente de confirmar en el README la verificación final de ambos filtros de búsqueda |
| Restricción de puertos a `127.0.0.1` | Configurada |
| Logging adicional de seguridad en FastAPI | En desarrollo; verificación pendiente |
| TLS para MongoDB y Elasticsearch | Pendiente; actualmente se utiliza HTTP/TCP sin cifrado TLS |
| Comparativa final, conclusiones y revisión de entrega | Pendientes de cierre |

## 2. Requisitos previos

- Windows 11 y PowerShell (los comandos pueden adaptarse a otros sistemas).
- Docker Desktop con contenedores Linux y Docker Compose V2.
- Postman para pruebas HTTP.
- Git y una cuenta de GitHub si se desea publicar el repositorio.
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
├── docker-compose.yml
├── .gitattributes
├── .gitignore
└── README.md
```

El archivo `.env`, los archivos de respaldo y las claves privadas **no deben publicarse**. La memoria PDF de la actividad contiene las capturas y explicaciones de las pruebas.

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

El script `scripts/init_mongo.js` crea datos ficticios en la base de datos `tienda` durante la **primera inicialización** de un volumen vacío.

| Usuario de la aplicación | Contraseña de ejemplo | Tipo |
| --- | --- | --- |
| `admin` | `admin123` | Administrador ficticio de la tienda |
| `peter` | `peter123` | Cliente |
| `maria` | `maria123` | Cliente |

Estos usuarios de la colección `usuarios` **no son** cuentas administrativas de MongoDB ni sustituyen la autenticación de la base de datos. El laboratorio conserva las contraseñas ficticias de la aplicación en texto claro para reproducir el caso inicial; en una aplicación real deberían almacenarse mediante un algoritmo de hash de contraseñas apropiado.

Pedidos de ejemplo: un portátil ASUS para `peter` y dos ratones Logitech para `maria`.

El script `scripts/init_elastic.sh` carga tres artículos:

| Artículo | Categoría | Precio |
| --- | --- | ---: |
| Portátil ASUS | Informática | 799 € |
| Ratón Logitech | Accesorios | 25 € |
| Teclado mecánico | Accesorios | 65 € |

**Nota:** Docker Compose no ejecuta automáticamente `init_elastic.sh`. El índice se cargó inicialmente mediante un contenedor temporal con `curl`. Después se exportaron sus tres documentos, se creó un volumen persistente y se restauraron con la API `_bulk`.

## 6. Despliegue y particularidades de la configuración actual

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
MONGO_PASSWORD=REEMPLAZAR_LOCALMENTE
ELASTIC_USER=fastapi_elastic
ELASTIC_PASSWORD=REEMPLAZAR_LOCALMENTE
```

El servicio `fastapi-app` recibe además `MONGO_HOST=mongo`, `MONGO_DATABASE=tienda` y `ELASTIC_HOST=elasticsearch`. En `main.py`, MongoDB utiliza `authSource="tienda"` y la conexión HTTP a Elasticsearch utiliza autenticación Basic con la cuenta técnica.

No se incluyen contraseñas reales en este README. **No basta con crear `.env` para desplegar `main` desde cero:** antes deben existir las cuentas y los roles en las bases de datos.

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

FastAPI se configuró para consultar Elasticsearch mediante `ELASTIC_USER` y `ELASTIC_PASSWORD`, sin usar la cuenta administrativa. La comprobación final de `/articulos?q=*` y `/articulos?q=ASUS` con esta nueva conexión debe quedar registrada al cerrar el apartado.

### 8.4. Puertos, logging y TLS

- **Puertos:** MongoDB, Elasticsearch y FastAPI se publican en `127.0.0.1` para reducir la exposición externa.
- **Logging:** se revisaron los logs estándar de los tres servicios. Los de FastAPI registran peticiones y códigos HTTP; los de MongoDB y Elasticsearch mostraron principalmente eventos operativos. Esto **no equivale a auditoría de seguridad completa**.
- **Logging adicional:** se ha propuesto un middleware de FastAPI para registrar método, ruta, código de respuesta y duración, sin almacenar contraseñas ni cuerpos de petición. Su instalación y prueba final están pendientes de confirmación.
- **TLS:** **todavía no está implementado**. Elasticsearch utiliza HTTP con autenticación Basic y MongoDB no tiene configurado TLS. El acceso limitado a localhost no cifra el tráfico entre contenedores. La activación de TLS y la verificación de certificados son tareas pendientes.

## 9. Pruebas de regresión con Postman

Sobre FastAPI (`http://localhost:8000`), sin añadir autenticación Basic a las peticiones del cliente:

| Prueba | Resultado esperado / verificado |
| --- | --- |
| `GET /health` | `200 OK` — verificado tras RBAC de MongoDB |
| `GET /pedidos` | `200 OK` — verificado tras RBAC de MongoDB |
| `POST /login_mongo` con credenciales válidas | `200 OK` — verificado |
| `POST /login_mongo` con credenciales incorrectas | `401 Unauthorized` — verificado |
| `POST /login_mongo` con `$ne` en `password` | `422 Unprocessable Entity` — verificado |
| `GET /articulos?q=*` | `200 OK`, tres documentos — verificado en la fase inicial; repetir tras autenticación de Elasticsearch |
| `GET /articulos?q=ASUS` | `200 OK`, artículo ASUS — verificado en la fase inicial; repetir tras autenticación de Elasticsearch |

En Postman se han organizado pruebas de funcionamiento inicial, ataques y contramedidas. Antes de exportar la colección, **eliminar contraseñas reales, cabeceras `Authorization` y otros secretos**; si hace falta, sustituirlos por variables de entorno de Postman sin valores compartidos.

## 10. Comprobaciones útiles

### MongoDB: acceso sin credenciales (en `main`)

```powershell
docker compose exec mongo mongosh tienda --quiet --eval 'db.usuarios.findOne()'
```

Resultado esperado: error de autorización.

### MongoDB: conexión de la cuenta técnica

```powershell
docker compose exec mongo mongosh tienda --username fastapi_user --authenticationDatabase tienda --password
```

Dentro de `mongosh`, comprobar las lecturas y verificar que las escrituras son rechazadas.

### Elasticsearch: acceso sin credenciales (en `main`)

```powershell
curl.exe -i "http://localhost:9200/"
```

Resultado esperado: `401 Unauthorized`.

### Elasticsearch: consulta autenticada

```powershell
curl.exe -u fastapi_elastic "http://localhost:9200/articulos/_count"
```

La herramienta solicitará la contraseña; el índice contiene tres documentos. **No incluir contraseñas en la línea de comandos ni en el repositorio.**

### Estado y registros

```powershell
docker compose ps
docker compose logs --tail=30 fastapi-app
docker compose logs --tail=30 mongo
docker compose logs --tail=30 elasticsearch
```

## 11. Riesgos residuales y próximos pasos

1. Completar y verificar el middleware de logging de seguridad; valorar centralización, retención y trazabilidad de eventos.
2. Configurar TLS para las comunicaciones con Elasticsearch y MongoDB, gestionar certificados y validar la cadena de confianza.
3. Confirmar y documentar la regresión final de `/articulos` con el usuario técnico autenticado.
4. Preparar un procedimiento reproducible de inicialización para un clon limpio del repositorio, sin depender del volumen externo local de MongoDB.
5. Completar la comparación antes/después y la reflexión sobre Zero Trust, mínimo privilegio, RGPD y NIS2 en la memoria PDF.
6. Revisar `.gitignore`, el historial de Git y la colección de Postman antes de publicar en GitHub.

**Limitaciones relevantes:** la autenticación de la aplicación de ejemplo todavía compara contraseñas ficticias en texto claro; no hay TLS habilitado y los registros estándar no proporcionan auditoría completa. Estas limitaciones deben distinguirse de las defensas ya verificadas.

## 12. Seguridad del repositorio público

El archivo `.gitignore` debe excluir al menos:

```gitignore
.env
.env.*
!.env.example
/tienda-backup.archive
/articulos-backup.json
/articulos-restore.ndjson
*.key
*.p12
__pycache__/
*.pyc
.venv/
```

`.gitignore` **no elimina secretos que ya estén incluidos en el historial**. Revisar las dos ramas (`main` y `vulnerable`) antes de publicar y sustituir cualquier credencial real comprometida. Los archivos de ejemplo deben contener únicamente valores ficticios.

## 13. Detener el laboratorio

```powershell
docker compose down
```

Este comando detiene y elimina los contenedores y redes del proyecto sin solicitar la eliminación de volúmenes. **No utilizar `docker compose down -v`** salvo que se desee eliminar los volúmenes administrados por Compose y reinicializar el entorno. Los volúmenes externos tienen un tratamiento diferente, pero también deben protegerse frente a eliminaciones manuales.

---

**Documentación académica:** el informe PDF independiente recoge la metodología, las capturas, los ataques, las defensas y su relación con Zero Trust, mínimo privilegio, RGPD y NIS2.
