from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Importa los blueprints
from routes.usuarios import usuarios_bp
from routes.productos import productos_bp
from routes.categorias import categorias_bp
from routes.sucursales import sucursales_bp
from routes.ordenesVerificacion import ordenes_bp
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

# Configuración de CORS
CORS(app, 
     resources={r"/*": {"origins": "*"}},  # Permite todos los orígenes para todas las rutas
     supports_credentials=True,  # Habilita el soporte para credenciales
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]  # Métodos permitidos
)

# Registra los blueprints
app.register_blueprint(usuarios_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(sucursales_bp)
app.register_blueprint(ordenes_bp)
app.register_blueprint(usuarios_sucursales_bp)

@app.route('/')
def home():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


