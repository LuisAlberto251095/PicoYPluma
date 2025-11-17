from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hola, esta es tu página web en Python funcionando 24/7!"

if __name__ == "__main__":
    app.run()
