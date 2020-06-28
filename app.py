from io import BytesIO
from flask import Flask, render_template, send_file, request
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import jinja2
from random import randint, seed
from datetime import datetime
plt.style.use('ggplot')

app = Flask(__name__)
my_loader = jinja2.ChoiceLoader([
    app.jinja_loader
])
app.jinja_loader = my_loader
app.static_folder = 'static'


@app.route('/vis/<j>')
def vis(j):
    seed(datetime.now())
    n = 10
    p1 = [randint(0, 10) for _ in range(n)]
    p2 = [randint(0, 10) for _ in range(n)]
    t = [i for i in range(n)]
    fig, _ = plt.subplots()
    plt.plot(t, p1, color='blue')
    plt.plot(t, p2, color='orange')
    plt.xlabel('Time')
    plt.ylabel('Value')
    img = BytesIO()
    fig.savefig(img, dpi=128)
    img.seek(0)
    return send_file(img, mimetype='image/png')

@app.route('/')
def index():
    # TODO: Modify to display Comunas
    data = ['Las Condes', 'Providencia', 'La Pintana', 'Lo Barnechea', 'Santiago']
    return render_template('index.html', data=data)

@app.route('/consideraciones')
def consideraciones():
    return render_template('consideraciones.html')

@app.route('/datos')
def datos():
    return render_template('datos.html')

@app.route("/comuna" , methods=['GET', 'POST'])
def comuna():
    select = request.form.get('select-comuna')
    return render_template('analizar_comuna.html', name=str(select)) #TODO: Ir a la página

@app.after_request
def add_header(r):
    """
    Forzar refresco de cache después de cada request
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

if __name__ == '__main__':
    app.run(threaded=False, debug=True)