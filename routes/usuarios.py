from flask import Blueprint, request, jsonify, session
from flask_mysqldb import MySQL
import uuid
from datetime import datetime
import hashlib

mysql = MySQL()

usuarios_bp = Blueprint('usuarios', __name__)

def get_user_info(token):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id_usuario, u.rol, us.id_sucursal
        FROM Usuarios u
        JOIN Sesiones s ON u.id_usuario = s.id_usuario
        LEFT JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario
        WHERE s.token = %s AND s.fecha_fin IS NULL
    """, (token,))
    user = cur.fetchone()
    cur.close()
    return user

@usuarios_bp.route('/usuarios', methods=['POST'])
def add_usuario():
    data = request.get_json()
    nombre = data['nombre']
    apellido_p = data['apellido_p']
    apellido_m = data['apellido_m']
    correo = data['correo']
    rol = data['rol']
    contrasena = data['contrasena']
    
    # Verificar que no haya usuarios con el mismo nombre y apellido en la misma sucursal
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM Usuarios u
        JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario
        WHERE u.nombre = %s AND u.apellido_p = %s AND u.apellido_m = %s
    """, (nombre, apellido_p, apellido_m))
    count = cur.fetchone()[0]
    if count > 0:
        return jsonify({'error': 'Ya existe un usuario con el mismo nombre y apellidos en la misma sucursal'})

    # Hashear la contraseña
    hashed_contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
    
    query_insertion = """
        INSERT INTO Usuarios (nombre, apellido_p, apellido_m, correo, rol, contrasena)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
        
    cur.execute(query_insertion, (nombre, apellido_p, apellido_m, correo, rol, hashed_contrasena))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Usuario añadido correctamente'})

@usuarios_bp.route('/usuarios', methods=['GET'])
def get_all_usuarios():
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    cur = mysql.connection.cursor()
    if user[1] == 'Admin':
        cur.execute("SELECT id_usuario, nombre, apellido_p, apellido_m, correo, rol FROM Usuarios")
    elif user[1] == 'Gerente':
        cur.execute("""
            SELECT u.id_usuario, u.nombre, u.apellido_p, u.apellido_m, u.correo, u.rol
            FROM Usuarios u
            JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario
            WHERE us.id_sucursal = %s
        """, (user[2],))
    else:
        return jsonify({"error": "No autorizado"}), 403

    data = cur.fetchall()
    cur.close()
    
    usuarios = []
    for row in data:
        usuario = {
            'id_usuario': row[0],
            'nombre': row[1],
            'apellido_p': row[2],
            'apellido_m': row[3],
            'correo': row[4],
            'rol': row[5]
        }
        usuarios.append(usuario)
    
    return jsonify({'usuarios': usuarios})

@usuarios_bp.route('/usuarios/<id>', methods=['GET'])
def get_usuario(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id_usuario, u.nombre, u.apellido_p, u.apellido_m, u.correo, u.rol, us.id_sucursal
        FROM Usuarios u
        LEFT JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario
        WHERE u.id_usuario = %s
    """, (id,))
    data = cur.fetchone()
    cur.close()

    if data:
        if user[1] == 'Admin' or (user[1] == 'Gerente' and user[2] == data[6]):
            usuario = {
                'id_usuario': data[0],
                'nombre': data[1],
                'apellido_p': data[2],
                'apellido_m': data[3],
                'correo': data[4],
                'rol': data[5]
            }
            return jsonify({'usuario': usuario})
        else:
            return jsonify({"error": "No autorizado"}), 403
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404

@usuarios_bp.route('/usuarios/<id>', methods=['PUT'])
def update_usuario(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT us.id_sucursal FROM Usuarios u LEFT JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario WHERE u.id_usuario = %s", (id,))
    user_data = cur.fetchone()
    cur.close()

    if user[1] != 'Admin' and not (user[1] == 'Gerente' and user[2] == user_data[0]):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    nombre = data['nombre']
    apellido_p = data['apellido_p']
    apellido_m = data['apellido_m']
    correo = data['correo']
    rol = data['rol']
    
    cur = mysql.connection.cursor()
    
    query_update = """
        UPDATE Usuarios
        SET nombre = %s, apellido_p = %s, apellido_m = %s, correo = %s, rol = %s
        WHERE id_usuario = %s
    """
        
    cur.execute(query_update, (nombre, apellido_p, apellido_m, correo, rol, id))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Usuario actualizado correctamente'})

@usuarios_bp.route('/usuarios/<id>', methods=['DELETE'])
def delete_usuario(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT us.id_sucursal FROM Usuarios u LEFT JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario WHERE u.id_usuario = %s", (id,))
    user_data = cur.fetchone()
    cur.close()

    if user[1] != 'Admin' and not (user[1] == 'Gerente' and user[2] == user_data[0]):
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Usuarios WHERE id_usuario = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'result': 'Usuario eliminado correctamente'})

@usuarios_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    correo = data['correo']
    contrasena = data['contrasena']
    
    # Hashear la contraseña proporcionada
    hashed_contrasena = hashlib.sha256(contrasena.encode()).hexdigest()
    
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id_usuario, u.nombre, u.apellido_p, u.apellido_m, u.correo, u.rol, us.id_sucursal
        FROM Usuarios u
        LEFT JOIN UsuariosSucursales us ON u.id_usuario = us.id_usuario
        WHERE u.correo = %s AND u.contrasena = %s
    """, (correo, hashed_contrasena))
    user = cur.fetchone()
    cur.close()
    
    if user:
        token = str(uuid.uuid4())
        fecha_inicio = datetime.now()
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Sesiones (id_usuario, token, fecha_inicio) VALUES (%s, %s, %s)", (user[0], token, fecha_inicio))
        mysql.connection.commit()
        cur.close()
        
        user_info = {
            'id_usuario': user[0],
            'nombre': user[1],
            'apellido_p': user[2],
            'apellido_m': user[3],
            'correo': user[4],
            'rol': user[5],
            'id_sucursal': user[6]
        }
        
        return jsonify({'message': 'Inicio de sesión exitoso', 'token': token, 'user': user_info})
    else:
        return jsonify({'error': 'Correo o contraseña incorrectos'})

@usuarios_bp.route('/logout', methods=['POST'])
def logout():
    data = request.get_json()
    token = data['token']
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_sesion FROM Sesiones WHERE token = %s", (token,))
    sesion = cur.fetchone()
    
    if sesion:
        fecha_fin = datetime.now()
        cur.execute("UPDATE Sesiones SET fecha_fin = %s WHERE token = %s", (fecha_fin, token))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Cierre de sesión exitoso'})
    else:
        cur.close()
        return jsonify({'error': 'Token no válido o ya expirado'})
