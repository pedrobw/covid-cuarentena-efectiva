from io import BytesIO # Para generar bytes de la img de plot "on the fly" con url
from flask import Flask, render_template, send_file, request, redirect # Flask app
import jinja2 # Para manejo de estructura de la Flask app
from random import randint, seed # Para test de gráficos random
from datetime import datetime # Para random seed
from time import sleep # Para lock
# Imports necesarios para trabajar base de datos
from pandas import to_datetime, read_csv # Trabajar con BDs
from sqlalchemy import create_engine # Para consultas
from sqlalchemy.types import DateTime, Integer # Especificar tipos al transformar BD
from datetime import date, datetime, timedelta # Para manejo de fechas, especialmente de headers
# Para hacer plots con Matplotlib
import matplotlib
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
from numpy import log
matplotlib.use('Agg')
plt.style.use('ggplot')

app = Flask(__name__)
my_loader = jinja2.ChoiceLoader([
    app.jinja_loader
])
app.jinja_loader = my_loader
app.static_folder = 'static'
queue = [False for i in range(11)]


# Nombres auxiliares
# Cuarentenas: Fechas de inicio y término
qt = 'Cuarentenas totales'

# Contagio
ct = 'Casos totales' # Nota: Población por comuna se puede encontrar acá
ca = 'Casos actuales por fecha de inicio de síntomas'
cn = 'Casos nuevos por fecha de inicio de síntomas'
# Nota: Para tiempo de duplicación, utilizar Casos totales
vd = 'Viajes diarios' # Nota: Solo disponibles en RM

# Letalidad
dn = 'Decesos nuevos' # Nota: Disponible desde el 14 de junio

# Trazabilidad - Nada por comuna
# Disponibilidad - Nada por comuna
# Otros - Nada por comuna

# URLS DE DATOS REQUERIDOS
urls = {}
# Cuarentenas
urls[qt] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto29/Cuarentenas-Totales.csv'
# Contagio
urls[ct] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto1/Covid-19.csv'
urls[ca] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto1/Covid-19.csv'
urls[cn] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto15/FechaInicioSintomas.csv'
urls[vd] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto42/ViajesComunas_std.csv'
# Letalidad
urls[dn] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto38/CasosFallecidosPorComuna.csv'
# Trazabilidad - Nada por comuna
# Disponibilidad - Nada por comuna
# Otros - Nada por comuna


# Engine para queries de SQLite
engine = create_engine('sqlite://', echo=False, connect_args={"check_same_thread": False})
# Datos
def get_csvs():
    '''Crea las bases de datos CSVs a partir de los repositorios''' 
    dbs = {}
    for abbr in urls.keys():
        try:
            dbs[abbr] = read_csv(urls[abbr], error_bad_lines=False)
            print("OK", abbr)
        except Exception as e:
            print(e)
            exit()
    return dbs

def csv_to_db():
    # Base de datos
    dbs[qt]['Fecha de Inicio'] = to_datetime(dbs[qt]['Fecha de Inicio'])
    dbs[qt]['Fecha de Término'] = to_datetime(dbs[qt]['Fecha de Término'])
    dbs[qt].to_sql(qt, con=engine, dtype={
        'Fecha de Inicio': DateTime(),
        'Fecha de Término': DateTime(),
        'Código CUT Comuna': Integer()
    })
    dbs[ct].to_sql(ct, con=engine, dtype={
        'Codigo comuna': Integer(),
        'Poblacion': Integer()
    })

dbs = get_csvs()

# Funciones auxiliares para procesar datos

def string_to_date(s):
    '''Convierte una fecha en un datetime'''
    return datetime(*(int(i) for i in s.split('-')))

def SE_to_date(s):
    '''Convierte una semana epidemiológica en una fecha'''
    return datetime(2020, 2, 15) + timedelta(7 * (int(s.split("SE")[1]) - 7))

def date_headers(abbv, date_from, date_to):
    return [col for col in dbs[abbv].columns if (
        ('2020-' in col) and ((string_to_date(col) >= date_from) and (string_to_date(col) <= date_to))
    )]

def SE_headers(abbv, date_from, date_to):
    return [col for col in dbs[abbv].columns if (
        ('SE' in col) and ((SE_to_date(col) >= date_from) and (SE_to_date(col) <= date_to))
    )]

def headers_to_col_query(l):
    return "`{}`".format("`, `".join(l))

def calcular_pendiente(x, y):
    return (y[1] - y[0]) / (x[1] - x[0]).days

# Interpretaciones de los resultados

# Confirmados totales
def interpretar_0(m_pre, m_post):
    t = """Como se puede observar en el gráfico, la pendiente del período en donde la cuarentena 
    aún no debería hacer efecto es de {:.1f}, mientras que en el período donde ya la cuarentena 
    está activa o recién terminada, alcanza un valor de {:.1f}, es decir, {}. Por lo tanto, en términos
    de reducir el ritmo de aumento de los casos confirmados, la cuarentena ha sido {}. Más 
    precisamente, el ritmo de aumento de los casos confirmados varió, en promedio, en un 
    {:.1f}%""".format(
        m_pre,
        m_post,
        "mayor" if m_post > m_pre else "menor" if m_post < m_pre else "igual",
        "inefectiva" if m_post > m_pre else "efectiva" if m_post < m_pre else "igual",
        100 * (m_post - m_pre)/m_pre
    )
    return t

# Confirmados por 100k habitantes
def interpretar_1(m_pre, m_post):
    t = """La interpretación es idéntica a la de confirmados totales, con la excepción de que se 
    escala el gráfico para tener mejor apreciación relativa a otras comunas demográficamente 
    distintas. Como se puede observar en el gráfico, la pendiente del período en donde la cuarentena 
    aún no debería hacer efecto es de {:.1f}, mientras que en el período donde ya la cuarentena 
    está activa o recién terminada, alcanza un valor de {:.1f}, es decir, {}. Por lo tanto, en términos
    de reducir el ritmo de aumento de los casos confirmados por 100 mil habitantes, la cuarentena 
    ha sido {}. Más precisamente, el ritmo de aumento de los casos confirmados por 100 mil 
    habitantes varió, en promedio, en un {:.1f}%""".format(
        m_pre,
        m_post,
        "mayor" if m_post > m_pre else "menor" if m_post < m_pre else "igual",
        "inefectiva" if m_post > m_pre else "efectiva" if m_post < m_pre else "igual",
        100 * (m_post - m_pre)/m_pre
    )
    return t


@app.route('/vis/<j>')
def vis(j):
    global queue
    j = int(j)
    while not queue[j-1]:
        sleep(0.5)
    seed(datetime.now())
    n = 10
    p1 = [randint(0, 10) for _ in range(n)]
    p2 = [randint(0, 10) for _ in range(n)]
    t = [i for i in range(n)]
    fig = plt.figure(j)
    plt.clf()
    plt.margins(x=0, y=0, tight=True)
    plt.plot(t, p1, color='blue')
    plt.plot(t, p2, color='orange')
    plt.xlabel('Time')
    plt.ylabel('Value')
    img = BytesIO()
    fig.savefig(img, bbox_inches='tight', dpi=150)
    img.seek(0)
    queue[j] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/0/<sel_comuna>')
def vis0(sel_comuna):
    global queue
    for i in range(len(queue)):
        queue[i] = False
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    # Fechas importantes a revisar
    dia_inicio = q_comuna['Fecha de Inicio'].split(" ")[0]
    dia_termino = q_comuna['Fecha de Término'].split(" ")[0]
    # Antes de la cuarentena
    pre_fecha_0 = string_to_date(dia_inicio) + timedelta(days=-14)
    pre_fecha_1 = string_to_date(dia_inicio)
    # Período de transición
    trans_fecha_0 = string_to_date(dia_inicio)
    trans_fecha_1 = string_to_date(dia_inicio) + timedelta(days=14)
    # Período de plena cuarentena
    tot_fecha_0 = string_to_date(dia_inicio) + timedelta(days=14)
    tot_fecha_1 = string_to_date(dia_termino)
    # Período de cuarentena efectiva
    post_fecha_0 = string_to_date(dia_termino)
    post_fecha_1 = string_to_date(dia_termino) + timedelta(days=14)

    dates = [
        date_headers(ct, pre_fecha_0, pre_fecha_1),
        date_headers(ct, trans_fecha_0, trans_fecha_1),
        date_headers(ct, tot_fecha_0, tot_fecha_1),
        date_headers(ct, post_fecha_0, post_fecha_1)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [string_to_date(i) for i in dates[0]]
    trans_fechas = [string_to_date(i) for i in dates[1]]
    tot_fechas = [string_to_date(i) for i in dates[2]]
    post_fechas = [string_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales

    # Plot
    fig = plt.figure(0)
    plt.clf()
    ax = plt.axes()
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
    plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel('Casos totales confirmados', **hfont)
    plt.xticks(rotation=20, ha='right')
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    img = BytesIO()
    fig.savefig(img, bbox_inches='tight', dpi=150)
    img.seek(0)
    queue[0] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/1/<sel_comuna>')
def vis1(sel_comuna):
    global queue
    while not queue[0]:
        sleep(0.5)
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    # Fechas importantes a revisar
    dia_inicio = q_comuna['Fecha de Inicio'].split(" ")[0]
    dia_termino = q_comuna['Fecha de Término'].split(" ")[0]
    # Antes de la cuarentena
    pre_fecha_0 = string_to_date(dia_inicio) + timedelta(days=-14)
    pre_fecha_1 = string_to_date(dia_inicio)
    # Período de transición
    trans_fecha_0 = string_to_date(dia_inicio)
    trans_fecha_1 = string_to_date(dia_inicio) + timedelta(days=14)
    # Período de plena cuarentena
    tot_fecha_0 = string_to_date(dia_inicio) + timedelta(days=14)
    tot_fecha_1 = string_to_date(dia_termino)
    # Período de cuarentena efectiva
    post_fecha_0 = string_to_date(dia_termino)
    post_fecha_1 = string_to_date(dia_termino) + timedelta(days=14)

    dates = [
        date_headers(ct, pre_fecha_0, pre_fecha_1),
        date_headers(ct, trans_fecha_0, trans_fecha_1),
        date_headers(ct, tot_fecha_0, tot_fecha_1),
        date_headers(ct, post_fecha_0, post_fecha_1)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [string_to_date(i) for i in dates[0]]
    trans_fechas = [string_to_date(i) for i in dates[1]]
    tot_fechas = [string_to_date(i) for i in dates[2]]
    post_fechas = [string_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    pre_casos_totales = [100000*i/poblacion for i in pre_casos_totales]
    trans_casos_totales = [100000*i/poblacion for i in trans_casos_totales]
    tot_casos_totales = [100000*i/poblacion for i in tot_casos_totales]
    post_casos_totales = [100000*i/poblacion for i in post_casos_totales]
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales

    # Plot
    fig = plt.figure(0)
    plt.clf()
    ax = plt.axes()
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
    plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel('Casos confirmados por 100.000 hab.', **hfont)
    plt.xticks(rotation=30, ha='right')
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, bbox_inches='tight', dpi=150)
    img.seek(0)
    queue[1] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/2/<sel_comuna>')
def vis2(sel_comuna):
    global queue
    while not queue[1]:
        sleep(0.5)
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    # Fechas importantes a revisar
    dia_inicio = q_comuna['Fecha de Inicio'].split(" ")[0]
    dia_termino = q_comuna['Fecha de Término'].split(" ")[0]
    # Antes de la cuarentena
    pre_fecha_0 = string_to_date(dia_inicio) + timedelta(days=-14)
    pre_fecha_1 = string_to_date(dia_inicio)
    # Período de transición
    trans_fecha_0 = string_to_date(dia_inicio)
    trans_fecha_1 = string_to_date(dia_inicio) + timedelta(days=14)
    # Período de plena cuarentena
    tot_fecha_0 = string_to_date(dia_inicio) + timedelta(days=14)
    tot_fecha_1 = string_to_date(dia_termino)
    # Período de cuarentena efectiva
    post_fecha_0 = string_to_date(dia_termino)
    post_fecha_1 = string_to_date(dia_termino) + timedelta(days=14)

    dates = [
        date_headers(ct, pre_fecha_0, pre_fecha_1),
        date_headers(ct, trans_fecha_0, trans_fecha_1),
        date_headers(ct, tot_fecha_0, tot_fecha_1),
        date_headers(ct, post_fecha_0, post_fecha_1)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [string_to_date(i) for i in dates[0]]
    trans_fechas = [string_to_date(i) for i in dates[1]]
    tot_fechas = [string_to_date(i) for i in dates[2]]
    post_fechas = [string_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales

    # Plot
    fig = plt.figure(0)
    plt.clf()
    ax = plt.axes()
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
    plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel('Casos totales confirmados', **hfont)
    plt.xticks(rotation=30, ha='right')
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, bbox_inches='tight', dpi=150)
    img.seek(0)
    queue[2] = True
    return send_file(img, mimetype='image/png')

@app.route('/')
def index():
    csv_to_db()
    # Lista de (Cuarentenas de) Comunas Disponibles
    comunas_disponibles = [i[0] for i in engine.execute("SELECT Nombre from '{}'".format(qt)).fetchall()]
    comunas_disponibles.sort()

    return render_template('index.html', data=comunas_disponibles)

@app.route('/consideraciones')
def consideraciones():
    return render_template('consideraciones.html')

@app.route('/datos')
def datos():
    return render_template('datos.html')

@app.route("/comuna" , methods=['GET', 'POST'])
def comuna():
    select = request.form.get('select-comuna')
    return redirect("/comuna/{}".format(select))

@app.route("/comuna/<select>")
def comuna_select(select):
    csv_to_db()
    # Lista de (Cuarentenas de) Comunas Disponibles
    comunas_disponibles = [i[0] for i in engine.execute("SELECT Nombre from '{}'".format(qt)).fetchall()]
    if select not in comunas_disponibles:
        select = None
        return render_template(
            'analizar_comuna.html',
            name=select
        )

    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, select)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    # Descripción de la cuarentena
    alcance = q_comuna['Alcance']
    descripcion = q_comuna['Detalle']
    # Fechas importantes a revisar
    dia_inicio = q_comuna['Fecha de Inicio'].split(" ")[0]
    dia_termino = q_comuna['Fecha de Término'].split(" ")[0]
    # Antes de la cuarentena
    pre_fecha_0 = string_to_date(dia_inicio) + timedelta(days=-14)
    pre_fecha_1 = string_to_date(dia_inicio)
    # Período de transición
    trans_fecha_0 = string_to_date(dia_inicio)
    trans_fecha_1 = string_to_date(dia_inicio) + timedelta(days=14)
    # Período de plena cuarentena
    tot_fecha_0 = string_to_date(dia_inicio) + timedelta(days=14)
    tot_fecha_1 = string_to_date(dia_termino)
    # Período de cuarentena efectiva
    post_fecha_0 = string_to_date(dia_termino)
    post_fecha_1 = string_to_date(dia_termino) + timedelta(days=14)

    dates = [
        date_headers(ct, pre_fecha_0, pre_fecha_1),
        date_headers(ct, trans_fecha_0, trans_fecha_1),
        date_headers(ct, tot_fecha_0, tot_fecha_1),
        date_headers(ct, post_fecha_0, post_fecha_1)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [string_to_date(i) for i in dates[0]]
    trans_fechas = [string_to_date(i) for i in dates[1]]
    tot_fechas = [string_to_date(i) for i in dates[2]]
    post_fechas = [string_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales

    
    pre_x = [pre_fechas_line[0], pre_fechas_line[-1]]
    pre_y = [pre_casos_line[0], pre_casos_line[-1]]
    post_x = [post_fechas_line[0], post_fechas_line[-1]]
    post_y = [post_casos_line[0], post_casos_line[-1]]
    m_pre = calcular_pendiente(pre_x, pre_y)
    m_post = calcular_pendiente(post_x, post_y)
    text_0 = interpretar_0(m_pre, m_post)
    # Conservamos las pendientes porque son idénticas, por escalamiento
    text_1 = interpretar_1(m_pre, m_post)

    

    return render_template(
        'analizar_comuna.html',
        name=select,
        poblacion=poblacion,
        dia_inicio="/".join(dia_inicio.split("-")[::-1]),
        dia_termino="/".join(dia_termino.split("-")[::-1]),
        descripcion=descripcion,
        alcance=alcance,
        text_0=text_0,
        text_1=text_1
    )

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
    app.run(debug=True)