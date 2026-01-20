from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import random
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)

# ==========================================
# 1. CONFIGURACIÓN DEL SISTEMA
# ==========================================
db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta_y_segura'

# ==========================================
# 2. CONFIGURACIÓN DEL CORREO (GMAIL)
# ==========================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisalbertotoalombotoapaxi@gmail.com'
app.config['MAIL_PASSWORD'] = 'dwjl pwrc wguz gtvi'

mail = Mail(app)
db = SQLAlchemy(app)


# ==========================================
# 3. MODELOS DE BASE DE DATOS
# ==========================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_granja = db.Column(db.String(150), nullable=True)
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


class Ave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lote_codigo = db.Column(db.String(50), unique=True)  # ID Único

    # Datos básicos
    especie = db.Column(db.String(50), nullable=False)
    raza_color = db.Column(db.String(100))
    etapa = db.Column(db.String(50))  # Aqui se guarda 'nacidos', 'desarrollo', etc.

    sexo = db.Column(db.String(20))
    cant_machos = db.Column(db.Integer, default=0)
    cant_hembras = db.Column(db.Integer, default=0)

    fecha_nacimiento = db.Column(db.Date)
    cantidad = db.Column(db.Integer, default=0)

    # DATOS FINANCIEROS
    forma_pago = db.Column(db.String(50))
    costo_unitario = db.Column(db.Float, default=0.0)
    monto_pago = db.Column(db.Float, default=0.0)
    comprobante = db.Column(db.String(100))

    estado = db.Column(db.String(20), default='Activo')
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cedula_ruc = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    observaciones = db.Column(db.Text)


class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    tipo_insumo = db.Column(db.String(50))
    observaciones = db.Column(db.Text)


with app.app_context():
    db.create_all()


# ==========================================
# 4. RUTAS DE ACCESO (LOGIN / REGISTRO)
# ==========================================

@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('menu_principal'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['user_name'] = user.nombres
        session['role'] = user.role
        return redirect(url_for('menu_principal'))

    flash('Usuario o contraseña incorrectos', 'danger')
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/seleccionar-tipo')
def seleccionar_tipo():
    return render_template('account_type.html')


@app.route('/create_account/<tipo>', methods=['GET', 'POST'])
def create_account(tipo):
    if tipo == 'admin':
        if User.query.filter_by(role='Propietario').first():
            flash('⚠️ ACCESO RESTRINGIDO: Ya existe un Administrador.', 'danger')
            return redirect(url_for('home'))
    elif tipo == 'colaborador':
        if User.query.filter_by(role='Colaborador').count() >= 20:
            flash('⚠️ LÍMITE ALCANZADO: Máximo 20 colaboradores.', 'danger')
            return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            password = request.form.get('password')
            confirm = request.form.get('confirm_password')

            if password != confirm:
                flash('Las contraseñas no coinciden', 'danger')
                return render_template('register_admin.html', tipo=tipo)

            hashed_password = generate_password_hash(password)

            rol_usuario = 'Propietario' if tipo == 'admin' else 'Colaborador'
            nombre_granja_valor = request.form.get('nombre_granja') if tipo == 'admin' else None

            new_user = User(
                nombre_granja=nombre_granja_valor,
                cedula=request.form.get('cedula'),
                nombres=request.form.get('nombres'),
                apellidos=request.form.get('apellidos'),
                pais=request.form.get('pais'),
                provincia=request.form.get('provincia'),
                ciudad=request.form.get('ciudad'),
                direccion=request.form.get('direccion'),
                username=request.form.get('username'),
                password_hash=hashed_password,
                email=request.form.get('email'),
                recuperacion_email=request.form.get('email'),
                role=rol_usuario
            )

            db.session.add(new_user)
            db.session.commit()
            flash('✅ Cuenta creada exitosamente. Inicie sesión.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            flash(f'Error al crear cuenta: {str(e)}', 'danger')
            return render_template('register_admin.html', tipo=tipo)

    return render_template('register_admin.html', tipo=tipo)


# ==========================================
# 5. RECUPERACIÓN DE CONTRASEÑA
# ==========================================

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = str(random.randint(100000, 999999))
            session['reset_token'] = token
            session['reset_email'] = email
            msg = Message('Código de Recuperación - Pico y Pluma', sender='noreply@demo.com', recipients=[email])
            msg.body = f'Su código de recuperación es: {token}'
            try:
                mail.send(msg)
                flash('Se ha enviado un código a su correo.', 'info')
                return redirect(url_for('verify_code'))
            except Exception as e:
                flash(f'Error enviando correo: {e}', 'danger')
        else:
            flash('El correo no está registrado.', 'danger')
    return render_template('recuperar_1_email.html')


@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    if request.method == 'POST':
        if request.form.get('codigo') == session.get('reset_token'):
            return redirect(url_for('new_password'))
        flash('Código incorrecto.', 'danger')
    return render_template('recuperar_2_codigo.html')


@app.route('/new_password', methods=['GET', 'POST'])
def new_password():
    if request.method == 'POST':
        pass1 = request.form.get('password')
        pass2 = request.form.get('confirm_password')
        if pass1 == pass2:
            user = User.query.filter_by(email=session.get('reset_email')).first()
            if user:
                user.password_hash = generate_password_hash(pass1)
                db.session.commit()
                session.pop('reset_token', None)
                flash('Contraseña actualizada.', 'success')
                return redirect(url_for('home'))
        flash('Las contraseñas no coinciden.', 'danger')
    return render_template('recuperar_3_clave.html')


# ==========================================
# 6. DASHBOARD E INVENTARIO
# ==========================================

@app.route('/menu-principal')
def menu_principal():
    if 'user_id' not in session: return redirect(url_for('home'))
    return render_template('menu_principal.html', nombre=session.get('user_name', 'Usuario'),
                           rol=session.get('role', 'Colaborador'))


@app.route('/inventario')
def inventario():
    if 'user_id' not in session: return redirect(url_for('home'))
    aves = Ave.query.filter(Ave.estado != 'Eliminado').order_by(Ave.id.desc()).all()
    return render_template('inventario.html', aves=aves)


@app.route('/eliminar_ave/<int:id>')
def eliminar_ave(id):
    if session.get('role') == 'Propietario':
        ave = Ave.query.get_or_404(id)
        ave.estado = 'Eliminado'
        db.session.commit()
        flash('Lote eliminado.', 'warning')

        # Redirigir inteligentemente: Si estaba en una etapa, volver a esa etapa
        if ave.etapa:
            return redirect(url_for('ver_etapa', etapa=ave.etapa))

    else:
        flash('No tienes permiso para eliminar.', 'danger')

    return redirect(url_for('inventario'))


# ==========================================
# 7. MÓDULO DE COMPRAS Y REGISTRO (LOGICA NUEVA)
# ==========================================

@app.route('/registrar_movimiento/<tipo>')
def registrar_movimiento(tipo):
    if tipo == 'Venta':  # Cambiado para coincidir con tu HTML menu_principal
        # Si tienes html de ventas, retornarlo aquí. Si no, placeholder:
        return f"<h1>Sección de Ventas</h1><p>En construcción</p><a href='/menu-principal'>Volver</a>"
    if tipo == 'Compra':  # Por si acaso se llama Compra en otro lado
        return render_template('compras_seleccion.html')

    # Fallback para el link de "Compras" en menu_principal si el texto es distinto
    return render_template('compras_seleccion.html')


@app.route('/formulario_compra/<categoria>')
def formulario_compra(categoria):
    if categoria == 'aves':
        return render_template('compras_aves_etapa.html')
    # Aquí puedes añadir 'insumos'
    if categoria == 'insumos':
        return redirect(url_for('proveedores'))

    return redirect(url_for('menu_principal'))


# --- NUEVA RUTA: PARA VER LA LISTA ANTES DEL FORMULARIO ---
@app.route('/ver-etapa/<etapa>')
def ver_etapa(etapa):
    if 'user_id' not in session: return redirect(url_for('home'))

    # Filtra por etapa (ej: nacidos) y que no estén eliminados
    aves = Ave.query.filter_by(etapa=etapa, estado='Activo').order_by(Ave.fecha_registro.desc()).all()

    return render_template('lista_etapa.html', aves=aves, etapa=etapa)


@app.route('/formulario_final_ave/<etapa>', methods=['GET', 'POST'])
def formulario_final_ave(etapa):
    if request.method == 'POST':
        # 1. Recoger datos
        codigo_id = request.form.get('lote_codigo')

        # Validar ID
        existe = Ave.query.filter_by(lote_codigo=codigo_id).first()
        if existe:
            flash(f'ERROR: El ID "{codigo_id}" ya existe. Use otro.', 'danger')
            return redirect(url_for('formulario_final_ave', etapa=etapa))

        try:
            # Tipo y Descripción
            tipo_ave = request.form.get('tipo_ave')
            if tipo_ave == 'Otro': tipo_ave = request.form.get('nuevo_tipo_ave')

            descripcion = request.form.get('descripcion')
            if descripcion == 'Otro': descripcion = request.form.get('nueva_descripcion')

            # Pagos y Costos
            f_pago = request.form.get('forma_pago')
            costo_u = float(request.form.get('costo_unitario') or 0)
            monto_total = float(request.form.get('valor_total') or 0)
            comprobante = request.form.get('numero_comprobante') if f_pago == 'Deposito' else None

            nueva_ave = Ave(
                lote_codigo=codigo_id,
                especie=tipo_ave,
                raza_color=descripcion,
                etapa=etapa,
                fecha_nacimiento=datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date(),
                cantidad=int(request.form.get('cantidad') or 1),
                forma_pago=f_pago,
                costo_unitario=costo_u,
                monto_pago=monto_total,
                comprobante=comprobante,
                estado='Activo'
            )

            db.session.add(nueva_ave)
            db.session.commit()
            flash(f'✅ {etapa.capitalize()} registrado exitosamente.', 'success')

            # REDIRECCIONAR A LA LISTA DE ESA ETAPA (CAMBIO SOLICITADO)
            return redirect(url_for('ver_etapa', etapa=etapa))

        except Exception as e:
            flash(f'Error al guardar: {e}', 'danger')
            return redirect(url_for('formulario_final_ave', etapa=etapa))

    return render_template('formulario_nacidos.html', etapa=etapa)


# ==========================================
# 8. RUTAS EXTRA Y PLACEHOLDERS (Para evitar errores 404/BuildError)
# ==========================================

@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if request.method == 'POST':
        # Logica rapida para guardar clientes si se requiere
        pass
    clientes_list = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes_list)


@app.route('/proveedores', methods=['GET', 'POST'])
def proveedores():
    if request.method == 'POST':
        # Logica rapida para guardar proveedores
        pass
    proveedores_list = Proveedor.query.all()
    return render_template('proveedores.html', proveedores=proveedores_list)


@app.route('/muerte_aves')
def muerte_aves():
    return "<h1>Registro de Bajas / Muertes</h1><p>Módulo en construcción.</p><a href='/menu-principal'>Volver al Menú</a>"


@app.route('/datos_financieros')
def datos_financieros():
    return "<h1>Datos Financieros</h1><p>Módulo en construcción.</p><a href='/menu-principal'>Volver al Menú</a>"


@app.route('/alertas')
def alertas():
    return "<h1>Sistema de Alertas</h1><p>Módulo en construcción.</p><a href='/menu-principal'>Volver al Menú</a>"


@app.route('/graficas')
def graficas():
    return "<h1>Gráficas Estadísticas</h1><p>Módulo en construcción.</p><a href='/menu-principal'>Volver al Menú</a>"


@app.route('/colaboradores')
def colaboradores():
    return "<h1>Gestión de Colaboradores</h1><p>Módulo en construcción.</p><a href='/menu-principal'>Volver al Menú</a>"


# ==========================================
# 9. REPARACIÓN DB
# ==========================================
@app.route('/reparar-base-de-datos')
def reparar_db():
    with app.app_context():
        db.create_all()
    return "Base de datos verificada y actualizada."


if __name__ == '__main__':
    app.run(debug=True)