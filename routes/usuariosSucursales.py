from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info

mysql = MySQL()

usuarios_sucursales_bp = Blueprint('usuarios_sucursales', __name__)

# Crear una asignación de usuario a sucursal
@usuarios_sucursales_bp.route('/usuarios_sucursales', methods=['POST'])
def add_usuario_sucursal():
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    id_usuario = data['id_usuario']
    id_sucursal = data['id_sucursal']
    
    # Verificar que no exista ya una asignación para el mismo usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM UsuariosSucursales WHERE id_usuario = %s AND id_sucursal = %s", (id_usuario, id_sucursal))
    count = cur.fetchone()[0]
    if count > 0:
        return jsonify({'error': 'El usuario ya está asignado a esta sucursal'}), 400
    
    query_insertion = """
        INSERT INTO UsuariosSucursales (id_usuario, id_sucursal)
        VALUES (%s, %s)
    """
        
    cur.execute(query_insertion, (id_usuario, id_sucursal))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Usuario asignado a sucursal correctamente'})

# Obtener todas las asignaciones de usuarios a sucursales
@usuarios_sucursales_bp.route('/usuarios_sucursales', methods=['GET'])
def get_all_usuarios_sucursales():
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    if user[1] == 'Admin':
        cur.execute("""
            SELECT us.id_usuarioSucursal, u.nombre, u.apellido_p, u.apellido_m, u.correo, u.rol, s.nombre AS nombre_sucursal, s.direccion
            FROM UsuariosSucursales us
            JOIN Usuarios u ON us.id_usuario = u.id_usuario
            JOIN Sucursales s ON us.id_sucursal = s.id_sucursal
        """)
    else:
        cur.execute("""
            SELECT us.id_usuarioSucursal, u.nombre, u.apellido_p, u.apellido_m, u.correo, u.rol, s.nombre AS nombre_sucursal, s.direccion
            FROM UsuariosSucursales us
            JOIN Usuarios u ON us.id_usuario = u.id_usuario
            JOIN Sucursales s ON us.id_sucursal = s.id_sucursal
            WHERE us.id_sucursal = %s
        """, (user[2],))
    data = cur.fetchall()
    cur.close()
    
    usuarios_sucursales = []
    for row in data:
        usuario_sucursal = {
            'id_usuarioSucursal': row[0],
            'nombre': row[1],
            'apellido_p': row[2],
            'apellido_m': row[3],
            'correo': row[4],
            'rol': row[5],
            'nombre_sucursal': row[6],
            'direccion': row[7]
        }
        usuarios_sucursales.append(usuario_sucursal)
    
    return jsonify({'usuarios_sucursales': usuarios_sucursales})

# Obtener una asignación de usuario a sucursal por ID
@usuarios_sucursales_bp.route('/usuarios_sucursales/<id>', methods=['GET'])
def get_usuario_sucursal(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT us.id_usuarioSucursal, u.nombre, u.apellido_p, u.apellido_m, u.correo, u.rol, s.nombre AS nombre_sucursal, s.direccion
        FROM UsuariosSucursales us
        JOIN Usuarios u ON us.id_usuario = u.id_usuario
        JOIN Sucursales s ON us.id_sucursal = s.id_sucursal
        WHERE us.id_usuarioSucursal = %s
    """, (id,))
    data = cur.fetchone()
    cur.close()
    
    if data:
        if user[1] == 'Admin' or (user[1] == 'Gerente' and user[2] == data[5]):
            usuario_sucursal = {
                'id_usuarioSucursal': data[0],
                'nombre': data[1],
                'apellido_p': data[2],
                'apellido_m': data[3],
                'correo': data[4],
                'rol': data[5],
                'nombre_sucursal': data[6],
                'direccion': data[7]
            }
            return jsonify({'usuario_sucursal': usuario_sucursal})
        else:
            return jsonify({"error": "No autorizado"}), 403
    else:
        return jsonify({"error": "Asignación no encontrada"}), 404

# Actualizar una asignación de usuario a sucursal
@usuarios_sucursales_bp.route('/usuarios_sucursales/<id>', methods=['PUT'])
def update_usuario_sucursal(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    id_usuario = data['id_usuario']
    id_sucursal = data['id_sucursal']
    
    # Verificar que no exista ya una asignación para el mismo usuario
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM UsuariosSucursales WHERE id_usuario = %s AND id_sucursal = %s", (id_usuario, id_sucursal))
    count = cur.fetchone()[0]
    if count > 0:
        return jsonify({'error': 'El usuario ya está asignado a esta sucursal'}), 400
    
    query_update = """
        UPDATE UsuariosSucursales
        SET id_usuario = %s, id_sucursal = %s
        WHERE id_usuarioSucursal = %s
    """
        
    cur.execute(query_update, (id_usuario, id_sucursal, id))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Asignación actualizada correctamente'})

# Eliminar una asignación de usuario a sucursal
@usuarios_sucursales_bp.route('/usuarios_sucursales/<id>', methods=['DELETE'])
def delete_usuario_sucursal(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] not in ['Admin', 'Gerente']:
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM UsuariosSucursales WHERE id_usuarioSucursal = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'result': 'Asignación eliminada correctamente'})
