from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Ruta principal que muestra el login
@app.route('/')
def home():
    return render_template('login.html')

# Ruta para procesar el inicio de sesión (simulada)
@app.route('/login', methods=['POST'])
def login():
    # Aquí iría tu lógica de validación de usuario real
    return "Intentando iniciar sesión..."

if __name__ == '__main__':
    app.run(debug=True)
