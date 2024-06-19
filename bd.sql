-- Active: 1718734395482@@127.0.0.1@3306@verificador_almacen

CREATE TABLE Categorias (
    id_categoria INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100),
    descripcion VARCHAR(250),
    imagen VARCHAR(250)
);

CREATE TABLE Productos (
    id_producto INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100),
    descripcion VARCHAR(250),
    imagen VARCHAR(250),
    cantidad INT,
    id_categoria INT,
    FOREIGN KEY (id_categoria) REFERENCES Categorias(id_categoria)
);

ALTER TABLE productos ADD COLUMN id_sucursal INT;

ALTER TABLE productos 
ADD CONSTRAINT id_sucursal 
FOREIGN KEY (id_sucursal) 
REFERENCES sucursales(id_sucursal);

CREATE TABLE Sucursales (
    id_sucursal INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100),
    direccion VARCHAR(250)
);

CREATE TABLE Usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    apellido_p VARCHAR(50),
    apellido_m VARCHAR(50),
    correo VARCHAR(150),
    contrasena VARCHAR(250),
    rol ENUM('Admin', 'Gerente', 'Empleado')
);
CREATE TABLE UsuariosSucursales (
    id_usuarioSucursal INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT,
    id_sucursal INT,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario),
    FOREIGN KEY (id_sucursal) REFERENCES Sucursales(id_sucursal)
);


CREATE TABLE OrdenesVerificación (
    id_ordenVerificacion INT PRIMARY KEY AUTO_INCREMENT,
    estado ENUM('Abierta', 'Cerrada'),
    fecha DATE,
    id_sucursal INT,
    id_usuario INT,
    FOREIGN KEY (id_sucursal) REFERENCES Sucursales(id_sucursal),
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);

CREATE TABLE DetallesÓrdenes (
    id_detallesÓrdenes INT PRIMARY KEY AUTO_INCREMENT,
    cantidad INT,
    id_producto INT,
    id_ordenVerificacion INT,
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto),
    FOREIGN KEY (id_ordenVerificacion) REFERENCES OrdenesVerificación(id_ordenVerificacion)
);


CREATE TABLE Sesiones (
    id_sesion INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT,
    token VARCHAR(255),
    fecha_inicio DATETIME,
    fecha_fin DATETIME,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
);