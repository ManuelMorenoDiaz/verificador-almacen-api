from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info
mysql = MySQL()

productos_bp = Blueprint('productos', __name__)

# Crear un producto
@productos_bp.route('/productos', methods=['POST'])
def add_producto():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    if rol not in ['Admin', 'Gerente']:
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json()
    nombre = data['nombre']
    descripcion = data['descripcion']
    imagen = data['imagen']
    cantidad = data['cantidad']
    id_categoria = data['id_categoria']
    id_sucursal = data['id_sucursal']

    if rol == 'Gerente' and id_sucursal != id_sucursal_usuario:
        return jsonify({'error': 'Permisos insuficientes para añadir productos a otra sucursal'}), 403
    
    cur = mysql.connection.cursor()
    
    query_insertion = """
        INSERT INTO Productos (nombre, descripcion, imagen, cantidad, id_categoria, id_sucursal)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
        
    cur.execute(query_insertion, (nombre, descripcion, imagen, cantidad, id_categoria, id_sucursal))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Producto añadido correctamente'})

# Obtener todos los productos
@productos_bp.route('/productos', methods=['GET'])
def get_all_productos():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    cur = mysql.connection.cursor()
    
    if rol == 'Admin':
        query = """
            SELECT p.id_producto, p.nombre, p.descripcion, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal
            FROM Productos p
            JOIN Categorias c ON p.id_categoria = c.id_categoria
            JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
        """
        cur.execute(query)
    elif rol in ['Gerente', 'Empleado']:
        query = """
            SELECT p.id_producto, p.nombre, p.descripcion, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal
            FROM Productos p
            JOIN Categorias c ON p.id_categoria = c.id_categoria
            JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
            WHERE p.id_sucursal = %s
        """
        cur.execute(query, (id_sucursal_usuario,))
    
    data = cur.fetchall()
    cur.close()
    
    productos = []
    for row in data:
        producto = {
            'id_producto': row[0],
            'nombre': row[1],
            'descripcion': row[2],
            'imagen': row[3],
            'cantidad': row[4],
            'id_categoria': row[5],
            'nombre_categoria': row[6],
            'id_sucursal': row[7],
            'nombre_sucursal': row[8]
        }
        productos.append(producto)
    
    return jsonify({'productos': productos})

# Obtener un producto por ID
@productos_bp.route('/productos/<id>', methods=['GET'])
def get_producto(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    cur = mysql.connection.cursor()
    
    query = """
        SELECT p.id_producto, p.nombre, p.descripcion, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal
        FROM Productos p
        JOIN Categorias c ON p.id_categoria = c.id_categoria
        JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
        WHERE p.id_producto = %s
    """
    cur.execute(query, (id,))
    data = cur.fetchone()
    cur.close()
    
    if data:
        if rol in ['Admin', 'Gerente'] or (rol == 'Empleado' and data[7] == id_sucursal_usuario):
            producto = {
                'id_producto': data[0],
                'nombre': data[1],
                'descripcion': data[2],
                'imagen': data[3],
                'cantidad': data[4],
                'id_categoria': data[5],
                'nombre_categoria': data[6],
                'id_sucursal': data[7],
                'nombre_sucursal': data[8]
            }
            return jsonify({'producto': producto})
        else:
            return jsonify({'error': 'Permisos insuficientes'}), 403
    else:
        return jsonify({"error": "Producto no encontrado"})

# Actualizar un producto
@productos_bp.route('/productos/<id>', methods=['PUT'])
def update_producto(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    if rol not in ['Admin', 'Gerente']:
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json()
    nombre = data['nombre']
    descripcion = data['descripcion']
    imagen = data['imagen']
    cantidad = data['cantidad']
    id_categoria = data['id_categoria']
    id_sucursal = data['id_sucursal']

    if rol == 'Gerente' and id_sucursal != id_sucursal_usuario:
        return jsonify({'error': 'Permisos insuficientes para actualizar productos en otra sucursal'}), 403
    
    cur = mysql.connection.cursor()
    
    query_update = """
        UPDATE Productos
        SET nombre = %s, descripcion = %s, imagen = %s, cantidad = %s, id_categoria = %s, id_sucursal = %s
        WHERE id_producto = %s
    """
        
    cur.execute(query_update, (nombre, descripcion, imagen, cantidad, id_categoria, id_sucursal, id))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Producto actualizado correctamente'})

# Eliminar un producto
@productos_bp.route('/productos/<id>', methods=['DELETE'])
def delete_producto(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    if rol not in ['Admin', 'Gerente']:
        return jsonify({'error': 'Permisos insuficientes'}), 403

    if rol == 'Gerente':
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_sucursal FROM Productos WHERE id_producto = %s", (id,))
        producto = cur.fetchone()
        cur.close()
        if producto and producto[0] != id_sucursal_usuario:
            return jsonify({'error': 'Permisos insuficientes para eliminar productos de otra sucursal'}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Productos WHERE id_producto = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'result': 'Producto eliminado correctamente'})
