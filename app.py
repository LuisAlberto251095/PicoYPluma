import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Configuración de la Base de Datos ---

# 1. Obtenemos la URL de la variable de entorno que configuraste en Render
db_url = os.environ.get("DATABASE_URL")

# 2. Pequeño truco: Render usa "postgres://", pero SQLAlchemy (la librería de Python)
#    prefiere "postgresql://". Los reemplazamos para evitar errores.
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# 3. Configuramos la app de Flask
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Para evitar warnings
db = SQLAlchemy(app)

# --- Definición de un Modelo (Ejemplo: un contador de visitas) ---
# Un modelo es cómo se verá la "tabla" en nuestra base de datos.
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Podríamos añadir más campos si quisiéramos, como:
    # nombre = db.Column(db.String(100))

    def __repr__(self):
        return f'<Visitor {self.id}>'

# --- Ruta Principal (Home) ---
@app.route("/")
def home():
    # Esta función ahora hará 3 cosas:
    
    # 1. Contar los visitantes que ya están en la base de datos
    visitor_count = Visitor.query.count()
    
    # 2. Añadir este nuevo visitante a la base de datos
    new_visitor = Visitor()
    db.session.add(new_visitor)
    db.session.commit()
    
    # 3. Mostrar el total (nuevo + anteriores)
    total_visitantes = visitor_count + 1
    
    return f"¡Hola! Tu web en Python ahora tiene conexión a Base de Datos. Visitantes totales: {total_visitantes}"

# --- Creación de las tablas ---
# Esto es importante: le dice a la base de datos que cree la tabla "Visitor"
# si es que no existe.
with app.app_context():
