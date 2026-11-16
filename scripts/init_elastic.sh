#!/bin/sh

ELASTIC_URL="http://elasticsearch:9200"

# Insertar los artículos de la tienda
curl -sS -f -X PUT "$ELASTIC_URL/articulos/_doc/1" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Portátil ASUS","categoria":"Informática","precio":799}' || exit 1

curl -sS -f -X PUT "$ELASTIC_URL/articulos/_doc/2" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Ratón Logitech","categoria":"Accesorios","precio":25}' || exit 1

curl -sS -f -X PUT "$ELASTIC_URL/articulos/_doc/3?refresh=true" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Teclado mecánico","categoria":"Accesorios","precio":65}' || exit 1

echo "Artículos cargados correctamente"
