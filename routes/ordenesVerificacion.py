from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info
from datetime import datetime

mysql = MySQL()

ordenes_bp = Blueprint('ordenes', __name__)

@ordenes_bp.route('/ordenes', methods=['POST'])
def add_orden_verificacion():
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    rol = user[1]
    id_sucursal_usuario = user[2]

    if rol not in ['Empleado']:
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    estado = data['estado']
    fecha = data['fecha']
    id_sucursal = data['id_sucursal']
    id_usuario = user[0]
    
    if rol == 'Gerente' and id_sucursal != id_sucursal_usuario:
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    
    query_insertion = """
        INSERT INTO OrdenesVerificación (estado, fecha, id_sucursal, id_usuario)
        VALUES (%s, %s, %s, %s)
    """
    
    cur.execute(query_insertion, (estado, fecha, id_sucursal, id_usuario))
    id_orden_verificacion = cur.lastrowid

    detalles = data.get('detalles', [])
    for detalle in detalles:
        id_producto = detalle['id_producto']
        cantidad = detalle['cantidad']
        cur.execute("""
            INSERT INTO DetallesÓrdenes (id_producto, id_ordenVerificacion, cantidad)
            VALUES (%s, %s, %s)
        """, (id_producto, id_orden_verificacion, cantidad))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Orden de verificación añadida correctamente'})

@ordenes_bp.route('/ordenes', methods=['GET'])
def get_all_ordenes():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 401

    rol, id_sucursal_usuario = user_info[1], user_info[2]

    cur = mysql.connection.cursor()
    if rol == 'Admin':
        cur.execute("""
            SELECT ov.id_ordenVerificacion, ov.estado, ov.fecha, ov.id_sucursal, ov.id_usuario,
                   s.nombre as sucursal_nombre, u.nombre as usuario_nombre
            FROM OrdenesVerificación ov
            JOIN Sucursales s ON ov.id_sucursal = s.id_sucursal
            JOIN Usuarios u ON ov.id_usuario = u.id_usuario
        """)
    elif rol in ['Gerente', 'Empleado']:
        cur.execute("""
            SELECT ov.id_ordenVerificacion, ov.estado, ov.fecha, ov.id_sucursal, ov.id_usuario,
                   s.nombre as sucursal_nombre, u.nombre as usuario_nombre
            FROM OrdenesVerificación ov
            JOIN Sucursales s ON ov.id_sucursal = s.id_sucursal
            JOIN Usuarios u ON ov.id_usuario = u.id_usuario
            WHERE ov.id_sucursal = %s
        """, (id_sucursal_usuario,))
    else:
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = cur.fetchall()
    cur.close()

    ordenes = []
    for row in data:
        orden = {
            'id_ordenVerificacion': row[0],
            'estado': row[1],
            'fecha': row[2],
            'sucursal': {
                'id_sucursal': row[3],
                'nombre': row[5]  # Ajustado aquí
            },
            'usuario': {
                'id_usuario': row[4],
                'nombre': row[6]  # Ajustado aquí
            }
        }
        ordenes.append(orden)
    
    return jsonify({'ordenes': ordenes})

@ordenes_bp.route('/ordenes/<id>', methods=['GET'])
def get_orden(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    rol, id_sucursal_usuario = user_info[1], user_info[2]

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT ov.id_ordenVerificacion, ov.estado, ov.fecha, ov.id_sucursal, ov.id_usuario,
               s.nombre as sucursal_nombre, u.nombre as usuario_nombre
        FROM OrdenesVerificación ov
        JOIN Sucursales s ON ov.id_sucursal = s.id_sucursal
        JOIN Usuarios u ON ov.id_usuario = u.id_usuario
        WHERE ov.id_ordenVerificacion = %s
    """, (id,))
    data = cur.fetchone()

    if data:
        if rol == 'Admin' or (rol == 'Gerente' and data[3] == id_sucursal_usuario) or (rol == 'Empleado' and data[3] == id_sucursal_usuario):
            cur.execute("""
                SELECT do.id_detallesÓrdenes, do.cantidad, p.id_producto, p.nombre, p.descripcion, p.imagen
                FROM DetallesÓrdenes do
                JOIN Productos p ON do.id_producto = p.id_producto
                WHERE do.id_ordenVerificacion = %s
            """, (id,))
            detalles = cur.fetchall()

            detalles_orden = []
            for detalle in detalles:
                detalles_orden.append({
                    'id_detallesÓrdenes': detalle[0],
                    'cantidad': detalle[1],
                    'producto': {
                        'id_producto': detalle[2],
                        'nombre': detalle[3],
                        'descripcion': detalle[4],
                    }
                })

            orden = {
                'id_ordenVerificacion': data[0],
                'estado': data[1],
                'fecha': data[2],
                'sucursal': {
                    'id_sucursal': data[3],
                    'nombre': data[5]  # Ajusta el índice aquí
                },
                'usuario': {
                    'id_usuario': data[4],
                    'nombre': data[6]  # Ajusta el índice aquí
                },
                'detalles': detalles_orden
            }

            cur.close()
            return jsonify({'orden': orden})

        else:
            cur.close()
            return jsonify({'error': 'Permisos insuficientes'}), 403

    else:
        cur.close()
        return jsonify({'error': 'Orden no encontrada'}), 404


@ordenes_bp.route('/ordenes/<id>', methods=['PUT'])
def update_orden_verificacion(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    rol = user[1]
    id_sucursal_usuario = user[2]

    if rol not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_sucursal, id_usuario FROM OrdenesVerificación WHERE id_ordenVerificacion = %s", (id,))
    orden = cur.fetchone()

    if not orden:
        cur.close()
        return jsonify({"error": "Orden de verificación no encontrada"}), 404

    if rol == 'Gerente' and orden[0] != id_sucursal_usuario:
        cur.close()
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    estado = data['estado']
    fecha_str = data['fecha']

    # Convertir la fecha al formato adecuado
    try:
        fecha = datetime.strptime(fecha_str, '%a, %d %b %Y %H:%M:%S GMT').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        cur.close()
        return jsonify({"error": "Formato de fecha no válido"}), 400

    id_sucursal = data['id_sucursal']
    id_usuario = orden[1]
    
    query_update = """
        UPDATE OrdenesVerificación
        SET estado = %s, fecha = %s, id_sucursal = %s, id_usuario = %s
        WHERE id_ordenVerificacion = %s
    """
    cur.execute(query_update, (estado, fecha, id_sucursal, id_usuario, id))
    
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Orden de verificación actualizada correctamente'})

@ordenes_bp.route('/ordenes/<id>', methods=['DELETE'])
def delete_orden_verificacion(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    rol = user[1]
    id_sucursal_usuario = user[2]

    if rol not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_sucursal FROM OrdenesVerificación WHERE id_ordenVerificacion = %s", (id,))
    orden = cur.fetchone()

    if not orden:
        cur.close()
        return jsonify({"error": "Orden de verificación no encontrada"}), 404

    if rol == 'Gerente' and orden[0] != id_sucursal_usuario:
        cur.close()
        return jsonify({"error": "No autorizado"}), 403

    cur.execute("DELETE FROM DetallesÓrdenes WHERE id_ordenVerificacion = %s", (id,))
    cur.execute("DELETE FROM OrdenesVerificación WHERE id_ordenVerificacion = %s", (id,))

    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Orden de verificación eliminada correctamente'})
