from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
import io
import base64
import os

mysql = MySQL()

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/productos', methods=['POST'])
def add_producto():
    data = request.get_json()
    nombre = data['nombre']
    descripcion = data['descripcion']
    imagen = data['imagen']
    cantidad = data['cantidad']
    id_categoria = data['id_categoria']
    id_sucursal = data['id_sucursal']  # Agregar el campo id_sucursal
    
    # Generar el código de barras
    barcode_buffer = io.BytesIO()
    barcode = Code128(nombre[:20], writer=ImageWriter())  # Limitar la longitud del nombre a 20 caracteres
    barcode.write(barcode_buffer)
    barcode_data = base64.b64encode(barcode_buffer.getvalue()).decode('utf-8')[:1000]  # Limitar la longitud de los datos codificados a 1000 caracteres
    
    # Generar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(nombre[:20])  # Limitar la longitud del nombre a 20 caracteres
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_data = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')  # Limitar la longitud de los datos codificados a 1000 caracteres
    
    cur = mysql.connection.cursor()
    
    query_insertion = """
        INSERT INTO Productos (nombre, descripcion, codigo_barras, codigo_qr, imagen, cantidad, id_categoria, id_sucursal)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
        
    cur.execute(query_insertion, (nombre, descripcion, barcode_data, qr_data, imagen, cantidad, id_categoria, id_sucursal))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Producto añadido correctamente'})

@productos_bp.route('/productos', methods=['GET'])
def get_all_productos():
    cur = mysql.connection.cursor()
    query = """
        SELECT p.id_producto, p.nombre, p.descripcion, p.codigo_barras, p.codigo_qr, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal
        FROM Productos p
        JOIN Categorias c ON p.id_categoria = c.id_categoria
        JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
    """
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    
    productos = []
    for row in data:
        producto = {
            'id_producto': row[0],
            'nombre': row[1],
            'descripcion': row[2],
            'codigo_barras': row[3],
            'codigo_qr': row[4],
            'imagen': row[5],
            'cantidad': row[6],
            'id_categoria': row[7],
            'nombre_categoria': row[8],
            'id_sucursal': row[9],
            'nombre_sucursal': row[10]
        }
        productos.append(producto)
    
    return jsonify({'productos': productos})

@productos_bp.route('/productos/<id>', methods=['GET'])
def get_producto(id):
    cur = mysql.connection.cursor()
    query = """
        SELECT p.id_producto, p.nombre, p.descripcion, p.codigo_barras, p.codigo_qr, p.imagen, p.cantidad, p.id_categoria, c.nombre AS nombre_categoria, p.id_sucursal, s.nombre AS nombre_sucursal
        FROM Productos p
        JOIN Categorias c ON p.id_categoria = c.id_categoria
        JOIN Sucursales s ON p.id_sucursal = s.id_sucursal
        WHERE p.id_producto = %s
    """
    cur.execute(query, (id,))
    data = cur.fetchone()
    cur.close()
    
    if data:
        producto = {
            'id_producto': data[0],
            'nombre': data[1],
            'descripcion': data[2],
            'codigo_barras': data[3],  # Decodificar y guardar el código de barras
            'codigo_qr': data[4],  # Decodificar y guardar el código QR
            'imagen': data[5],
            'cantidad': data[6],
            'id_categoria': data[7],
            'nombre_categoria': data[8],
            'id_sucursal': data[9],
            'nombre_sucursal': data[10]
        }
        return jsonify({'producto': producto})
    else:
        return jsonify({"error": "Producto no encontrado"})

@productos_bp.route('/productos/<id>', methods=['PUT'])
def update_producto(id):
    data = request.get_json()
    nombre = data['nombre']
    descripcion = data['descripcion']
    imagen = data['imagen']
    cantidad = data['cantidad']
    id_categoria = data['id_categoria']
    id_sucursal = data['id_sucursal']  # Agregar el campo id_sucursal
    
    # Generar el código de barras
    barcode_buffer = io.BytesIO()
    barcode = Code128(nombre[:20], writer=ImageWriter())  # Limitar la longitud del nombre a 20 caracteres
    barcode.write(barcode_buffer)
    barcode_data = base64.b64encode(barcode_buffer.getvalue()).decode('utf-8')[:1000]  # Limitar la longitud de los datos codificados a 1000 caracteres
    
    # Generar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(nombre[:20])  # Limitar la longitud del nombre a 20 caracteres
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_data = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')  # Limitar la longitud de los datos codificados a 1000 caracteres
    
    cur = mysql.connection.cursor()
    
    query_update = """
        UPDATE Productos
        SET nombre = %s, descripcion = %s, codigo_barras = %s, codigo_qr = %s, imagen = %s, cantidad = %s, id_categoria = %s, id_sucursal = %s
        WHERE id_producto = %s
    """
        
    cur.execute(query_update, (nombre, descripcion, barcode_data, qr_data, imagen, cantidad, id_categoria, id_sucursal, id))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Producto actualizado correctamente'})

@productos_bp.route('/productos/<id>', methods=['DELETE'])
def delete_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Productos WHERE id_producto = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'result': 'Producto eliminado correctamente'})
