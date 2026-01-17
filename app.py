from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
# Importante: usamos .strip() para evitar errores por espacios o saltos de línea al final
db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')

if db_url:
    db_url = db_url.strip()  # <--- ESTO CORRIGE TU ERROR PRINCIPAL "postgres\n"

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave_secreta_por_defecto')

db = SQLAlchemy(app)

# --- MODELO DE BASE DE DATOS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(10), unique=True, nullable=False)
    institucion_deportiva = db.Column(db.String(100), nullable=False)
    canton = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    recuperacion_email = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='Invitado')

    def __repr__(self):
        return f'<User {self.username}>'

# --- CREAR TABLAS ---
# Esto asegura que las tablas existan al arrancar la app
with app.app_context():
    db.create_all()

# --- RUTAS ---

@app.route('/')
def home():
    return render_template('login.html')

# --- RUTA DE REPARACIÓN (ÚSALA SIEMPRE QUE CAMBIES ALGO EN LA BD) ---
@app.route('/reparar-base-de-datos')
def reparar_db():
    try:
        db.drop_all()
        db.create_all()
        return "<h1>¡Base de datos limpiada y reparada! Ahora ve a registrar el administrador de nuevo.</h1>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

# --- RUTA: MENÚ PRINCIPAL ---
@app.route('/menu-principal')
def menu_principal():
    # Verificamos si hay un usuario en la sesión
    if 'user_name' in session:
        return render_template('menu_principal.html', nombre_usuario=session['user_name'])
    else:
        flash('Por favor inicia sesión primero.', 'danger')
        return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        # Guardamos el usuario en la sesión
        session['user_name'] = f"{user.nombres} {user.apellidos}"
        return redirect(url_for('menu_principal'))
    else:
        flash('Usuario o contraseña incorrectos.', 'danger')
        return redirect(url_for('home'))

@app.route('/create_account')
def create_account():
    return render_template('account_type.html')

@app.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    opciones_institucion = ["Latacunga", "La Maná", "Pujilí", "Salcedo", "Saquisilí", "Sigchos", "Pangua", "Todos"]
    
    if request.method == 'POST':
        # Verificar si ya existe un administrador
        existing_admin = User.query.filter_by(role='Administrador').first()
        if existing_admin:
            flash('El sistema ya tiene un administrador.', 'danger')
            return render_template('register_admin.html', opciones=opciones_institucion)

        # Capturar datos del formulario
        nombres = request.form.get('nombres')
        apellidos = request.form.get('apellidos')
        cedula = request.form.get('cedula')
        institucion = request.form.get('institucion_deportiva')
        canton = request.form.get('canton')  # <--- FALTABA ESTA LÍNEA EN TU CÓDIGO
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        recuperacion_email = request.form.get('recuperacion_email')

        # Validaciones básicas
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register_admin.html', opciones=opciones_institucion)

        if User.query.filter((User.email == email) | (User.username == username) | (User.cedula == cedula)).first():
             flash('El usuario, correo o cédula ya están registrados.', 'danger')
             return render_template('register_admin.html', opciones=opciones_institucion)

        # Crear nuevo usuario
        hashed_password = generate_password_hash(password)
        
        new_admin = User(
            nombres=nombres, apellidos=apellidos, cedula=cedula, 
            institucion_deportiva=institucion, canton=canton, 
            email=email, username=username, password_hash=hashed_password,
            recuperacion_email=recuperacion_email, role='Administrador'
        )

        try:
            db.session.add(new_admin)
            db.session.commit()
            flash('Administrador registrado con éxito. ¡Ahora inicia sesión!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')
            return render_template('register_admin.html', opciones=opciones_institucion)

    return render_template('register_admin.html', opciones=opciones_institucion)

if __name__ == '__main__':
    app.run(debug=True)
