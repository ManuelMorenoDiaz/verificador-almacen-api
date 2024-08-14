from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info

mysql = MySQL()

detalles_ordenes_bp = Blueprint('detalles_ordenes', __name__)

# Crear un nuevo Detalle de Orden
@detalles_ordenes_bp.route('/detalles_ordenes', methods=['POST'])
def add_detalle_orden():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info or user_info[1] != 'Admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json()
    cantidad = data['cantidad']
    id_producto = data['id_producto']
    id_ordenVerificacion = data['id_ordenVerificacion']

    cur = mysql.connection.cursor()
    query_insertion = """
        INSERT INTO DetallesÓrdenes (cantidad, id_producto, id_ordenVerificacion)
        VALUES (%s, %s, %s)
    """
    cur.execute(query_insertion, (cantidad, id_producto, id_ordenVerificacion))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Detalle de Orden añadido correctamente'})

# Obtener todos los Detalles de Orden
@detalles_ordenes_bp.route('/detalles_ordenes', methods=['GET'])
def get_all_detalles_ordenes():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    cur = mysql.connection.cursor()
    query = "SELECT * FROM DetallesÓrdenes"
    cur.execute(query)
    data = cur.fetchall()
    cur.close()

    detalles = []
    for row in data:
        detalle = {
            'id_detallesÓrdenes': row[0],
            'cantidad': row[1],
            'id_producto': row[2],
            'id_ordenVerificacion': row[3]
        }
        detalles.append(detalle)

    return jsonify({'detalles_ordenes': detalles})

# Obtener un Detalle de Orden específico
@detalles_ordenes_bp.route('/detalles_ordenes/<id>', methods=['GET'])
def get_detalle_orden(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM DetallesÓrdenes WHERE id_detallesÓrdenes = %s", (id,))
    data = cur.fetchone()
    cur.close()

    if data:
        detalle = {
            'id_detallesÓrdenes': data[0],
            'cantidad': data[1],
            'id_producto': data[2],
            'id_ordenVerificacion': data[3]
        }
        return jsonify({'detalle_orden': detalle})
    else:
        return jsonify({"error": "Detalle de Orden no encontrado"})

# Actualizar un Detalle de Orden
@detalles_ordenes_bp.route('/detalles_ordenes/<id>', methods=['PUT'])
def update_detalle_orden(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info or user_info[1] != 'Admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json()
    cantidad = data['cantidad']
    id_producto = data['id_producto']
    id_ordenVerificacion = data['id_ordenVerificacion']

    cur = mysql.connection.cursor()
    query_update = """
        UPDATE DetallesÓrdenes
        SET cantidad = %s, id_producto = %s, id_ordenVerificacion = %s
        WHERE id_detallesÓrdenes = %s
    """
    cur.execute(query_update, (cantidad, id_producto, id_ordenVerificacion, id))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Detalle de Orden actualizado correctamente'})

# Eliminar un Detalle de Orden
@detalles_ordenes_bp.route('/detalles_ordenes/<id>', methods=['DELETE'])
def delete_detalle_orden(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info or user_info[1] != 'Admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM DetallesÓrdenes WHERE id_detallesÓrdenes = %s", (id,))
        mysql.connection.commit()
        return jsonify({'result': 'Detalle de Orden eliminado correctamente'})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
