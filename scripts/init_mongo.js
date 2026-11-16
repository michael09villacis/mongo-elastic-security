db = db.getSiblingDB("tienda");

// Crear colección de usuarios
db.usuarios.insertMany([
    {
        username: "admin",
        password: "admin123",
        rol: "administrador"
    },
    {
        username: "peter",
        password: "peter123",
        rol: "cliente"
    },
    {
        username: "maria",
        password: "maria123",
        rol: "cliente"
    }
]);

// Crear colección de pedidos
db.pedidos.insertMany([
    {
        producto: "Portátil ASUS",
        cantidad: 1,
        usuario: "peter"
    },
    {
        producto: "Ratón Logitech",
        cantidad: 2,
        usuario: "maria"
    }
]);

print("Base de datos tienda inicializada correctamente");