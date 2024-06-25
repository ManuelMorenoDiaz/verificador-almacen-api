from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info

mysql = MySQL()

sucursales_bp = Blueprint('sucursales', __name__)

@sucursales_bp.route('/sucursales', methods=['POST'])
def add_sucursal():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info or user_info[1] != 'Admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json()
    nombre = data['nombre']
    direccion = data['direccion']
    
    cur = mysql.connection.cursor()
    query_insertion = """
        INSERT INTO Sucursales (nombre, direccion)
        VALUES (%s, %s)
    """
    cur.execute(query_insertion, (nombre, direccion))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Sucursal añadida correctamente'})

@sucursales_bp.route('/sucursales', methods=['GET'])
def get_all_sucursales():
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    cur = mysql.connection.cursor()
    
    if rol == 'Admin':
        query = "SELECT * FROM Sucursales"
        cur.execute(query)
    else:
        query = "SELECT * FROM Sucursales WHERE id_sucursal = %s"
        cur.execute(query, (id_sucursal_usuario,))
    
    data = cur.fetchall()
    cur.close()
    
    sucursales = []
    for row in data:
        sucursal = {
            'id_sucursal': row[0],
            'nombre': row[1],
            'direccion': row[2]
        }
        sucursales.append(sucursal)
    
    return jsonify({'sucursales': sucursales})

@sucursales_bp.route('/sucursales/<id>', methods=['GET'])
def get_sucursal(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info:
        return jsonify({'error': 'Acceso no autorizado'}), 403

    id_usuario, rol, id_sucursal_usuario = user_info

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Sucursales WHERE id_sucursal = %s", (id,))
    data = cur.fetchone()
    cur.close()
    
    if data:
        if rol == 'Admin' or (rol in ['Gerente', 'Empleado'] and int(id) == id_sucursal_usuario):
            sucursal = {
                'id_sucursal': data[0],
                'nombre': data[1],
                'direccion': data[2]
            }
            return jsonify({'sucursal': sucursal})
        else:
            return jsonify({'error': 'Permisos insuficientes'}), 403
    else:
        return jsonify({"error": "Sucursal no encontrada"})

@sucursales_bp.route('/sucursales/<id>', methods=['PUT'])
def update_sucursal(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info or user_info[1] != 'Admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json()
    nombre = data['nombre']
    direccion = data['direccion']
    
    cur = mysql.connection.cursor()
    query_update = """
        UPDATE Sucursales
        SET nombre = %s, direccion = %s
        WHERE id_sucursal = %s
    """
    cur.execute(query_update, (nombre, direccion, id))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': 'Sucursal actualizada correctamente'})

@sucursales_bp.route('/sucursales/<id>', methods=['DELETE'])
def delete_sucursal(id):
    token = request.headers.get('Authorization')
    user_info = get_user_info(token)
    if not user_info or user_info[1] != 'Admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Sucursales WHERE id_sucursal = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'result': 'Sucursal eliminada correctamente'})
