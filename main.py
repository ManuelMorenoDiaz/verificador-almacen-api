from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Importa los blueprints
from routes.usuarios import usuarios_bp
from routes.productos import productos_bp
from routes.categorias import categorias_bp
from routes.sucursales import sucursales_bp
# from routes.ordenesVerificacion import ordenesVerificacion_bp
# from routes.detallesOrdenes import detallesOrdenes_bp
from routes.usuariosSucursales import usuarios_sucursales_bp
app = Flask(__name__)

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'verificador_almacen'

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'rodr'

mysql = MySQL(app)
jwt = JWTManager(app)

# Habilita CORS
CORS(app, supports_credentials=True)

# Registra los blueprints
app.register_blueprint(usuarios_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(sucursales_bp)
# app.register_blueprint(ordenesVerificacion_bp)
# app.register_blueprint(detallesOrdenes_bp)
app.register_blueprint(usuarios_sucursales_bp)

if __name__ == '__main__':
    app.run(debug=True)
