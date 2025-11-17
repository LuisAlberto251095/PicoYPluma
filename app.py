import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Configuración de la Base de Datos (Sigue igual) ---
# La dejamos lista para cuando conectemos el login
db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Ruta Principal (Home) ---
# Ahora, esta ruta simplemente mostrará nuestra nueva
# página de inicio (el login).
@app.route("/")
def home():
    # Renderizamos el archivo 'home.html'
    return render_template('home.html')

# --- El 'if __name__' (Sigue igual) ---
if __name__ == "__main__":
    app.run(debug=True)


