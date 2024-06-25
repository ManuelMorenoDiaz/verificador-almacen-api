from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from routes.usuarios import get_user_info
mysql = MySQL()

categorias_bp = Blueprint('categorias', __name__)

@categorias_bp.route('/categorias', methods=['POST'])
def add_categoria():
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] != 'Admin':
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    nombre = data['nombre']
    descripcion = data['descripcion']
    imagen = data['imagen']
    
    cur = mysql.connection.cursor()
    
    query_insertion = """
        INSERT INTO Categorias (nombre, descripcion, imagen)
        VALUES (%s, %s, %s)
    """
        
    cur.execute(query_insertion, (nombre, descripcion, imagen))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Categoria añadida correctamente'})

@categorias_bp.route('/categorias', methods=['GET'])
def get_all_categorias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Categorias")
    data = cur.fetchall()
    cur.close()
    
    categorias = []
    for row in data:
        categoria = {
            'id_categoria': row[0],
            'nombre': row[1],
            'descripcion': row[2],
            'imagen': row[3]
        }
        categorias.append(categoria)
    
    return jsonify({'categorias': categorias})

@categorias_bp.route('/categorias/<id>', methods=['GET'])
def get_categoria(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Categorias WHERE id_categoria = %s", (id,))
    data = cur.fetchone()
    cur.close()
    
    if data:
        categoria = {
            'id_categoria': data[0],
            'nombre': data[1],
            'descripcion': data[2],
            'imagen': data[3]
        }
        return jsonify({'categoria': categoria})
    else:
        return jsonify({"error": "Categoria no encontrada"})

@categorias_bp.route('/categorias/<id>', methods=['PUT'])
def update_categoria(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] != 'Admin':
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    nombre = data['nombre']
    descripcion = data['descripcion']
    imagen = data['imagen']
    
    cur = mysql.connection.cursor()
    
    query_update = """
        UPDATE Categorias
        SET nombre = %s, descripcion = %s, imagen = %s
        WHERE id_categoria = %s
    """
        
    cur.execute(query_update, (nombre, descripcion, imagen, id))
    
    mysql.connection.commit()
    
    cur.close()
    
    return jsonify({'message': 'Categoria actualizada correctamente'})

@categorias_bp.route('/categorias/<id>', methods=['DELETE'])
def delete_categoria(id):
    user = get_user_info(request.headers.get('Authorization'))
    if not user or user[1] != 'Admin':
        return jsonify({"error": "No autorizado"}), 403

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Categorias WHERE id_categoria = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'result': 'Categoria eliminada correctamente'})
