from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import os

app = Flask(__name__)

# Configuración de la clave secreta
app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta')

# Configuración de la base de datos MySQL en Clever Cloud
db_user = 'utoxyrvuz8fbadhw'
db_password = 'FjgB1gcbXmC4i50ze7UI'
db_host = 'bdqjuxpj0akcxmtxeigj-mysql.services.clever-cloud.com'
db_name = 'bdqjuxpj0akcxmtxeigj'
db_port = '3306'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Definir modelos para cada tabla
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Guardar contraseña en texto plano (no recomendado)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class Mesa(db.Model):
    __tablename__ = 'mesas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='libre')
    comensales = db.Column(db.Integer, nullable=False, default=0)  # Número de comensales actuales
    max_comensales = db.Column(db.Integer, nullable=False)  # Máximo de comensales permitidos

class Extra(db.Model):
    __tablename__ = 'extras'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class PlatoExtras(db.Model):
    __tablename__ = 'plato_extras'
    id = db.Column(db.Integer, primary_key=True)
    plato_id = db.Column(db.Integer, db.ForeignKey('menu.id', ondelete='CASCADE'))
    extra_id = db.Column(db.Integer, db.ForeignKey('extras.id', ondelete='CASCADE'))

    plato = db.relationship('Plato', backref='plato_extras')
    extra = db.relationship('Extra', backref='plato_extras')

class Plato(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    extras = db.Column(db.String(200), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    categoria = db.relationship('Categoria', backref=db.backref('platos', lazy=True))

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(50), nullable=False)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id', ondelete='CASCADE'), nullable=True)  # Si no es del restaurante, puede ser None
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    ubicacion = db.Column(db.String(200), nullable=True)  # Nueva columna para almacenar la dirección del cliente

    # Relación con el modelo Usuario
    usuario = db.relationship('Usuario', backref='pedidos')
    

class Factura(db.Model):
    __tablename__ = 'facturas'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    pagado = db.Column(db.Boolean, default=False)

    # Relación con Pedido
    pedido = db.relationship('Pedido', backref='facturas')

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedidos'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    extras = db.Column(db.String(200), nullable=True)

    # Relación con el modelo Plato (Menu)
    menu = db.relationship('Plato', backref='detalle_pedidos')
# Ruta principal redirige a login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Función de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form['cedula']
        password = request.form['password']
        
        # Consulta a la base de datos para encontrar al usuario por cédula
        user = Usuario.query.filter_by(cedula=cedula).first()
        
        # Verifica si el usuario existe y si la contraseña es correcta
        if user and user.password == password:
            # Guardar información del usuario en la sesión
            session['user_id'] = user.id          # ID del usuario
            session['user_role'] = user.rol        # Rol del usuario (usuario, empleado, administrador)
            session['user_name'] = user.nombre      # Nombre del usuario
            
            # Redirigir al dashboard
            return redirect(url_for('dashboard'))
        else:
            # Mensaje de error si las credenciales son incorrectas
            flash('Cédula o contraseña incorrectos.')

    return render_template('login.html')

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

def iniciar_sesion(usuario):
    session['user_id'] = usuario.id  # Almacenar el ID del usuario en la sesión
    print(f"Usuario {usuario.nombre} ha iniciado sesión.")


# Este archivo define la app Flask principal
if __name__ == '__main__':
    app.run(debug=True)
