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
urls[ca] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto25/CasosActualesPorComuna.csv'
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

dbs = get_csvs()

def csv_to_db():
    # Base de datos
    dbs[qt]['Fecha de Inicio'] = to_datetime(dbs[qt]['Fecha de Inicio'])
    dbs[qt]['Fecha de Término'] = to_datetime(dbs[qt]['Fecha de Término'])
    dbs[vd]['Fecha'] = to_datetime(dbs[vd]['Fecha'])
    dbs[qt].to_sql(qt, con=engine, dtype={
        'Fecha de Inicio': DateTime(),
        'Fecha de Término': DateTime(),
        'Código CUT Comuna': Integer()
    })
    dbs[ct].to_sql(ct, con=engine, dtype={
        'Codigo comuna': Integer(),
        'Poblacion': Integer()
    })
    dbs[ca].to_sql(ca, con=engine, dtype={
        'Codigo comuna': Integer(),
        'Poblacion': Integer()
    })

    dbs[cn].to_sql(cn, con=engine, dtype={
        'Codigo comuna': Integer(),
        'Poblacion': Integer()
    })

    dbs[vd].to_sql(vd, con=engine, dtype={
        'Fecha': DateTime(),
        'Viajes': Integer()
    })

def get_fechas(q_comuna):
    # Fechas importantes a revisar
    dia_inicio = q_comuna['Fecha de Inicio'].split(" ")[0]
    dia_termino = q_comuna['Fecha de Término'].split(" ")[0]
    # Antes de la cuarentena
    pre_fecha_0 = string_to_date(dia_inicio) + timedelta(days=-14)
    pre_fecha_1 = string_to_date(dia_inicio)
    pre_fechas = (pre_fecha_0, pre_fecha_1)
    # Período de transición
    trans_fecha_0 = string_to_date(dia_inicio)
    trans_fecha_1 = string_to_date(dia_inicio) + timedelta(days=14)
    trans_fechas = (trans_fecha_0, trans_fecha_1)
    # Período de plena cuarentena
    tot_fecha_0 = string_to_date(dia_inicio) + timedelta(days=14)
    tot_fecha_1 = string_to_date(dia_termino)
    tot_fechas = (tot_fecha_0, tot_fecha_1)
    # Período de post-cuarentena con efectos residuales
    post_fecha_0 = string_to_date(dia_termino)
    post_fecha_1 = string_to_date(dia_termino) + timedelta(days=7)
    post_fechas = (post_fecha_0, post_fecha_1)
    return dia_inicio, dia_termino, pre_fechas, trans_fechas, tot_fechas, post_fechas


# Funciones auxiliares para procesar datos

def string_to_date(s):
    '''Convierte una fecha en un datetime'''
    return datetime(*(int(i) for i in s.split('-')))

def SE_to_date(s):
    '''Convierte una semana epidemiológica en una fecha'''
    return datetime(2020, 2, 15) + timedelta(7 * (int(s.split("SE")[1]) - 7))

def date_headers(abbv, from_to_date):
    return [col for col in dbs[abbv].columns if (
        ('2020-' in col) and ((string_to_date(col) >= from_to_date[0]) and (string_to_date(col) <= from_to_date[1]))
    )]

def SE_headers(abbv, from_to_date):
    return [col for col in dbs[abbv].columns if (
        ('SE' in col) and ((SE_to_date(col) >= from_to_date[0]) and (SE_to_date(col) <= from_to_date[1]))
    )]

def headers_to_col_query(l):
    return "`{}`".format("`, `".join(l))

def calcular_pendiente(x, y):
    return (y[1] - y[0]) / ((x[1] - x[0]).days + 0.000001)

# Interpretaciones de los resultados

# Confirmados totales
def interpretar_0(pre_x, pre_y, post_x, post_y):
    m_pre = calcular_pendiente(pre_x, pre_y)
    m_post = calcular_pendiente(post_x, post_y)
    t = """Como se puede observar en el gráfico, la pendiente del período en donde la cuarentena 
    aún no debería hacer efecto es de {:.1f}, mientras que en el período donde ya la cuarentena 
    está activa o recién terminada, alcanza un valor de {:.1f}, es decir, {}. Por lo tanto, en términos
    de reducir el ritmo de aumento de los casos confirmados, la cuarentena ha sido {}. Más 
    precisamente, el ritmo de aumento de los casos confirmados varió, en promedio, en un 
    {:.1f}%.""".format(
        m_pre,
        m_post,
        "mayor" if m_post > m_pre else "menor" if m_post < m_pre else "igual",
        "inefectiva" if m_post > m_pre else "efectiva" if m_post < m_pre else "igual",
        100 * (m_post - m_pre)/m_pre
    )
    return t

# Confirmados por 100k habitantes
def interpretar_1(pre_x, pre_y, post_x, post_y):
    m_pre = calcular_pendiente(pre_x, pre_y)
    m_post = calcular_pendiente(post_x, post_y)
    t = """La interpretación es idéntica a la de confirmados totales, con la excepción de que se 
    escala el gráfico a la población para tener mejor apreciación relativa a otras comunas demográficamente 
    distintas. Como se puede observar en el gráfico, la pendiente del período en donde la cuarentena 
    aún no debería hacer efecto es de {:.1f}, mientras que en el período donde ya la cuarentena 
    está activa o recién terminada, alcanza un valor de {:.1f}, es decir, {}. Por lo tanto, en términos
    de reducir el ritmo de aumento de los casos confirmados por 100 mil habitantes, la cuarentena 
    ha sido {}. Más precisamente, el ritmo de aumento de los casos confirmados por 100 mil 
    habitantes varió, en promedio, en un {:.1f}%.""".format(
        m_pre,
        m_post,
        "mayor" if m_post > m_pre else "menor" if m_post < m_pre else "igual",
        "inefectiva" if m_post > m_pre else "efectiva" if m_post < m_pre else "igual",
        100 * (m_post - m_pre)/m_pre
    )
    return t

# Confirmados actuales
def interpretar_2(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line):
    t = """Como se puede apreciar, el número de casos actuales {} desde el inicio de la plenitud 
    de la cuarentena, lo cual es relativamente {}.""".format(
        "ha disminuido" if post_y[1] < post_y[0] else "ha aumentado" if post_y[1]> post_y[0] else "se ha mantenido",
        "positivo" if post_y[1] < post_y[0] else "negativo" if post_y[1]> post_y[0] else "neutro",
    )
    if len(pre_fechas_line) > 1 and len(post_fechas_line) > 1:
        m_pre = calcular_pendiente(pre_x, pre_y)
        m_post = calcular_pendiente(post_x, post_y)
        if m_post > 0 and m_post < m_pre:
            t += """ Sin embargo, se puede observar que desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos ha disminuido. Más precisamente, se observa una variación promedio de un 
            {:.1f}%.""".format(
                100 * (m_post - m_pre)/m_pre
            )
        elif m_pre < 0 and m_post > 0:
            t += """ Por lo demás, se ha pasado de un ritmo de cambio negativo a uno positivo, lo cual puede ser 
            considerado un total fracaso como cuarentena."""
        elif m_pre > 0 and m_post > m_pre:
            t += """ Podemos observar además que desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos ha empeorado. Más precisamente, se observa una aumento promedio de un 
            {:.1f}%.""".format(
                100 * (m_post - m_pre)/m_pre
            )
    return t

# Confirmados actuales por 100k hab.
def interpretar_3(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line):
    t = """La interpretación es idéntica a la de confirmados actuales, con la excepción de que se 
    escala el gráfico a la población para tener mejor apreciación relativa a otras comunas demográficamente 
    distintas. Como se puede apreciar, el número de casos actuales {} desde el inicio de la 
    plenitud de la cuarentena, lo cual es relativamente {}.""".format(
        "ha disminuido" if post_y[1] < post_y[0] else "ha aumentado" if post_y[1]> post_y[0] else "se ha mantenido",
        "positivo" if post_y[1] < post_y[0] else "negativo" if post_y[1]> post_y[0] else "neutro",
    )
    if len(pre_fechas_line) > 1 and len(post_fechas_line) > 1:
        m_pre = calcular_pendiente(pre_x, pre_y)
        m_post = calcular_pendiente(post_x, post_y)
        if m_post > 0 and m_post < m_pre:
            t += """ Podemos observar además que desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos ha disminuido. Más precisamente, se observa una variación promedio de un 
            {:.1f}%.""".format(
                100 * (m_post - m_pre)/m_pre
            )
        elif m_pre < 0 and m_post > 0:
            t += """ Por lo demás, se ha pasado de un ritmo de cambio negativo a uno positivo, lo cual puede ser 
            considerado un total fracaso como cuarentena."""
        elif m_pre > 0 and m_post > m_pre:
            t += """ Podemos observar además que desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos ha empeorado. Más precisamente, se observa una aumento promedio de un 
            {:.1f}%.""".format(
                100 * (m_post - m_pre)/m_pre
            )
    return t

# Confirmados nuevos
def interpretar_4(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line):
    t = """Es posible notar que el número de casos nuevos {} desde el inicio de la plenitud 
    de la cuarentena, lo cual es considerado {} con respecto a este criterio.""".format(
        "ha disminuido" if post_y[1] < post_y[0] else "ha aumentado" if post_y[1]> post_y[0] else "se ha mantenido",
        "positivo" if post_y[1] < post_y[0] else "negativo" if post_y[1]> post_y[0] else "neutro",
    )
    if post_y[1] == 0:
        t += " Se observa además que ya se llegó a los cero casos nuevos, por lo que la cuarentena ha sido un éxito."
    else:
        t += " Aún no se llega a los cero casos nuevos, por lo que aún no puede decir con plenitud que la cuarentena ha sido un éxito."
    if len(pre_fechas_line) > 1 and len(post_fechas_line) > 1:
        m_pre = calcular_pendiente(pre_x, pre_y)
        m_post = calcular_pendiente(post_x, post_y)
        if m_post > 0 and m_post < m_pre:
            t += """ Se agrega que desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos nuevos ha bajado. Más precisamente, se ha reducido en un 
            {:.1f}% su variación promedio.""".format(
                100 * (m_post - m_pre)/m_pre
            )
        elif m_pre < 0 and m_post > 0:
            t += """ Por lo demás, se ha pasado de un ritmo de cambio negativo a uno positivo, lo cual puede ser 
            considerado un total fracaso como cuarentena."""
        elif m_pre > 0 and m_post > m_pre:
            t += """ Además, desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos nuevos ha crecido. Más precisamente, ha habido aumento de un 
            {:.1f}% en su variación promedio.""".format(
                100 * (m_post - m_pre)/m_pre
            )
    return t

# Confirmados nuevos
def interpretar_5(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line):
    t = """La interpretación es idéntica a la de casos nuevos, con la excepción de que se 
    escala el gráfico a la población para tener mejor apreciación relativa a otras comunas demográficamente 
    distintas. Es posible notar que el número de casos nuevos {} desde el inicio de la plenitud 
    de la cuarentena, lo cual es considerado {} con respecto a este criterio.""".format(
        "ha disminuido" if post_y[1] < post_y[0] else "ha aumentado" if post_y[1]> post_y[0] else "se ha mantenido",
        "positivo" if post_y[1] < post_y[0] else "negativo" if post_y[1]> post_y[0] else "neutro",
    )
    if post_y[1] == 0:
        t += " Se observa además que ya se llegó a los cero casos nuevos, por lo que la cuarentena ha sido un éxito."
    else:
        t += " Aún no se llega a los cero casos nuevos, por lo que aún no puede decir con plenitud que la cuarentena ha sido un éxito."
    if len(pre_fechas_line) > 1 and len(post_fechas_line) > 1:
        m_pre = calcular_pendiente(pre_x, pre_y)
        m_post = calcular_pendiente(post_x, post_y)
        if m_post > 0 and m_post < m_pre:
            t += """ Se agrega que desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos nuevos ha bajado. Más precisamente, se ha reducido en un 
            {:.1f}% su variación promedio.""".format(
                100 * (m_post - m_pre)/m_pre
            )
        elif m_pre < 0 and m_post > 0:
            t += """ Por lo demás, se ha pasado de un ritmo de cambio negativo a uno positivo, lo cual puede ser 
            considerado un total fracaso como cuarentena."""
        elif m_pre > 0 and m_post > m_pre:
            t += """ Además, desde que la cuarentena es plenamente efectiva, el ritmo de 
            aumento de los casos nuevos ha crecido. Más precisamente, ha habido aumento de un 
            {:.1f}% en su variación promedio.""".format(
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
    fig.savefig(img, dpi=120)
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

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        date_headers(ct, pre_fechas),
        date_headers(ct, trans_fechas),
        date_headers(ct, tot_fechas),
        date_headers(ct, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
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
    fig, ax = plt.subplots()#figure(0)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=20, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
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
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
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

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        date_headers(ct, pre_fechas),
        date_headers(ct, trans_fechas),
        date_headers(ct, tot_fechas),
        date_headers(ct, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
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
    pre_casos_totales = [100000 * i / poblacion for i in pre_casos_totales]
    trans_casos_totales = [100000 * i / poblacion for i in trans_casos_totales]
    tot_casos_totales = [100000 * i / poblacion for i in tot_casos_totales]
    post_casos_totales = [100000 * i / poblacion for i in post_casos_totales]
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales

    # Plot
    fig, ax = plt.subplots()#figure(1)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
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
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
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

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        date_headers(ca, pre_fechas),
        date_headers(ca, trans_fechas),
        date_headers(ca, tot_fechas),
        date_headers(ca, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ca, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ca, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ca, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ca, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales

    # Plot
    fig, ax = plt.subplots()#figure(2)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    try:
        plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
        plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    except:
        pass
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel(ca, **hfont)
    
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    queue[2] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/3/<sel_comuna>')
def vis3(sel_comuna):
    global queue
    while not queue[2]:
        sleep(0.5)
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        date_headers(ca, pre_fechas),
        date_headers(ca, trans_fechas),
        date_headers(ca, tot_fechas),
        date_headers(ca, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ca, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ca, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ca, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ca, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    pre_casos_totales = [100000 * i / poblacion for i in pre_casos_totales]
    trans_casos_totales = [100000 * i / poblacion for i in trans_casos_totales]
    tot_casos_totales = [100000 * i / poblacion for i in tot_casos_totales]
    post_casos_totales = [100000 * i / poblacion for i in post_casos_totales]
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales

    # Plot
    fig, ax = plt.subplots()#figure(3)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    try:
        plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
        plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    except:
        pass
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel(ca + " por 100.000 hab.", **hfont)
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    queue[3] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/4/<sel_comuna>')
def vis4(sel_comuna):
    global queue
    while not queue[3]:
        sleep(0.5)
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        SE_headers(cn, pre_fechas),
        SE_headers(cn, trans_fechas),
        SE_headers(cn, tot_fechas),
        SE_headers(cn, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [SE_to_date(i) for i in dates[0]]
    trans_fechas = [SE_to_date(i) for i in dates[1]]
    tot_fechas = [SE_to_date(i) for i in dates[2]]
    post_fechas = [SE_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, cn, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, cn, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, cn, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, cn, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    pre_casos_totales = [100000 * i / poblacion for i in pre_casos_totales]
    trans_casos_totales = [100000 * i / poblacion for i in trans_casos_totales]
    tot_casos_totales = [100000 * i / poblacion for i in tot_casos_totales]
    post_casos_totales = [100000 * i / poblacion for i in post_casos_totales]
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales

    # Plot
    fig, ax = plt.subplots()#figure(4)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    try:
        plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
        plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    except:
        pass
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel(cn, **hfont)
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    queue[4] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/5/<sel_comuna>')
def vis5(sel_comuna):
    global queue
    while not queue[4]:
        sleep(0.5)
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        SE_headers(cn, pre_fechas),
        SE_headers(cn, trans_fechas),
        SE_headers(cn, tot_fechas),
        SE_headers(cn, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [SE_to_date(i) for i in dates[0]]
    trans_fechas = [SE_to_date(i) for i in dates[1]]
    tot_fechas = [SE_to_date(i) for i in dates[2]]
    post_fechas = [SE_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, cn, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, cn, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, cn, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, cn, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    pre_casos_line = pre_casos_totales + trans_casos_totales
    post_casos_line = tot_casos_totales + post_casos_totales
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales

    # Plot
    fig, ax = plt.subplots()#figure(5)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_fechas, pre_casos_totales, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_fechas, trans_casos_totales, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_fechas, tot_casos_totales, color='green', label='Plena cuarentena')
    plt.scatter(post_fechas, post_casos_totales, color='blue', label='Post cuarentena')
    try:
        plt.plot([pre_fechas_line[0], pre_fechas_line[-1]], [pre_casos_line[0], pre_casos_line[-1]], color='red', linestyle=':')
        plt.plot([post_fechas_line[0], post_fechas_line[-1]], [post_casos_line[0], post_casos_line[-1]], color='blue', linestyle=':')
    except:
        pass
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel(cn + ' por 100.000 hab.', **hfont)
    plt.ylim(0, top=max(casos) + 10)
    plt.xlim(
        left=t0 + timedelta(-1),
        right=max(fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    queue[5] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/6/<sel_comuna>')
def vis6(sel_comuna):
    global queue
    while not queue[5]:
        sleep(0.5)
    csv_to_db()
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    # Fechas importantes a revisar
    dia_inicio = q_comuna['Fecha de Inicio'].split(" ")[0]
    dia_termino = q_comuna['Fecha de Término'].split(" ")[0]
    # Antes de la cuarentena
    pre_fecha_0 = string_to_date(dia_inicio) + timedelta(days=-21)
    pre_fecha_1 = string_to_date(dia_inicio)
    pre_fechas = (pre_fecha_0, pre_fecha_1)
    # Período de transición
    trans_fecha_0 = string_to_date(dia_inicio)
    trans_fecha_1 = string_to_date(dia_inicio) + timedelta(days=14)
    trans_fechas = (trans_fecha_0, trans_fecha_1)
    # Período de plena cuarentena
    tot_fecha_0 = string_to_date(dia_inicio) + timedelta(days=14)
    tot_fecha_1 = string_to_date(dia_termino)
    tot_fechas = (tot_fecha_0, tot_fecha_1)
    # Período de cuarentena efectiva
    post_fecha_0 = string_to_date(dia_termino)
    post_fecha_1 = string_to_date(dia_termino) + timedelta(days=7)
    post_fechas = (post_fecha_0, post_fecha_1)

    dates = [
        date_headers(ct, pre_fechas),
        date_headers(ct, trans_fechas),
        date_headers(ct, tot_fechas),
        date_headers(ct, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
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

    pre_final_fechas = []
    pre_tpo_duplicacion = []
    trans_final_fechas = []
    trans_tpo_duplicacion = []
    tot_final_fechas = []
    tot_tpo_duplicacion = []
    post_final_fechas = []
    post_tpo_duplicacion = []
    min_casos = casos[0]
    for i in range(len(casos)):
        curr_caso = casos[i]
        curr_fecha = fechas[i]
        if min_casos * 2 > curr_caso:
            continue
        for j in range(0, i):
            prev_caso = casos[j]
            prev_fecha = fechas[j]
            if prev_caso * 2 > curr_caso:
                if curr_fecha in pre_fechas:
                    pre_final_fechas.append(curr_fecha)
                    pre_tpo_duplicacion.append((curr_fecha - prev_fecha).days)
                if curr_fecha in trans_fechas:
                    trans_final_fechas.append(curr_fecha)
                    trans_tpo_duplicacion.append((curr_fecha - prev_fecha).days)
                if curr_fecha in tot_fechas:
                    tot_final_fechas.append(curr_fecha)
                    tot_tpo_duplicacion.append((curr_fecha - prev_fecha).days)
                if curr_fecha in post_fechas:
                    post_final_fechas.append(curr_fecha)
                    post_tpo_duplicacion.append((curr_fecha - prev_fecha).days)
                break

    final_fechas = pre_final_fechas + trans_final_fechas + tot_final_fechas + post_final_fechas
    tpo_duplicacion = pre_tpo_duplicacion + trans_tpo_duplicacion + tot_tpo_duplicacion + post_tpo_duplicacion

    # Plot
    fig, ax = plt.subplots()#figure(6)
    plt.clf()
    
    plt.tight_layout()
    plt.gcf().subplots_adjust(bottom=0.15, left=0.15)
    plt.xticks(rotation=15, ha='right')
    ax.tick_params(axis='both', which='major', labelsize=8, grid_color='white')
    ax.set_facecolor('whitesmoke')
    plt.margins(x=0, y=0, tight=True)
    plt.scatter(pre_final_fechas, pre_tpo_duplicacion, color='red', label='Antes de la cuarentena')
    plt.scatter(trans_final_fechas, trans_tpo_duplicacion, color='orange', label='Principios de la cuarentena')
    plt.scatter(tot_final_fechas, tot_tpo_duplicacion, color='green', label='Plena cuarentena')
    plt.scatter(post_final_fechas, post_tpo_duplicacion, color='blue', label='Post cuarentena')
    hfont = {'fontname':'Microsoft Yi Baiti'}
    plt.xlabel('Fecha', **hfont)
    plt.ylabel('Tiempo de duplicación (días)', **hfont)
    plt.ylim(0, top=max(tpo_duplicacion) + 10)
    plt.xlim(
        left=final_fechas[0] + timedelta(-1),
        right=max(final_fechas) + timedelta(1))
    font = font_manager.FontProperties(
        family='Microsoft Yi Baiti'
    )
    plt.legend(prop=font)
    img = BytesIO()
    fig.savefig(img, dpi=120)
    img.seek(0)
    queue[6] = True
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
        return render_template(
            'analizar_comuna.html',
            name=None,
            error="La comuna ingresada no existe en la base de datos."
        )

    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, select)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    # Descripción de la cuarentena
    alcance = q_comuna['Alcance']
    descripcion = q_comuna['Detalle']
    dia_inicio, dia_termino, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [
        date_headers(ct, pre_fechas),
        date_headers(ct, trans_fechas),
        date_headers(ct, tot_fechas),
        date_headers(ct, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas
    if len(pre_fechas_line) == 0 or len(post_fechas_line) == 0:
        return render_template('analizar_comuna.html', name=None, error="No hay suficientes datos para analizar esta comuna.")
    if len(pre_fechas_line) == 1:
        text_0 = """No hay suficientes datos previos a la cuarentena para analizar la evolución de esta variable. 
        Observe el gráfico para más detalles."""
        text_1 = text_0
    elif len(post_fechas_line) == 1:
        text_0 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable. Observe el gráfico para más detalles."""
        text_1 = text_0
    else:
        base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
        pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
        trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
        tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
        post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
        pre_casos_line = pre_casos_totales + trans_casos_totales
        post_casos_line = tot_casos_totales + post_casos_totales
        pre_x = [pre_fechas_line[0], pre_fechas_line[-1]]
        pre_y = [pre_casos_line[0], pre_casos_line[-1]]
        post_x = [post_fechas_line[0], post_fechas_line[-1]]
        post_y = [post_casos_line[0], post_casos_line[-1]]
        text_0 = interpretar_0(pre_x, pre_y, post_x, post_y)
        # Conservamos las pendientes porque son idénticas, por escalamiento
        text_1 = interpretar_1(pre_x, pre_y, post_x, post_y)

    dia_inicio, dia_termino, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)
    dates = [
        date_headers(ca, pre_fechas),
        date_headers(ca, trans_fechas),
        date_headers(ca, tot_fechas),
        date_headers(ca, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas
    if len(pre_fechas_line) == 0 or len(post_fechas_line) == 0:
        print(pre_fechas_line, post_fechas_line)
        text_2 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable."""
        text_3 = text_2
    elif len(post_fechas_line) == 1:
        text_2 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable. Observe el gráfico para más detalles."""
        text_3 = text_2
    else:
        base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
        pre_casos_totales = list(engine.execute(base_query.format(pre_query, ca, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
        trans_casos_totales = list(engine.execute(base_query.format(trans_query, ca, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
        tot_casos_totales = list(engine.execute(base_query.format(tot_query, ca, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
        post_casos_totales = list(engine.execute(base_query.format(post_query, ca, cod_comuna)).fetchone()) if len(post_query) > 3 else []
        pre_casos_line = pre_casos_totales + trans_casos_totales
        post_casos_line = tot_casos_totales + post_casos_totales
        pre_x = [pre_fechas_line[0], pre_fechas_line[-1]]
        pre_y = [pre_casos_line[0], pre_casos_line[-1]]
        post_x = [post_fechas_line[0], post_fechas_line[-1]]
        post_y = [post_casos_line[0], post_casos_line[-1]]
        text_2 = interpretar_2(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line)
        text_3 = interpretar_3(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line)

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)
    dates = [
        SE_headers(cn, pre_fechas),
        SE_headers(cn, trans_fechas),
        SE_headers(cn, tot_fechas),
        SE_headers(cn, post_fechas)
    ]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas = [SE_to_date(i) for i in dates[0]]
    trans_fechas = [SE_to_date(i) for i in dates[1]]
    tot_fechas = [SE_to_date(i) for i in dates[2]]
    post_fechas = [SE_to_date(i) for i in dates[3]]
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    t0 = min(fechas)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    if len(pre_fechas_line) == 0 or len(post_fechas_line) == 0:
        print(pre_fechas_line, post_fechas_line)
        text_4 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable."""
        text_5 = text_2
    elif len(post_fechas_line) == 1:
        text_4 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable. Observe el gráfico para más detalles."""
        text_5 = text_2
    else:
        base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
        pre_casos_totales = list(engine.execute(base_query.format(pre_query, cn, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
        trans_casos_totales = list(engine.execute(base_query.format(trans_query, cn, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
        tot_casos_totales = list(engine.execute(base_query.format(tot_query, cn, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
        post_casos_totales = list(engine.execute(base_query.format(post_query, cn, cod_comuna)).fetchone()) if len(post_query) > 3 else []
        pre_casos_line = pre_casos_totales + trans_casos_totales
        post_casos_line = tot_casos_totales + post_casos_totales
        pre_x = [pre_fechas_line[0], pre_fechas_line[-1]]
        pre_y = [pre_casos_line[0], pre_casos_line[-1]]
        post_x = [post_fechas_line[0], post_fechas_line[-1]]
        post_y = [post_casos_line[0], post_casos_line[-1]]
        text_4 = interpretar_4(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line)
        text_5 = interpretar_5(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line)

    return render_template(
        'analizar_comuna.html',
        name=select,
        poblacion=poblacion,
        dia_inicio="/".join(dia_inicio.split("-")[::-1]),
        dia_termino="/".join(dia_termino.split("-")[::-1]),
        descripcion=descripcion,
        alcance=alcance,
        text_0=text_0,
        text_1=text_1,
        text_2=text_2,
        text_3=text_3,
        text_4=text_4,
        text_5=text_5
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