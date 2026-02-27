from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from sqlalchemy import text, func, extract
import os
import random
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

app = Flask(__name__)



# ==========================================
# CONFIGURACIÓN
# ==========================================
db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_super_secreta_y_segura'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'luisalbertotoalombotoapaxi@gmail.com'
app.config['MAIL_PASSWORD'] = 'dwjl pwrc wguz gtvi'

mail = Mail(app)
db = SQLAlchemy(app)


def obtener_todas_las_alertas():
    aves = Ave.query.all()
    alertas_finales = []
    hoy = date.today()

    for ave in aves:
        try:
            # CORRECCIÓN AQUÍ: Verificamos si ya es una fecha o si es un string
            if isinstance(ave.fecha_nacimiento, str):
                fecha_nac = datetime.strptime(ave.fecha_nacimiento, '%Y-%m-%d').date()
            else:
                fecha_nac = ave.fecha_nacimiento  # Si ya es objeto date, lo usamos directo

            if not fecha_nac:
                continue

            edad_dias = (hoy - fecha_nac).days
            alerta = None

            # Lógica de alertas
            if ave.etapa == 'nacidos' and edad_dias >= 30:
                alerta = {
                    'lote': ave.lote_codigo,
                    'mensaje': f'El lote tiene {edad_dias} días. Debe pasar a Desarrollo.',
                    'color_alerta': 'warning',
                    'icono': 'fa-exclamation-triangle'
                }
            elif ave.etapa == 'desarrollo' and edad_dias >= 150:
                alerta = {
                    'lote': ave.lote_codigo,
                    'mensaje': f'El lote tiene {edad_dias} días. Debe pasar a Reproducción.',
                    'color_alerta': 'danger',
                    'icono': 'fa-exclamation-circle'
                }

            if alerta:
                alertas_finales.append(alerta)
        except Exception as e:
            print(f"Error procesando lote {ave.lote_codigo}: {e}")
            continue

    return alertas_finales

# ==========================================
# FILTROS
# ==========================================
@app.template_filter('calcular_edad')
def calcular_edad_filtro(fecha_str):
    if not fecha_str: return "---"
    try:
        if isinstance(fecha_str, str):
            fecha_nac = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        else:
            fecha_nac = fecha_str
        hoy = date.today()
        dias = (hoy - fecha_nac).days + 1
        if dias < 0: return "Error"
        if dias == 0: return "Nacido hoy"
        if dias < 30:
            return f"{dias} días"
        else:
            meses = dias // 30
            rest = dias % 30
            return f"{meses} meses ({rest} d)"
    except:
        return "---"


# ==========================================
# MODELOS DE BASE DE DATOS
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Propietario')
    email = db.Column(db.String(120), unique=True)
    nombre_granja = db.Column(db.String(150))
    apellidos = db.Column(db.String(100))
    pais = db.Column(db.String(50))
    provincia = db.Column(db.String(50))
    ciudad = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    recuperacion_email = db.Column(db.String(120))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)


class Ave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lote_codigo = db.Column(db.String(50), unique=True)
    tipo_ave = db.Column(db.String(50))
    descripcion = db.Column(db.String(100))
    etapa = db.Column(db.String(50))
    origen = db.Column(db.String(20), default='Compra')
    fecha_nacimiento = db.Column(db.Date)
    cantidad = db.Column(db.Integer, default=0)
    cant_machos = db.Column(db.Integer, default=0)
    cant_hembras = db.Column(db.Integer, default=0)
    forma_pago = db.Column(db.String(50))
    precio_macho = db.Column(db.Float, default=0.0)
    precio_hembra = db.Column(db.Float, default=0.0)
    costo_unitario = db.Column(db.Float, default=0.0)
    monto_pago = db.Column(db.Float, default=0.0)
    numero_comprobante = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='Activo')
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    especie = db.Column(db.String(50))
    raza_color = db.Column(db.String(100))


class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, default=date.today)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    producto = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    cantidad = db.Column(db.Float, default=0.0)
    valor_unitario = db.Column(db.Float, default=0.0)
    valor_total = db.Column(db.Float, default=0.0)
    forma_pago = db.Column(db.String(50))
    numero_comprobante = db.Column(db.String(100))  # NUEVO CAMPO AGREGADO


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cedula_ruc = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    observaciones = db.Column(db.Text)


class Proveedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    contacto = db.Column(db.String(100))
    tipo_insumo = db.Column(db.String(50))
    observaciones = db.Column(db.Text)


class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_nombre = db.Column(db.String(150))
    cliente_cedula = db.Column(db.String(20))
    cliente_celular = db.Column(db.String(20))
    destino = db.Column(db.String(100))
    valor_envio = db.Column(db.Float, default=0.0)
    costo_envio_real = db.Column(db.Float, default=0.0)
    categoria_venta = db.Column(db.String(50))
    lote_origen = db.Column(db.String(50))
    tipo_ave = db.Column(db.String(50))
    descripcion = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.Date)
    cantidad_total = db.Column(db.Integer, default=0)
    cant_machos = db.Column(db.Integer, default=0)
    cant_hembras = db.Column(db.Integer, default=0)
    precio_unitario = db.Column(db.Float, default=0.0)
    precio_macho = db.Column(db.Float, default=0.0)
    precio_hembra = db.Column(db.Float, default=0.0)
    subtotal_aves = db.Column(db.Float, default=0.0)
    total_pagar = db.Column(db.Float, default=0.0)
    forma_pago = db.Column(db.String(50))
    numero_comprobante = db.Column(db.String(100))
    observaciones = db.Column(db.Text)

class Baja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_baja = db.Column(db.DateTime, default=datetime.utcnow)
    lote_origen = db.Column(db.String(50))
    tipo_ave = db.Column(db.String(50))
    etapa_ave = db.Column(db.String(50))
    causa = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    cantidad_total = db.Column(db.Integer, default=0)
    cant_machos = db.Column(db.Integer, default=0)
    cant_hembras = db.Column(db.Integer, default=0)
    perdida_economica = db.Column(db.Float, default=0.0)


with app.app_context():
    db.create_all()


# ==========================================
# FUNCIÓN AUXILIAR PARA CÓDIGOS INSUMOS
# ==========================================
def obtener_siguiente_codigo_insumo(prefijo):
    ultimo = Insumo.query.filter(Insumo.codigo.like(f"{prefijo}%")) \
        .order_by(Insumo.codigo.desc()).first()
    if not ultimo:
        return f"{prefijo}0000000001"
    try:
        numero_str = ultimo.codigo[2:]
        numero = int(numero_str) + 1
        return f"{prefijo}{str(numero).zfill(10)}"
    except:
        return f"{prefijo}0000000001"


# ==========================================
# RUTAS DE AUTENTICACIÓN
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
        primer_nombre = user.nombres.split()[0] if user.nombres else ""
        primer_apellido = user.apellidos.split()[0] if user.apellidos else ""

        session['user_id'] = user.id
        session['user_nombre'] = f"{primer_nombre} {primer_apellido}".strip()
        session['role'] = user.role
        return redirect(url_for('menu_principal'))
    flash('Usuario o contraseña incorrectos', 'danger')
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter((User.email == email) | (User.recuperacion_email == email)).first()
        if user:
            token = generate_password_hash(str(random.random()), method='pbkdf2:sha256')[-20:]
            msg = Message('Recuperación de Contraseña', sender='luisalbertotoalombotoapaxi@gmail.com',
                          recipients=[email])
            msg.body = f'Tu enlace de recuperación (demo): {url_for("home", _external=True)}'
            mail.send(msg)
            flash('Se ha enviado un correo de recuperación', 'info')
        else:
            flash('Correo no encontrado', 'danger')
    try:
        return render_template('recuperar_1_email.html')
    except:
        return render_template('recuperar_contrasena.html')


@app.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    return render_template('recuperar_2_codigo.html')


@app.route('/new_password', methods=['GET', 'POST'])
def new_password():
    return redirect(url_for('home'))


@app.route('/seleccionar-tipo')
def seleccionar_tipo():
    # CAMBIO CLAVE: Contamos cuántos propietarios hay en total
    conteo_propietarios = User.query.filter_by(role='Propietario').count()

    # hay_propietario será True SOLO si ya existen 2 o más
    # Si hay 1, esto será False y dejará ver el botón de registro
    hay_propietario = True if conteo_propietarios >= 2 else False

    # Lógica para los 20 colaboradores
    num_colabs = User.query.filter_by(role='Colaborador').count()
    lleno_colabs = True if num_colabs >= 20 else False

    return render_template('account_type.html', hay_propietario=hay_propietario, lleno_colabs=lleno_colabs)

@app.route('/create_account/<tipo>', methods=['GET', 'POST'])
def create_account(tipo):
    # --- VALIDACIÓN DE LÍMITES REAL ---
    # Contamos cuántos hay. .count() nos devolverá 0, 1 o 2.
    num_propietarios = User.query.filter_by(role='Propietario').count()

    # Solo bloqueamos si ya se llegó a 2. Si hay 1, el sistema DEJA PASAR.
    if tipo == 'admin' and num_propietarios >= 2:
        flash('Ya existen 2 Propietarios (límite máximo alcanzado).', 'danger')
        return redirect(url_for('seleccionar_tipo'))

    if request.method == 'POST':
        # Verificamos contraseñas
        if request.form['password'] != request.form.get('confirm_password', request.form['password']):
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register_admin.html', tipo=tipo)

        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        # Instanciamos el usuario con todos los campos
        nuevo_usuario = User(
            cedula=request.form['cedula'],
            nombres=request.form['nombres'],
            apellidos=request.form.get('apellidos'),
            username=request.form['username'],
            password_hash=hashed_pw,
            # Se asigna el rol según el botón que presionó el usuario
            role='Propietario' if tipo == 'admin' else 'Colaborador',
            email=request.form['email'],
            nombre_granja=request.form.get('nombre_granja') if tipo == 'admin' else None,
            pais=request.form.get('pais'),
            provincia=request.form.get('provincia'),
            ciudad=request.form.get('ciudad'),
            direccion=request.form.get('direccion'),
            # Fecha para evitar errores en la lista
            fecha_registro=datetime.utcnow()
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Cuenta creada con éxito. Inicia sesión.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Error: El usuario o cédula ya están registrados.', 'danger')
            return render_template('register_admin.html', tipo=tipo)

    return render_template('register_admin.html', tipo=tipo)


@app.route('/menu-principal')  # o la ruta que uses para el dashboard
def menu_principal():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    # Obtener el nombre y rol del usuario de la sesión
    nombre = session.get('user_nombre', 'Usuario')
    rol = session.get('user_rol', 'Admin')

    # AQUÍ ESTÁ LA CORRECCIÓN:
    lista_alertas = obtener_todas_las_alertas()

    return render_template('menu_principal.html',
                           nombre=nombre,
                           rol=rol,
                           alertas=lista_alertas)  # Pasamos la lista real

# ==========================================
# GESTIÓN DE AVES (INVENTARIO)
# ==========================================

@app.route('/registrar_ave/<etapa>', methods=['GET', 'POST'])
def registrar_ave(etapa):
    if 'user_id' not in session: return redirect(url_for('home'))
    origen = request.args.get('origen', 'Compra')
    return render_template('formulario_ave.html', etapa=etapa, origen=origen)


@app.route('/formulario_final_ave/<etapa>', methods=['GET', 'POST'])
def formulario_final_ave(etapa):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    edit_id = request.form.get('ave_id_hidden') or request.args.get('edit_id')
    ave_editar = Ave.query.get(edit_id) if edit_id else None

    origen_actual = 'Compra'
    if request.method == 'POST':
        origen_actual = request.form.get('origen', 'Compra')
    else:
        if ave_editar:
            origen_actual = ave_editar.origen
        else:
            origen_actual = request.args.get('origen', 'Compra')

    def obtener_siguiente_codigo(prefijo):
        ultimo = Ave.query.filter(Ave.lote_codigo.like(f"{prefijo}%")) \
            .order_by(Ave.lote_codigo.desc()).first()
        if not ultimo:
            return f"{prefijo}000000001"
        try:
            num = int(ultimo.lote_codigo[len(prefijo):]) + 1
            return f"{prefijo}{str(num).zfill(9)}"
        except:
            return f"{prefijo}000000001"

    if request.method == 'POST':
        try:
            f_nac = datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d').date()

            codigo = request.form.get('lote_codigo') or f"ERR-{random.randint(1000,9999)}"

            cant = int(request.form.get('cantidad', 0) or 0)
            c_machos = int(request.form.get('cant_machos', 0) or 0)
            c_hembras = int(request.form.get('cant_hembras', 0) or 0)

            costo_u = float(request.form.get('costo_unitario', 0) or 0)
            p_macho = float(request.form.get('precio_macho', 0) or 0)
            p_hembra = float(request.form.get('precio_hembra', 0) or 0)

            forma_pago = request.form.get('forma_pago')
            numero_comprobante = (
                request.form.get('numero_comprobante')
                if forma_pago in ['Transferencia', 'Deposito']
                else None
            )

            if etapa in ['desarrollo', 'engorde']:
                cant = c_machos + c_hembras
                monto_total = (c_machos * p_macho) + (c_hembras * p_hembra)
            else:
                monto_total = cant * costo_u

            if ave_editar:
                ave_editar.tipo_ave = request.form['tipo_ave']
                ave_editar.descripcion = request.form['descripcion']
                ave_editar.fecha_nacimiento = f_nac
                ave_editar.cantidad = cant
                ave_editar.cant_machos = c_machos
                ave_editar.cant_hembras = c_hembras
                ave_editar.costo_unitario = costo_u
                ave_editar.precio_macho = p_macho
                ave_editar.precio_hembra = p_hembra
                ave_editar.monto_pago = monto_total
                ave_editar.forma_pago = forma_pago
                ave_editar.numero_comprobante = numero_comprobante
                ave_editar.observaciones = request.form.get('observaciones', '')
                flash('Lote actualizado correctamente', 'success')

            else:
                nuevo_lote = Ave(
                    lote_codigo=codigo,
                    etapa=etapa,
                    origen=origen_actual,
                    tipo_ave=request.form['tipo_ave'],
                    descripcion=request.form['descripcion'],
                    fecha_nacimiento=f_nac,
                    cantidad=cant,
                    cant_machos=c_machos,
                    cant_hembras=c_hembras,
                    costo_unitario=costo_u,
                    precio_macho=p_macho,
                    precio_hembra=p_hembra,
                    monto_pago=monto_total,
                    forma_pago=forma_pago,
                    numero_comprobante=numero_comprobante,
                    observaciones=request.form.get('observaciones', '')
                )
                db.session.add(nuevo_lote)
                flash(f'Lote registrado exitosamente ({origen_actual})', 'success')

            db.session.commit()
            return redirect(url_for('ver_etapa', etapa=etapa, origen=origen_actual))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')

    nuevo_codigo = ""
    if not ave_editar:
        if origen_actual == 'Produccion':
            prefijo_final = "PIN" if etapa == 'nacidos' else "PID" if etapa == 'desarrollo' else "PIGR"
        else:
            prefijo_final = "CN" if etapa == 'nacidos' else "CD" if etapa == 'desarrollo' else "CGR"
        nuevo_codigo = obtener_siguiente_codigo(prefijo_final)

    common_args = {
        'etapa': etapa,
        'ave': ave_editar,
        'nuevo_codigo': nuevo_codigo,
        'origen': origen_actual
    }

    if etapa == 'desarrollo':
        return render_template('formulario_desarrollo.html', **common_args)
    elif etapa == 'engorde':
        return render_template('formulario_reproductores.html', **common_args)
    else:
        return render_template('formulario_nacidos.html', **common_args)


@app.route('/ver-etapa/<etapa>')
def ver_etapa(etapa):
    if 'user_id' not in session: return redirect(url_for('home'))
    origen = request.args.get('origen', 'Compra')
    aves = Ave.query.filter_by(etapa=etapa, estado='Activo', origen=origen).order_by(Ave.fecha_registro.desc()).all()
    return render_template('lista_etapa.html', aves=aves, etapa=etapa, categoria_principal='aves', origen=origen)


@app.route('/eliminar_ave/<int:id>')
def eliminar_ave(id):
    if 'user_id' not in session: return redirect(url_for('home'))
    ave = Ave.query.get_or_404(id)
    ave.estado = 'Eliminado'
    db.session.commit()
    flash('Lote eliminado correctamente', 'success')
    return redirect(request.referrer)


# ==========================================
# GESTIÓN DE INVENTARIO GENERAL
# ==========================================
@app.route('/inventario')
def inventario():
    if 'user_id' not in session: return redirect(url_for('home'))
    aves = Ave.query.filter(Ave.estado != 'Eliminado').order_by(Ave.fecha_registro.desc()).all()
    insumos = Insumo.query.order_by(Insumo.fecha.desc()).all()
    return render_template('inventario.html', aves=aves, insumos=insumos)


# ==========================================
# GESTIÓN DE INSUMOS (COMPRAS Y PRODUCCIÓN)
# ==========================================
@app.route('/insumos/datos-productos')
def lista_insumos():
    if 'user_id' not in session: return redirect(url_for('home'))

    insumos = Insumo.query.filter(Insumo.codigo.like('CI%')).order_by(Insumo.fecha.desc()).all()
    origen = request.args.get('origen', 'Compra')
    return render_template('lista_etapa.html', insumos=insumos, categoria_principal='insumos', origen=origen)


@app.route('/insumos/registrar', methods=['GET', 'POST'])
def registrar_insumo():
    if 'user_id' not in session: return redirect(url_for('home'))
    edit_id = request.args.get('edit_id')
    insumo_editar = Insumo.query.get(edit_id) if edit_id else None

    nuevo_codigo = ""
    if not insumo_editar:
        nuevo_codigo = obtener_siguiente_codigo_insumo("CI")

    if request.method == 'POST':
        try:
            comprobante = request.form.get('numero_comprobante', '')  # CAPTURAMOS COMPROBANTE

            if insumo_editar:
                insumo_editar.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
                insumo_editar.producto = request.form['producto']
                insumo_editar.descripcion = request.form['descripcion']
                insumo_editar.cantidad = float(request.form['cantidad'])
                insumo_editar.valor_unitario = float(request.form['valor_unitario'])
                insumo_editar.valor_total = insumo_editar.cantidad * insumo_editar.valor_unitario
                insumo_editar.forma_pago = request.form['forma_pago']
                insumo_editar.numero_comprobante = comprobante if insumo_editar.forma_pago == 'Transferencia' else ''
            else:
                codigo_final = request.form.get('codigo') or obtener_siguiente_codigo_insumo("CI")
                forma_pago = request.form['forma_pago']

                nuevo_insumo = Insumo(
                    fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                    codigo=codigo_final,
                    producto=request.form['producto'],
                    descripcion=request.form['descripcion'],
                    cantidad=float(request.form['cantidad']),
                    valor_unitario=float(request.form['valor_unitario']),
                    valor_total=float(request.form['cantidad']) * float(request.form['valor_unitario']),
                    forma_pago=forma_pago,
                    numero_comprobante=comprobante if forma_pago == 'Transferencia' else ''
                )
                db.session.add(nuevo_insumo)
            db.session.commit()
            flash('Insumo guardado correctamente', 'success')
            return redirect(url_for('lista_insumos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')

    return render_template('formulario_insumos.html', insumo=insumo_editar, hoy=date.today(), nuevo_codigo=nuevo_codigo)


@app.route('/inventario/registrar-insumo', methods=['GET', 'POST'])
def registrar_insumo_inventario():
    if 'user_id' not in session: return redirect(url_for('home'))
    edit_id = request.args.get('edit_id')
    insumo_editar = Insumo.query.get(edit_id) if edit_id else None

    nuevo_codigo = ""
    if not insumo_editar:
        nuevo_codigo = obtener_siguiente_codigo_insumo("IG")

    if request.method == 'POST':
        try:
            comprobante = request.form.get('numero_comprobante', '')  # CAPTURAMOS COMPROBANTE

            if insumo_editar:
                insumo_editar.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
                insumo_editar.producto = request.form['producto']
                insumo_editar.descripcion = request.form['descripcion']
                insumo_editar.cantidad = float(request.form['cantidad'])
                insumo_editar.valor_unitario = float(request.form['valor_unitario'])
                insumo_editar.valor_total = insumo_editar.cantidad * insumo_editar.valor_unitario
                insumo_editar.forma_pago = request.form['forma_pago']
                insumo_editar.numero_comprobante = comprobante if insumo_editar.forma_pago == 'Transferencia' else ''
            else:
                codigo_final = request.form.get('codigo') or obtener_siguiente_codigo_insumo("IG")
                forma_pago = request.form['forma_pago']

                nuevo_insumo = Insumo(
                    fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                    codigo=codigo_final,
                    producto=request.form['producto'],
                    descripcion=request.form['descripcion'],
                    cantidad=float(request.form['cantidad']),
                    valor_unitario=float(request.form['valor_unitario']),
                    valor_total=float(request.form['cantidad']) * float(request.form['valor_unitario']),
                    forma_pago=forma_pago,
                    numero_comprobante=comprobante if forma_pago == 'Transferencia' else ''
                )
                db.session.add(nuevo_insumo)
            db.session.commit()
            flash('Stock de insumo actualizado desde Inventario', 'success')
            return redirect(url_for('inventario'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')

    return render_template('formulario_insumo_inventario.html', insumo=insumo_editar, hoy=date.today(),
                           nuevo_codigo=nuevo_codigo)


@app.route('/eliminar_insumo/<int:id>')
def eliminar_insumo(id):
    if 'user_id' not in session: return redirect(url_for('home'))
    insumo = Insumo.query.get_or_404(id)
    db.session.delete(insumo)
    db.session.commit()
    flash('Insumo eliminado', 'success')
    return redirect(request.referrer or url_for('inventario'))


# ==========================================
# GESTIÓN DE VENTAS
# ==========================================
@app.route('/ventas/lista')
def lista_ventas():
    if 'user_id' not in session: return redirect(url_for('home'))
    ventas = Venta.query.order_by(Venta.fecha_venta.desc()).all()
    neto_total = sum((v.subtotal_aves + (v.valor_envio - v.costo_envio_real)) for v in ventas)
    return render_template('lista_ventas.html', ventas=ventas, acumulador={'neto_total': neto_total})


@app.route('/ventas/registrar', methods=['GET', 'POST'])
@app.route('/ventas/editar/<int:id>', methods=['GET', 'POST'])
def registrar_venta(id=None):
    if 'user_id' not in session: return redirect(url_for('home'))

    venta_editar = None
    if id:
        venta_editar = Venta.query.get_or_404(id)

    aves_disponibles = Ave.query.filter(Ave.estado == 'Activo', Ave.cantidad > 0).all()

    inventario_data = []
    for ave in aves_disponibles:
        inventario_data.append({
            'lote': ave.lote_codigo,
            'etapa': ave.etapa,
            'tipo': ave.tipo_ave,
            'desc': ave.descripcion,
            'fecha': ave.fecha_nacimiento.strftime('%Y-%m-%d') if ave.fecha_nacimiento else '',
            'total': ave.cantidad,
            'machos': ave.cant_machos,
            'hembras': ave.cant_hembras,
            'precio_u': ave.costo_unitario,
            'precio_m': ave.precio_macho,
            'precio_h': ave.precio_hembra
        })

    if request.method == 'POST':
        try:
            fecha_str = request.form.get('fecha_venta')
            fecha_v = datetime.now()
            if fecha_str:
                try:
                    fecha_v = datetime.strptime(fecha_str, '%Y-%m-%d')
                except:
                    pass

            cli_nom = request.form.get('cliente_nombre')
            cli_ced = request.form.get('cliente_cedula')
            cli_cel = request.form.get('cliente_celular')
            destino = request.form.get('destino')
            envio_cobrado = float(request.form.get('valor_envio') or 0)
            envio_real = float(request.form.get('costo_encomienda_real') or 0)
            categoria = request.form.get('categoria_venta')
            pago = request.form.get('forma_pago')
            comprobante = request.form.get('numero_comprobante', '')

            tipo = ""
            desc = ""
            lote = ""
            f_nac_str = ""
            c_machos = 0
            c_hembras = 0
            c_total = 0
            p_unit = 0.0
            p_macho = 0.0
            p_hembra = 0.0

            if categoria == 'Nacidos':
                lote = request.form.get('lote_nac')
                tipo = request.form.get('tipo_ave_nac')
                desc = request.form.get('descripcion_nac')
                f_nac_str = request.form.get('fecha_nacimiento_nac')
                c_total = int(request.form.get('cantidad_nac') or 0)
                p_unit = float(request.form.get('precio_unitario') or 0)
            else:
                lote = request.form.get('lote_sex')
                tipo = request.form.get('tipo_ave_sex')
                desc = request.form.get('descripcion_sex')
                f_nac_str = request.form.get('fecha_nacimiento_sex')
                c_machos = int(request.form.get('cant_machos') or 0)
                c_hembras = int(request.form.get('cant_hembras') or 0)
                c_total = c_machos + c_hembras

                p_macho = float(request.form.get('precio_macho') or 0)
                p_hembra = float(request.form.get('precio_hembra') or 0)

                if c_total > 0:
                    sub_temp = (c_machos * p_macho) + (c_hembras * p_hembra)
                    p_unit = sub_temp / c_total

            fecha_n = None
            if f_nac_str:
                try:
                    fecha_n = datetime.strptime(f_nac_str, '%Y-%m-%d').date()
                except:
                    pass

            total_pagar_form = float(request.form.get('total_pagar') or 0)
            subtotal = total_pagar_form - envio_cobrado

            if venta_editar:
                venta_editar.fecha_venta = fecha_v
                venta_editar.cliente_nombre = cli_nom
                venta_editar.cliente_cedula = cli_ced
                venta_editar.cliente_celular = cli_cel
                venta_editar.destino = destino
                venta_editar.valor_envio = envio_cobrado
                venta_editar.costo_envio_real = envio_real
                venta_editar.categoria_venta = categoria
                venta_editar.lote_origen = lote
                venta_editar.tipo_ave = tipo
                venta_editar.descripcion = desc
                venta_editar.fecha_nacimiento = fecha_n
                venta_editar.cantidad_total = c_total
                venta_editar.cant_machos = c_machos
                venta_editar.cant_hembras = c_hembras
                venta_editar.precio_unitario = p_unit
                venta_editar.precio_macho = p_macho
                venta_editar.precio_hembra = p_hembra
                venta_editar.subtotal_aves = subtotal
                venta_editar.total_pagar = total_pagar_form
                venta_editar.forma_pago = pago
                venta_editar.numero_comprobante = comprobante if pago == 'Transferencia' else ''
                flash('Venta actualizada correctamente', 'success')
            else:
                nueva_venta = Venta(
                    fecha_venta=fecha_v,
                    cliente_nombre=cli_nom,
                    cliente_cedula=cli_ced,
                    cliente_celular=cli_cel,
                    destino=destino,
                    valor_envio=envio_cobrado,
                    costo_envio_real=envio_real,
                    categoria_venta=categoria,
                    lote_origen=lote,
                    tipo_ave=tipo,
                    descripcion=desc,
                    fecha_nacimiento=fecha_n,
                    cantidad_total=c_total,
                    cant_machos=c_machos,
                    cant_hembras=c_hembras,
                    precio_unitario=p_unit,
                    precio_macho=p_macho,
                    precio_hembra=p_hembra,
                    subtotal_aves=subtotal,
                    total_pagar=total_pagar_form,
                    forma_pago=pago
                )
                db.session.add(nueva_venta)

                if lote:
                    ave_en_stock = Ave.query.filter_by(lote_codigo=lote).first()

                    if ave_en_stock:
                        if ave_en_stock.cantidad >= c_total:
                            ave_en_stock.cantidad -= c_total
                        else:
                            ave_en_stock.cantidad = 0

                        if ave_en_stock.cant_machos >= c_machos:
                            ave_en_stock.cant_machos -= c_machos
                        else:
                            ave_en_stock.cant_machos = 0

                        if ave_en_stock.cant_hembras >= c_hembras:
                            ave_en_stock.cant_hembras -= c_hembras
                        else:
                            ave_en_stock.cant_hembras = 0

                flash('Venta registrada y stock descontado', 'success')

            db.session.commit()
            return redirect(url_for('lista_ventas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar venta: {e}', 'danger')

    return render_template('formulario_ventas.html', hoy=date.today(), venta=venta_editar,
                           inventario_json=inventario_data)


# ==========================================
# RUTAS AUXILIARES / CLIENTES / PROVEEDORES
# ==========================================
@app.route('/clientes')
def clientes():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    clientes_unicos = (
        db.session.query(
            Venta.cliente_nombre.label("nombre"),
            Venta.cliente_cedula.label("cedula_ruc"),
            func.max(Venta.cliente_celular).label("telefono"),
            func.max(Venta.destino).label("direccion")
        )
        .filter(Venta.cliente_cedula != None)
        .group_by(Venta.cliente_cedula, Venta.cliente_nombre)
        .order_by(Venta.cliente_nombre.asc())
        .all()
    )

    return render_template('clientes.html', clientes=clientes_unicos)

@app.route('/clientes/registrar', methods=['GET', 'POST'])
def registrar_cliente():
    if 'user_id' not in session: return redirect(url_for('home'))
    if request.method == 'POST':
        nuevo = Cliente(
            nombre=request.form['nombre'],
            cedula_ruc=request.form.get('cedula'),
            telefono=request.form.get('telefono'),
            direccion=request.form.get('direccion'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('clientes'))
    return render_template('formulario_cliente.html')


@app.route('/clientes/eliminar/<int:id>')
def eliminar_cliente(id):
    if 'user_id' not in session: return redirect(url_for('home'))
    c = Cliente.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for('clientes'))


@app.route('/proveedores')
def proveedores():
    if 'user_id' not in session: return redirect(url_for('home'))
    return render_template('proveedores.html', proveedores=Proveedor.query.all())


@app.route('/proveedores/registrar', methods=['GET', 'POST'])
def registrar_proveedor():
    if 'user_id' not in session: return redirect(url_for('home'))
    if request.method == 'POST':
        nuevo = Proveedor(
            nombre=request.form['nombre'],
            contacto=request.form.get('contacto'),
            tipo_insumo=request.form.get('tipo_insumo'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('proveedores'))
    return render_template('formulario_proveedor.html')


@app.route('/proveedores/eliminar/<int:id>')
def eliminar_proveedor(id):
    if 'user_id' not in session: return redirect(url_for('home'))
    p = Proveedor.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('proveedores'))


@app.route('/registrar_movimiento/<tipo>')
def registrar_movimiento(tipo):
    if tipo == 'Compra':
        return redirect(url_for('ver_etapa', etapa='nacidos', origen='Compra'))
    elif tipo == 'Venta':
        return redirect(url_for('lista_ventas'))
    return redirect(url_for('menu_principal'))


# ==========================================
# GESTIÓN DE BAJAS Y MORTALIDAD
# ==========================================
@app.route('/muerte_aves')
def muerte_aves():
    if 'user_id' not in session: return redirect(url_for('home'))
    bajas = Baja.query.order_by(Baja.fecha_baja.desc()).all()
    return render_template('lista_bajas.html', bajas=bajas)


@app.route('/registrar_baja', methods=['GET', 'POST'])
@app.route('/editar_baja/<int:id>', methods=['GET', 'POST'])
def registrar_baja(id=None):
    if 'user_id' not in session: return redirect(url_for('home'))

    baja_editar = None
    if id:
        baja_editar = Baja.query.get_or_404(id)

    aves_disponibles = Ave.query.filter(Ave.estado == 'Activo', Ave.cantidad > 0).all()

    # Si estamos editando, asegurarnos de incluir el lote original aunque ahora tenga cantidad 0
    if baja_editar and baja_editar.lote_origen:
        ave_original = Ave.query.filter_by(lote_codigo=baja_editar.lote_origen).first()
        if ave_original and ave_original not in aves_disponibles:
            aves_disponibles.append(ave_original)

    inventario_data = []
    for ave in aves_disponibles:
        inventario_data.append({
            'lote': ave.lote_codigo,
            'etapa': ave.etapa,
            'tipo': ave.tipo_ave,
            'total': ave.cantidad,
            'machos': ave.cant_machos,
            'hembras': ave.cant_hembras,
            'costo_u': ave.costo_unitario,
            'precio_m': ave.precio_macho,
            'precio_h': ave.precio_hembra
        })

    if request.method == 'POST':
        try:
            fecha_str = request.form.get('fecha_baja')
            fecha_b = datetime.now()
            if fecha_str:
                try:
                    fecha_b = datetime.strptime(fecha_str, '%Y-%m-%d')
                except:
                    pass

            lote = request.form.get('lote_origen')
            tipo = request.form.get('tipo_ave')
            etapa = request.form.get('etapa_ave')
            causa = request.form.get('causa')
            obs = request.form.get('observaciones', '')

            c_total = int(request.form.get('cantidad_total') or 0)
            c_machos = int(request.form.get('cant_machos') or 0)
            c_hembras = int(request.form.get('cant_hembras') or 0)
            perdida = float(request.form.get('perdida_economica') or 0.0)

            if baja_editar:
                # 1. DEVOLVER EL STOCK ANTERIOR (Reversar)
                if baja_editar.lote_origen:
                    ave_vieja = Ave.query.filter_by(lote_codigo=baja_editar.lote_origen).first()
                    if ave_vieja:
                        ave_vieja.cantidad += baja_editar.cantidad_total
                        ave_vieja.cant_machos += baja_editar.cant_machos
                        ave_vieja.cant_hembras += baja_editar.cant_hembras

                # 2. ACTUALIZAR LOS DATOS DE LA BAJA
                baja_editar.fecha_baja = fecha_b
                baja_editar.lote_origen = lote
                baja_editar.tipo_ave = tipo
                baja_editar.etapa_ave = etapa
                baja_editar.causa = causa
                baja_editar.observaciones = obs
                baja_editar.cantidad_total = c_total
                baja_editar.cant_machos = c_machos
                baja_editar.cant_hembras = c_hembras
                baja_editar.perdida_economica = perdida

                # 3. VOLVER A DESCONTAR CON LA NUEVA CANTIDAD
                if lote:
                    ave_nueva = Ave.query.filter_by(lote_codigo=lote).first()
                    if ave_nueva:
                        ave_nueva.cantidad = max(0, ave_nueva.cantidad - c_total)
                        ave_nueva.cant_machos = max(0, ave_nueva.cant_machos - c_machos)
                        ave_nueva.cant_hembras = max(0, ave_nueva.cant_hembras - c_hembras)

                flash('Registro actualizado. Las aves han sido devueltas/descontadas del inventario correctamente.',
                      'success')

            else:
                nueva_baja = Baja(
                    fecha_baja=fecha_b, lote_origen=lote, tipo_ave=tipo,
                    etapa_ave=etapa, causa=causa, observaciones=obs,
                    cantidad_total=c_total, cant_machos=c_machos,
                    cant_hembras=c_hembras, perdida_economica=perdida
                )
                db.session.add(nueva_baja)

                # Descuento del stock del ave seleccionada
                if lote:
                    ave_en_stock = Ave.query.filter_by(lote_codigo=lote).first()
                    if ave_en_stock:
                        ave_en_stock.cantidad = max(0, ave_en_stock.cantidad - c_total)
                        ave_en_stock.cant_machos = max(0, ave_en_stock.cant_machos - c_machos)
                        ave_en_stock.cant_hembras = max(0, ave_en_stock.cant_hembras - c_hembras)

                flash('Baja registrada y stock descontado', 'success')

            db.session.commit()
            return redirect(url_for('muerte_aves'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar baja: {e}', 'danger')

    return render_template('formulario_baja.html', hoy=date.today(), inventario_json=inventario_data, baja=baja_editar)

@app.route('/eliminar_baja/<int:id>')
def eliminar_baja(id):
    if 'user_id' not in session: return redirect(url_for('home'))
    try:
        baja = Baja.query.get_or_404(id)
        # Reversar la baja (Devolver el stock al inventario)
        if baja.lote_origen:
            ave_en_stock = Ave.query.filter_by(lote_codigo=baja.lote_origen).first()
            if ave_en_stock:
                ave_en_stock.cantidad += baja.cantidad_total
                ave_en_stock.cant_machos += baja.cant_machos
                ave_en_stock.cant_hembras += baja.cant_hembras

        db.session.delete(baja)
        db.session.commit()
        flash('Registro eliminado y aves devueltas al inventario', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al reversar: {e}', 'danger')

    return redirect(url_for('muerte_aves'))


# ==========================================
# RUTAS DE MANTENIMIENTO / OTROS
# ==========================================

@app.route('/datos_financieros')
def datos_financieros():
    if 'user_id' not in session: return redirect(url_for('home'))

    # 1. CAPTURAR FECHAS DEL FILTRO
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')

    ahora = datetime.now()

    # Si no hay filtro, mostrar por defecto el mes actual
    if not fecha_inicio_str or not fecha_fin_str:
        fecha_inicio = datetime(ahora.year, ahora.month, 1).date()
        fecha_fin = ahora.date()
    else:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

    # Para que el filtro incluya todas las horas del día final (23:59:59)
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())

    # ==========================================
    # 2. TOTALES HISTÓRICOS (GLOBAL Acumulado)
    # ==========================================
    ventas = Venta.query.all()
    ingresos_totales = sum((v.subtotal_aves + (v.valor_envio - v.costo_envio_real)) for v in ventas)
    compra_aves_total = db.session.query(func.sum(Ave.monto_pago)).filter(
        Ave.origen == 'Compra',
        Ave.estado == 'Activo'
    ).scalar() or 0
    compra_insumos_total = db.session.query(func.sum(Insumo.valor_total)).scalar() or 0
    muertes_total = db.session.query(func.sum(Baja.perdida_economica)).scalar() or 0

    gastos_totales = compra_aves_total + compra_insumos_total
    balance_total = ingresos_totales - gastos_totales - muertes_total

    # ==========================================
    # 3. TOTALES DEL PERIODO SELECCIONADO
    # ==========================================
    ventas_periodo = Venta.query.filter(
        Venta.fecha_venta >= fecha_inicio_dt,
        Venta.fecha_venta <= fecha_fin_dt
    ).all()
    ingresos_periodo = sum((v.subtotal_aves + (v.valor_envio - v.costo_envio_real)) for v in ventas_periodo)

    compra_aves_periodo = db.session.query(func.sum(Ave.monto_pago)).filter(
        Ave.origen == 'Compra',
        Ave.estado == 'Activo',
        Ave.fecha_registro >= fecha_inicio_dt,
        Ave.fecha_registro <= fecha_fin_dt
    ).scalar() or 0

    # Insumo usa Date puro, no DateTime
    compra_insumos_periodo = db.session.query(func.sum(Insumo.valor_total)).filter(
        Insumo.fecha >= fecha_inicio,
        Insumo.fecha <= fecha_fin
    ).scalar() or 0

    muertes_periodo = db.session.query(func.sum(Baja.perdida_economica)).filter(
        Baja.fecha_baja >= fecha_inicio_dt,
        Baja.fecha_baja <= fecha_fin_dt
    ).scalar() or 0

    gastos_periodo = compra_aves_periodo + compra_insumos_periodo
    balance_periodo = ingresos_periodo - gastos_periodo - muertes_periodo

    return render_template('datos_financieros.html',
                           ingresos=ingresos_totales,
                           compra_aves=compra_aves_total,
                           compra_insumos=compra_insumos_total,
                           muertes=muertes_total,
                           balance=balance_total,
                           ingresos_periodo=ingresos_periodo,
                           compra_aves_periodo=compra_aves_periodo,
                           compra_insumos_periodo=compra_insumos_periodo,
                           muertes_periodo=muertes_periodo,
                           balance_periodo=balance_periodo,
                           fecha_inicio=fecha_inicio.strftime('%Y-%m-%d'),
                           fecha_fin=fecha_fin.strftime('%Y-%m-%d'))


@app.route('/alertas')
def alertas():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # o 'home' según tu ruta

    # IMPORTANTE: Asegúrate de que tu modelo se llama 'Ave'.
    # Si tienes dos tablas distintas (ej. CompraAves y ProduccionInterna), avísame.
    todas_las_aves = Ave.query.all()
    hoy = date.today()

    lista_alertas = []

    for ave in todas_las_aves:
        # Si el ave no tiene fecha de nacimiento registrada, la saltamos
        if not ave.fecha_nacimiento:
            continue

        # 1. FORZAR LA CONVERSIÓN DE LA FECHA (La clave para que funcione)
        try:
            if isinstance(ave.fecha_nacimiento, str):
                fecha_nac = datetime.strptime(ave.fecha_nacimiento, '%Y-%m-%d').date()
            else:
                # Si ya es un objeto tipo fecha (datetime o date)
                fecha_nac = getattr(ave.fecha_nacimiento, 'date', lambda: ave.fecha_nacimiento)()
        except Exception as e:
            print(f"Error al leer la fecha del lote {ave.lote_codigo}: {e}")
            continue

            # 2. CALCULAR EDAD ACTUAL EN DÍAS (Exacto)
        dias_edad = (hoy - fecha_nac).days

        # Textos para mostrar la edad bonita en pantalla
        meses = dias_edad // 30
        dias_restantes = dias_edad % 30
        anios = dias_edad // 365

        # Limpiar el nombre de la etapa por si se guardó con mayúsculas o espacios
        etapa_actual = ave.etapa.lower().strip() if ave.etapa else ""
        origen = ave.origen if hasattr(ave, 'origen') else "General"

        # =========================================================
        # RANGO 1: NACIDOS (Límite 29 días, al día 30 pasan)
        # =========================================================
        if etapa_actual == 'nacidos':
            if dias_edad == 29:
                lista_alertas.append({
                    'lote': ave.lote_codigo,
                    'origen': origen,
                    'etapa_actual': 'Nacidos',
                    'edad_texto': f"{dias_edad} días",
                    'mensaje': "Falta 1 día. ¡Mañana este lote debe pasar a la etapa de Desarrollo!",
                    'color_alerta': 'warning',
                    'icono': 'fa-exclamation-triangle'
                })
            elif dias_edad >= 30:
                lista_alertas.append({
                    'lote': ave.lote_codigo,
                    'origen': origen,
                    'etapa_actual': 'Nacidos',
                    'edad_texto': f"{dias_edad} días",
                    'mensaje': "¡Límite superado! Este lote ya tiene 30 días o más y debe ser movido a Desarrollo.",
                    'color_alerta': 'danger',
                    'icono': 'fa-arrow-right'
                })

        # =========================================================
        # RANGO 2: DESARROLLO (Límite 3 meses 29 días [119 días], a los 4 meses [120 días] pasan)
        # =========================================================
        elif etapa_actual == 'desarrollo':
            if dias_edad == 119:
                lista_alertas.append({
                    'lote': ave.lote_codigo,
                    'origen': origen,
                    'etapa_actual': 'Desarrollo',
                    'edad_texto': "3 meses y 29 días",
                    'mensaje': "Falta 1 día. ¡Mañana este lote cumple 4 meses y debe pasar a Grandes/Reproductores!",
                    'color_alerta': 'warning',
                    'icono': 'fa-exclamation-triangle'
                })
            elif dias_edad >= 120:
                lista_alertas.append({
                    'lote': ave.lote_codigo,
                    'origen': origen,
                    'etapa_actual': 'Desarrollo',
                    'edad_texto': f"{meses} meses y {dias_restantes} días",
                    'mensaje': "¡Límite superado! Este lote ya cumplió 4 meses y debe pasar a Grandes/Reproductores.",
                    'color_alerta': 'danger',
                    'icono': 'fa-arrow-right'
                })

        # =========================================================
        # RANGO 3: GRANDES / REPRODUCTORES / ENGORDE (Aviso al año [365 días])
        # =========================================================
        # Agregué 'engorde' por si lo guardas así en la BD, como vi en tu HTML
        elif etapa_actual in ['engorde', 'grandes', 'reproductores']:
            if dias_edad >= 365:
                meses_sobrantes = meses % 12
                texto_edad = f"{anios} año(s)" if meses_sobrantes == 0 else f"{anios} año(s) y {meses_sobrantes} meses"

                lista_alertas.append({
                    'lote': ave.lote_codigo,
                    'origen': origen,
                    'etapa_actual': 'Grandes/Reproductores',
                    'edad_texto': texto_edad,
                    'mensaje': "Atención: Este lote ya cumplió 1 año de edad o más. Están viejos y su nivel productivo puede decaer.",
                    'color_alerta': 'info',
                    'icono': 'fa-clock'
                })

    # Ordenar por importancia: Rojas (danger) primero
    orden_prioridad = {'danger': 1, 'warning': 2, 'info': 3}
    lista_alertas.sort(key=lambda x: orden_prioridad.get(x['color_alerta'], 4))

    return render_template('alertas.html', alertas=lista_alertas)
@app.route('/graficas')
def graficas():
    if 'user_id' not in session: return redirect(url_for('home'))

    # 1. Capturar filtros de la URL (siempre como strings)
    filtro_anio = request.args.get('anio', 'Todos')
    filtro_mes = request.args.get('mes', 'Todos')

    # Traemos todos los registros
    ventas_all = Venta.query.all()
    aves_compradas = Ave.query.filter_by(origen='Compra').all()
    insumos_all = Insumo.query.all()
    bajas_all = Baja.query.all()

    # Variables acumuladoras
    total_ventas = 0
    total_compras_aves = 0
    cant_aves_compradas = 0
    total_compras_insumos = 0
    total_perdidas_muertes = 0
    cant_aves_muertas = 0

    from collections import defaultdict
    ingresos_dict = defaultdict(float)

    # 2. Asegurarnos de que EL AÑO ACTUAL siempre exista en la lista, haya o no ventas
    anios_set = set()
    anios_set.add(str(datetime.now().year))

    # --- PROCESAR VENTAS ---
    for v in ventas_all:
        fecha = v.fecha_venta
        if not fecha: continue

        v_anio = str(fecha.year)
        v_mes = str(fecha.month)

        anios_set.add(v_anio)

        # Aplicar el filtro dinámico
        if filtro_anio != 'Todos' and v_anio != filtro_anio: continue
        if filtro_mes != 'Todos' and v_mes != filtro_mes: continue

        # Si pasa el filtro, sumamos la plata
        ingreso = (v.subtotal_aves or 0) + (v.valor_envio or 0) - (v.costo_envio_real or 0)
        total_ventas += ingreso

        # Agrupar datos para la curva
        if filtro_anio != 'Todos' and filtro_mes != 'Todos':
            dia_str = str(fecha.day).zfill(2)
            ingresos_dict[dia_str] += ingreso
        else:
            mes_str = f"{fecha.year}-{str(fecha.month).zfill(2)}"
            ingresos_dict[mes_str] += ingreso

    # --- PROCESAR COMPRA DE AVES ---
    for a in aves_compradas:
        fecha = a.fecha_registro or a.fecha_nacimiento
        if not fecha: continue
        if filtro_anio != 'Todos' and str(fecha.year) != filtro_anio: continue
        if filtro_mes != 'Todos' and str(fecha.month) != filtro_mes: continue

        total_compras_aves += (a.monto_pago or 0)
        cant_aves_compradas += (a.cantidad or 0)

    # --- PROCESAR INSUMOS ---
    for i in insumos_all:
        fecha = i.fecha
        if not fecha: continue
        if filtro_anio != 'Todos' and str(fecha.year) != filtro_anio: continue
        if filtro_mes != 'Todos' and str(fecha.month) != filtro_mes: continue

        total_compras_insumos += (i.valor_total or 0)

    # --- PROCESAR MORTALIDAD (BAJAS) ---
    for b in bajas_all:
        fecha = b.fecha_baja
        if not fecha: continue
        if filtro_anio != 'Todos' and str(fecha.year) != filtro_anio: continue
        if filtro_mes != 'Todos' and str(fecha.month) != filtro_mes: continue

        total_perdidas_muertes += (b.perdida_economica or 0)
        cant_aves_muertas += (b.cantidad_total or 0)

    # 3. Cálculos Finales KPIs
    gastos_totales = total_compras_aves + total_compras_insumos
    rentabilidad = total_ventas - gastos_totales - total_perdidas_muertes
    inversion = gastos_totales + total_perdidas_muertes

    roi = (rentabilidad / inversion * 100) if inversion > 0 else 0
    tasa_mortalidad = (cant_aves_muertas / cant_aves_compradas * 100) if cant_aves_compradas > 0 else 0

    # 4. Preparar la Gráfica de Curva
    if filtro_anio != 'Todos' and filtro_mes != 'Todos':
        claves_ordenadas = sorted(ingresos_dict.keys())
        prefijo = "Día "
    else:
        claves_ordenadas = sorted(ingresos_dict.keys())[-12:]
        prefijo = "Mes "

    etiquetas_ingresos = claves_ordenadas
    totales_ingresos = [ingresos_dict[k] for k in claves_ordenadas]

    mejor_periodo_val = max(ingresos_dict.items(), key=lambda x: x[1]) if ingresos_dict else ("N/A", 0)
    peor_periodo_val = min(ingresos_dict.items(), key=lambda x: x[1]) if ingresos_dict else ("N/A", 0)

    mejor_periodo = f"{prefijo}{mejor_periodo_val[0]}" if ingresos_dict else "N/A"
    peor_periodo = f"{prefijo}{peor_periodo_val[0]}" if ingresos_dict else "N/A"

    anios_lista = sorted(list(anios_set), reverse=True)

    return render_template(
        'graficas.html',
        ventas=float(total_ventas),
        gastos_totales=float(gastos_totales),
        rentabilidad=float(rentabilidad),
        roi=float(roi),
        tasa_mortalidad=float(tasa_mortalidad),
        mejor_periodo=mejor_periodo,
        peor_periodo=peor_periodo,
        compra_aves=float(total_compras_aves),
        compra_insumos=float(total_compras_insumos),
        perdidas_muertes=float(total_perdidas_muertes),
        etiquetas_ingresos=json.dumps(etiquetas_ingresos),
        totales_ingresos=json.dumps(totales_ingresos),
        filtro_anio=filtro_anio,
        filtro_mes=filtro_mes,
        anios_lista=anios_lista
    )


# ==========================================
# GESTIÓN DE USUARIOS / COLABORADORES
# ==========================================
@app.route('/colaboradores')
def colaboradores():
    if 'user_id' not in session: return redirect(url_for('home'))

    # Consultamos todos los usuarios de la base de datos
    usuarios = User.query.all()

    # Pasamos los usuarios y el rol actual del usuario logueado
    return render_template('lista_colaboradores.html',
                           usuarios=usuarios,
                           rol_actual=session.get('role'))


@app.route('/eliminar_colaborador/<int:id>', methods=['POST', 'GET'])
def eliminar_colaborador(id):
    if 'user_id' not in session: return redirect(url_for('home'))

    # SEGURIDAD: Solo un 'Propietario' puede eliminar usuarios
    if session.get('role') != 'Propietario':
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('colaboradores'))

    usuario_a_eliminar = User.query.get_or_404(id)

    # SEGURIDAD: Evitar que el propietario logueado se elimine a sí mismo por error
    if usuario_a_eliminar.id == session['user_id']:
        flash('No puedes eliminar tu propia cuenta activa.', 'warning')
        return redirect(url_for('colaboradores'))

    try:
        db.session.delete(usuario_a_eliminar)
        db.session.commit()
        flash(f'El usuario {usuario_a_eliminar.nombres} ha sido eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {e}', 'danger')

    return redirect(url_for('colaboradores'))


@app.route('/reparar-base-de-datos')
def reparar_base_de_datos():
    try:
        db.drop_all()
        db.create_all()
        session.clear()
        return "<h1>Base de datos reseteada con éxito</h1><p>Todos los datos han sido borrados. Estructura actualizada con campo de comprobante. <a href='/'>Volver al inicio</a></p>"
    except Exception as e:
        return f"<h1>Error al reparar: {e}</h1>"


if __name__ == '__main__':
    app.run(debug=True)