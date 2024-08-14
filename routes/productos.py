from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info
import qrcode
import barcode
from barcode.writer import ImageWriter
import io
import base64

mysql = MySQL()
productos_bp = Blueprint('productos', __name__)

def generate_code_data(product_data):
    # Limpiar los datos para asegurarse de que solo contengan caracteres válidos
    def clean_data(data):
        # Aquí puedes ajustar el reemplazo según tus necesidades
        return data.encode('ascii', 'ignore').decode('ascii')

    # Limpiar los datos del producto
    cleaned_product_data = clean_data(product_data)

    # Generar un código QR con la información completa del producto en formato base64
    qr = qrcode.QRCode(
        version=None,  # Deja que la biblioteca determine la versión automáticamente
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Ajusta el nivel de corrección de errores
        box_size=10,
        border=4
    )
    qr.add_data(cleaned_product_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill='black', back_color='white')
    qr_buffered = io.BytesIO()
    qr_img.save(qr_buffered)
    qr_code_base64 = base64.b64encode(qr_buffered.getvalue()).decode('utf-8')

    # Genera un código de barras con la misma información en formato base64
    code128 = barcode.get_barcode_class('code128')
    barcode_instance = code128(cleaned_product_data, writer=ImageWriter())
    barcode_buffered = io.BytesIO()
    barcode_instance.write(barcode_buffered)
    barcode_base64 = base64.b64encode(barcode_buffered.getvalue()).decode('utf-8')

    return qr_code_base64, barcode_base64



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
    precio = data['precio']  # Nuevo campo

    if rol == 'Gerente' and id_sucursal != id_sucursal_usuario:
        return jsonify({'error': 'Permisos insuficientes para añadir productos a otra sucursal'}), 403
    
    cur = mysql.connection.cursor()
    
    query_insertion = """
        INSERT INTO Productos (nombre, descripcion, imagen, cantidad, id_categoria, id_sucursal, precio)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
        
    cur.execute(query_insertion, (nombre, descripcion, imagen, cantidad, id_categoria, id_sucursal, precio))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Producto añadido correctamente'})

# Obtener todos los productos
@productos_bp.route('/productos', methods=['GET'])
def get_all_productos():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    print(user_info)

    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    cur = mysql.connection.cursor()

    if rol == 'Admin':
        # Administradores pueden ver todos los productos sin importar la sucursal
        query = """
            SELECT p.id_producto, p.nombre, p.descripcion, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal, p.precio
            FROM Productos p
            JOIN Categorias c ON p.id_categoria = c.id_categoria
            JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
        """
        cur.execute(query)
    elif rol in ['Gerente', 'Empleado'] and id_sucursal_usuario is not None:
        # Gerentes y empleados solo pueden ver productos de su sucursal
        query = """
            SELECT p.id_producto, p.nombre, p.descripcion, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal, p.precio
            FROM Productos p
            JOIN Categorias c ON p.id_categoria = c.id_categoria
            JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
            WHERE p.id_sucursal = %s
        """
        cur.execute(query, (id_sucursal_usuario,))
    else:
        cur.close()
        return jsonify({'error': 'Permisos insuficientes o datos inválidos'}), 403

    data = cur.fetchall()
    cur.close()
    
    productos = []
    for row in data:
        product_data = f'{row[0]}|{row[1]}|{row[2]}|{row[4]}|{row[6]}|{row[8]}|{row[9]}'
        qr_code_base64, barcode_base64 = generate_code_data(product_data)
        producto = {
            'id_producto': row[0],
            'nombre': row[1],
            'descripcion': row[2],
            'imagen': row[3],
            'cantidad': row[4],
            'id_categoria': row[5],
            'nombre_categoria': row[6],
            'id_sucursal': row[7],
            'nombre_sucursal': row[8],
            'precio': row[9],
            'qr_code': qr_code_base64,
            'barcode': barcode_base64
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
        SELECT p.id_producto, p.nombre, p.descripcion, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal, p.precio
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
            product_data = f'{data[0]}|{data[1]}|{data[2]}|{data[3]}|{data[4]}|{data[6]}|{data[8]}|{data[9]}'
            qr_code_base64, barcode_base64 = generate_code_data(product_data)
            producto = {
                'id_producto': data[0],
                'nombre': data[1],
                'descripcion': data[2],
                'imagen': data[3],
                'cantidad': data[4],
                'id_categoria': data[5],
                'nombre_categoria': data[6],
                'id_sucursal': data[7],
                'nombre_sucursal': data[8],
                'precio': data[9],
                'qr_code': qr_code_base64,  # Generar base64 QR
                'barcode': barcode_base64  # Generar base64 Código de barras
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
    precio = data['precio']  # Nuevo campo

    if rol == 'Gerente' and id_sucursal != id_sucursal_usuario:
        return jsonify({'error': 'Permisos insuficientes para actualizar productos en otra sucursal'}), 403
    
    cur = mysql.connection.cursor()
    
    query_update = """
        UPDATE Productos
        SET nombre = %s, descripcion = %s, imagen = %s, cantidad = %s, id_categoria = %s, id_sucursal = %s, precio = %s
        WHERE id_producto = %s
    """
        
    cur.execute(query_update, (nombre, descripcion, imagen, cantidad, id_categoria, id_sucursal, precio, id))
    
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

    cur = mysql.connection.cursor()
    
    query_delete = "DELETE FROM Productos WHERE id_producto = %s"
    
    cur.execute(query_delete, (id,))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Producto eliminado correctamente'})
