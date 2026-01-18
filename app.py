from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DEL SISTEMA
# ==========================================
db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta_y_segura'

# ==========================================
# CONFIGURACIÓN DEL CORREO (GMAIL)
# ==========================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

# --- TUS DATOS DE GMAIL ---
app.config['MAIL_USERNAME'] = 'luisalbertotoalombotoapaxi@gmail.com'
app.config['MAIL_PASSWORD'] = 'dwjl pwrc wguz gtvi'
# -------------------------------

mail = Mail(app)
db = SQLAlchemy(app)


# ==========================================
# MODELO DE BASE DE DATOS
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_granja = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(50), nullable=False)
    provincia = db.Column(db.String(50), nullable=False)
    ciudad = db.Column(db.String(50), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    recuperacion_email = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='Propietario')

    def __repr__(self):
        return f'<User {self.username}>'


with app.app_context():
    db.create_all()


# ==========================================
# RUTAS PRINCIPALES
# ==========================================

@app.route('/')
def home():
    if 'user_name' in session:
        return redirect(url_for('menu_principal'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_name'] = f"{user.nombres} {user.apellidos}"
        return redirect(url_for('menu_principal'))
    else:
        flash('Credenciales incorrectas.', 'danger')
        return redirect(url_for('home'))


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    # Verificar si ya existe un usuario
    usuario_existente = User.query.first()
    if usuario_existente:
        flash('⚠️ ACCESO RESTRINGIDO: Ya existe un Propietario registrado.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')

            if password != confirm:
                flash('Las contraseñas no coinciden', 'danger')
                return render_template('register_admin.html')

            hashed_password = generate_password_hash(password)

            # --- CORRECCIÓN AQUÍ ---
            # Capturamos el único email del formulario
            email_unico = request.form.get('email')

            new_user = User(
                nombre_granja=request.form.get('nombre_granja'),
                cedula=request.form.get('cedula'),
                nombres=request.form.get('nombres'),
                apellidos=request.form.get('apellidos'),
                pais=request.form.get('pais'),
                provincia=request.form.get('provincia'),
                ciudad=request.form.get('ciudad'),
                direccion=request.form.get('direccion'),

                username=request.form.get('username'),
                password_hash=hashed_password,

                # Usamos el mismo email para login y para recuperación
                email=email_unico,
                recuperacion_email=email_unico
            )

            db.session.add(new_user)
            db.session.commit()
            flash('✅ Cuenta creada exitosamente. Inicie sesión.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error al crear cuenta: {str(e)}', 'danger')
            return render_template('register_admin.html')

    return render_template('register_admin.html')


# ==========================================
# SISTEMA DE RECUPERACIÓN DE CLAVE
# ==========================================

# PASO 1: Enviar Código por Correo
@app.route('/olvide-contrasena', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email_input = request.form.get('email')

        # Busca el usuario usando ese correo en cualquiera de los dos campos (aunque ahora sean el mismo)
        user = User.query.filter((User.recuperacion_email == email_input) | (User.email == email_input)).first()

        if user:
            token = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

            session['reset_token'] = token
            session['reset_email'] = user.email

            # Envío del correo real
            try:
                msg = Message('Código de Recuperación - Pico y Pluma',
                              sender=app.config['MAIL_USERNAME'],
                              recipients=[email_input])
                msg.body = f"Hola {user.nombres},\n\nSu código de seguridad es: {token}\n\nSi no solicitó esto, ignore este mensaje."
                mail.send(msg)

                flash(f'Hemos enviado un código a {email_input}.', 'info')
                return redirect(url_for('verify_token'))
            except Exception as e:
                flash(f'Error enviando correo: {e}', 'danger')
                print(e)
        else:
            flash('Correo no registrado.', 'danger')

    return render_template('recuperar_1_email.html')


# PASO 2: Verificar Código
@app.route('/verificar-codigo', methods=['GET', 'POST'])
def verify_token():
    if 'reset_token' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        codigo_ingresado = request.form.get('token').upper().strip()

        if codigo_ingresado == session['reset_token']:
            flash('Código correcto.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Código incorrecto.', 'danger')

    return render_template('recuperar_2_codigo.html')


# PASO 3: Nueva Contraseña (CON SEGURIDAD EXTRA)
@app.route('/restablecer-clave', methods=['GET', 'POST'])
def reset_password():
    if 'reset_token' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        pass1 = request.form.get('password')
        pass2 = request.form.get('confirm_password')

        if pass1 != pass2:
            flash('Las contraseñas no coinciden.', 'danger')
        else:
            user = User.query.filter_by(email=session['reset_email']).first()
            if user:
                # Seguridad: La nueva contraseña no puede ser igual a la anterior
                if check_password_hash(user.password_hash, pass1):
                    flash('⚠️ Por seguridad, la nueva contraseña no puede ser igual a la anterior.', 'danger')
                    return render_template('recuperar_3_clave.html')

                # Si es diferente, guardamos
                user.password_hash = generate_password_hash(pass1)
                db.session.commit()

                session.pop('reset_token', None)
                session.pop('reset_email', None)

                flash('✅ Contraseña actualizada correctamente.', 'success')
                return redirect(url_for('home'))
            else:
                flash('Error de usuario.', 'danger')

    return render_template('recuperar_3_clave.html')


@app.route('/menu-principal')
def menu_principal():
    return render_template('menu_principal.html', nombre_usuario=session.get('user_name', 'Usuario'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/reparar-base-de-datos')
def reparar_db():
    db.drop_all();
    db.create_all()
    return "DB Reset"


if __name__ == '__main__':
    app.run(debug=True)