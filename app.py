from flask import Flask, render_template, send_file, request, redirect # Flask app
import jinja2 # Para manejo de estructura de la Flask app
from random import randint, seed # Para test de gráficos random
from datetime import datetime # Para random seed
from time import sleep # Para lock
from datetime import date, datetime, timedelta # Para manejo de fechas, especialmente de headers

# Nombres auxiliares
from nombres_auxiliares import ca, cn, ct, qt, urls, vd
# Funciones auxiliares para procesar BD
from aux_funcs import date_headers, csv_to_db, get_csvs, get_fechas, headers_to_col_query, string_to_date, SE_headers, SE_to_date
from aux_funcs import dbs, engine
# Funciones auxiliares para interpretar datos
from interpretaciones import interpretar_0, interpretar_1, interpretar_2, interpretar_3, interpretar_4, interpretar_5, interpretar_6, interpretar_7, interpretar_8
# Función para plot común que se usa al analizar la efectividad, plot no disponible y random para testing
from common_plot import plot_common_graph, unavailable_plot, random_plot


app = Flask(__name__)
my_loader = jinja2.ChoiceLoader([
    app.jinja_loader
])
app.jinja_loader = my_loader
app.static_folder = 'static'

# Cola que actúa como lock para threads de plots (tienen race conditions en Flask porque paraleliza los llamados)
queue = [False for i in range(9)]


@app.route('/vis/<j>')
def test(j):
    global queue
    j = int(j)
    while not queue[j-1]:
        sleep(0.1)
    img = random_plot(j)
    queue[j] = True
    return send_file(img, mimetype='image/png')

@app.route('/unavailable_data/<i>')
def unavailable(i):
    i = int(i)
    global queue
    while not queue[i-1]:
        sleep(0.1)
    img = unavailable_plot(i)
    queue[i] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/0/<sel_comuna>')
def vis0(sel_comuna):
    global queue
    for i in range(len(queue)):
        queue[i] = False
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [date_headers(ct, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []

    # Plot
    img = plot_common_graph(
        n=0,
        ylabel=ct,
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_casos_totales,
        trans_y=trans_casos_totales,
        tot_y=tot_casos_totales,
        post_y=post_casos_totales
    )
    queue[0] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/1/<sel_comuna>')
def vis1(sel_comuna):
    global queue
    while not queue[0]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [date_headers(ct, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    pre_casos_totales, trans_casos_totales, tot_casos_totales, post_casos_totales = map(lambda x: [100000 * i / poblacion for i in x], [
        pre_casos_totales, trans_casos_totales, tot_casos_totales, post_casos_totales
    ])
    # Plot
    img = plot_common_graph(
        n=1,
        ylabel="Casos confirmados por 100k hab.",
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_casos_totales,
        trans_y=trans_casos_totales,
        tot_y=tot_casos_totales,
        post_y=post_casos_totales
    )
    queue[1] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/2/<sel_comuna>')
def vis2(sel_comuna):
    global queue
    while not queue[1]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [date_headers(ca, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ca, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ca, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ca, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ca, cod_comuna)).fetchone()) if len(post_query) > 3 else []

    # Plot
    img = plot_common_graph(
        n=2,
        ylabel=ca,
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_casos_totales,
        trans_y=trans_casos_totales,
        tot_y=tot_casos_totales,
        post_y=post_casos_totales
    )
    queue[2] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/3/<sel_comuna>')
def vis3(sel_comuna):
    global queue
    while not queue[2]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [date_headers(ca, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ca, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ca, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ca, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ca, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    pre_casos_totales, trans_casos_totales, tot_casos_totales, post_casos_totales = map(lambda x: [100000 * i / poblacion for i in x], [
        pre_casos_totales, trans_casos_totales, tot_casos_totales, post_casos_totales
    ])
    # Plot
    img = plot_common_graph(
        n=3,
        ylabel=ca + " por 100k hab.",
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_casos_totales,
        trans_y=trans_casos_totales,
        tot_y=tot_casos_totales,
        post_y=post_casos_totales
    )
    queue[3] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/4/<sel_comuna>')
def vis4(sel_comuna):
    global queue
    while not queue[3]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [SE_headers(cn, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [SE_to_date(i) for i in dates[x]], range(4))

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, cn, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, cn, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, cn, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, cn, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    # Población de la comuna
    poblacion = engine.execute("SELECT Poblacion from '{}' WHERE `Codigo comuna`='{}'".format(ct, cod_comuna)).fetchone()[0]
    pre_casos_totales, trans_casos_totales, tot_casos_totales, post_casos_totales = map(lambda x: [100000 * i / poblacion for i in x], [
        pre_casos_totales, trans_casos_totales, tot_casos_totales, post_casos_totales
    ])
    # Plot
    img = plot_common_graph(
        n=4,
        ylabel=cn,
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_casos_totales,
        trans_y=trans_casos_totales,
        tot_y=tot_casos_totales,
        post_y=post_casos_totales
    )
    queue[4] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/5/<sel_comuna>')
def vis5(sel_comuna):
    global queue
    while not queue[4]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    dates = [SE_headers(cn, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [SE_to_date(i) for i in dates[x]], range(4))

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, cn, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, cn, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, cn, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, cn, cod_comuna)).fetchone()) if len(post_query) > 3 else []

    # Plot
    img = plot_common_graph(
        n=5,
        ylabel=cn + " por 100k hab.",
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_casos_totales,
        trans_y=trans_casos_totales,
        tot_y=tot_casos_totales,
        post_y=post_casos_totales
    )
    queue[5] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/6/<sel_comuna>')
def vis6(sel_comuna):
    global queue
    while not queue[5]:
        sleep(0.1)
    csv_to_db(dbs)
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

    dates = [date_headers(ct, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas

    base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
    pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
    trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
    tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
    post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
    casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales

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

    # Plot
    if len(pre_tpo_duplicacion + trans_tpo_duplicacion + tot_tpo_duplicacion + post_tpo_duplicacion) == 0:
        return redirect('/unavailable_data/6')
    img = plot_common_graph(
        n=6,
        ylabel="Tiempo de duplicación (días)",
        pre_x=pre_final_fechas,
        trans_x=trans_final_fechas,
        tot_x=tot_final_fechas,
        post_x=post_final_fechas,
        pre_y=pre_tpo_duplicacion,
        trans_y=trans_tpo_duplicacion,
        tot_y=tot_tpo_duplicacion,
        post_y=post_tpo_duplicacion
    )
    queue[6] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/7/<sel_comuna>')
def vis7(sel_comuna):
    global queue
    while not queue[6]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    comunas = engine.execute("SELECT Nombre from '{}' WHERE `Código CUT Comuna`='{}'".format(qt, cod_comuna)).fetchall()
    comunas = tuple([i[0] for i in comunas])

    # Viajes donde la comuna es ORIGEN
    if len(comunas) > 1:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Origen IN {}".format(vd, comunas) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    else:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Origen='{}'".format(vd, comunas[0]) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    viajes = engine.execute(base_query.format(pre_fechas[0], post_fechas[1])).fetchall()
    fechas = [string_to_date(i[0].split(" ")[0]) for i in viajes]
    if len(fechas) < 7:
        return redirect('/unavailable_data/7')
    viajes = [i[1] for i in viajes]
    viajes_suma = [sum(viajes[i-7:i])/7 for i in range(7, len(viajes))]
    fechas = fechas[7:]
    pre_viajes_desde, trans_viajes_desde, tot_viajes_desde, post_viajes_desde = map(lambda x: [
        viajes_suma[i] for i in range(len(fechas)) if fechas[i] >= x[0] and fechas[i] <= x[1]
    ], [pre_fechas, trans_fechas, tot_fechas, post_fechas])
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [
        fechas[i] for i in range(len(fechas)) if fechas[i] >= x[0] and fechas[i] <= x[1]
    ], [pre_fechas, trans_fechas, tot_fechas, post_fechas])

    # Plot
    img = plot_common_graph(
        n=7,
        ylabel=vd + "(Origen, prom. 7 días)",
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_viajes_desde,
        trans_y=trans_viajes_desde,
        tot_y=tot_viajes_desde,
        post_y=post_viajes_desde
    )
    queue[7] = True
    return send_file(img, mimetype='image/png')

@app.route('/vis/8/<sel_comuna>')
def vis8(sel_comuna):
    global queue
    while not queue[7]:
        sleep(0.1)
    csv_to_db(dbs)
    # Datos de la Cuarentena Seleccionada
    q_comuna = engine.execute("SELECT * from '{}' WHERE Nombre='{}';".format(qt, sel_comuna)).fetchone()
    cod_comuna = q_comuna['Código CUT Comuna']

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)

    comunas = engine.execute("SELECT Nombre from '{}' WHERE `Código CUT Comuna`='{}'".format(qt, cod_comuna)).fetchall()
    comunas = tuple([i[0] for i in comunas])

    # Viajes donde la comuna es DESTINO
    if len(comunas) > 1:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Destino IN {}".format(vd, comunas) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    else:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Destino='{}'".format(vd, comunas[0]) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    viajes = engine.execute(base_query.format(pre_fechas[0], post_fechas[1])).fetchall()
    fechas = [string_to_date(i[0].split(" ")[0]) for i in viajes]
    if len(fechas) < 7:
        return redirect('/unavailable_data/8')
    viajes = [i[1] for i in viajes]
    viajes_suma = [sum(viajes[i-7:i])/7 for i in range(7, len(viajes))]
    fechas = fechas[7:]
    pre_viajes_hacia, trans_viajes_hacia, tot_viajes_hacia, post_viajes_hacia = map(lambda x: [
        viajes_suma[i] for i in range(len(fechas)) if fechas[i] >= x[0] and fechas[i] <= x[1]
    ], [pre_fechas, trans_fechas, tot_fechas, post_fechas])
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [
        fechas[i] for i in range(len(fechas)) if fechas[i] >= x[0] and fechas[i] <= x[1]
    ], [pre_fechas, trans_fechas, tot_fechas, post_fechas])

    # Plot
    img = plot_common_graph(
        n=8,
        ylabel=vd + "(Destino, prom. 7 días)",
        pre_x=pre_fechas,
        trans_x=trans_fechas,
        tot_x=tot_fechas,
        post_x=post_fechas,
        pre_y=pre_viajes_hacia,
        trans_y=trans_viajes_hacia,
        tot_y=tot_viajes_hacia,
        post_y=post_viajes_hacia
    )
    queue[8] = True
    return send_file(img, mimetype='image/png')

@app.route('/')
def index():
    csv_to_db(dbs)
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
    csv_to_db(dbs)
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

    # Análisis casos confirmados

    dia_inicio, dia_termino, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)
    dates = [date_headers(ct, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
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
        text_1 = interpretar_1(pre_x, pre_y, post_x, post_y)

    # Análisis casos actuales

    dia_inicio, dia_termino, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)
    dates = [date_headers(ca, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas
    if len(pre_fechas_line) == 0 or len(post_fechas_line) == 0:
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

    # Análisis casos nuevos
    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)
    dates = [SE_headers(cn, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [SE_to_date(i) for i in dates[x]], range(4))
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas

    if len(pre_fechas_line) == 0 or len(post_fechas_line) == 0:
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

    # Análisis tpo duplicación

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

    dates = [date_headers(ct, x, dbs) for x in [pre_fechas, trans_fechas, tot_fechas, post_fechas]]
    pre_query, trans_query, tot_query, post_query = map(headers_to_col_query, dates)
    pre_fechas, trans_fechas, tot_fechas, post_fechas = map(lambda x: [string_to_date(i) for i in x], dates)
    fechas = pre_fechas + trans_fechas + tot_fechas + post_fechas
    pre_fechas_line = pre_fechas + trans_fechas
    post_fechas_line = tot_fechas + post_fechas
    
    if len(pre_fechas_line) == 0 or len(post_fechas_line) == 0:
        text_6 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable."""
    elif len(post_fechas_line) == 1:
        text_6 = """No hay suficientes datos desde la instauración de la cuarentena para analizar la evolución de 
        esta variable. Observe el gráfico para más detalles."""
    else:
        base_query = "SELECT {} from '{}' WHERE `Codigo comuna`='{}'"
        pre_casos_totales = list(engine.execute(base_query.format(pre_query, ct, cod_comuna)).fetchone()) if len(pre_query) > 3 else []
        trans_casos_totales = list(engine.execute(base_query.format(trans_query, ct, cod_comuna)).fetchone()) if len(trans_query) > 3 else []
        tot_casos_totales = list(engine.execute(base_query.format(tot_query, ct, cod_comuna)).fetchone()) if len(tot_query) > 3 else []
        post_casos_totales = list(engine.execute(base_query.format(post_query, ct, cod_comuna)).fetchone()) if len(post_query) > 3 else []
        casos = pre_casos_totales + trans_casos_totales + tot_casos_totales + post_casos_totales

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
        pre_tpo_duplicacion_line = pre_tpo_duplicacion + trans_tpo_duplicacion
        post_tpo_duplicacion_line = tot_tpo_duplicacion + post_tpo_duplicacion
        pre_fechas_line = pre_final_fechas + trans_final_fechas
        post_fechas_line = tot_final_fechas + post_final_fechas
        if len(pre_tpo_duplicacion_line) < 2 or len(post_tpo_duplicacion_line) < 2:
            text_6 = "No existe suficiente información para realizar un análisis acabado (ver gráfico)."
        else:
            pre_x = [pre_fechas_line[0], pre_fechas_line[-1]]
            pre_y = [pre_tpo_duplicacion_line[0], pre_tpo_duplicacion_line[-1]]
            post_x = [post_fechas_line[0], post_fechas_line[-1]]
            post_y = [post_tpo_duplicacion_line[0], post_tpo_duplicacion_line[-1]]
            text_6 = interpretar_6(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line)

    # Análisis viajes

    _, _, pre_fechas, trans_fechas, tot_fechas, post_fechas = get_fechas(q_comuna)
    comunas = engine.execute("SELECT Nombre from '{}' WHERE `Código CUT Comuna`='{}'".format(qt, cod_comuna)).fetchall()
    comunas = tuple([i[0] for i in comunas])    

    # Viajes donde la comuna es ORIGEN
    if len(comunas) > 1:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Origen IN {}".format(vd, comunas) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    else:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Origen='{}'".format(vd, comunas[0]) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    viajes = engine.execute(base_query.format(pre_fechas[0], post_fechas[1])).fetchall()
    fechas = [string_to_date(i[0].split(" ")[0]) for i in viajes]
    if len(fechas) < 7:
        text_7 = "No hay información disponible para esta comuna, posiblemente porque solo está para RM."
    else:
        viajes = [i[1] for i in viajes]
        viajes_suma = [sum(viajes[i-7:i])/7 for i in range(7, len(viajes))]
        fechas = fechas[7:]
        pre_viajes_desde, trans_viajes_desde, tot_viajes_desde, post_viajes_desde = map(lambda x: [
            viajes_suma[i] for i in range(len(fechas)) if fechas[i] >= x[0] and fechas[i] <= x[1]
        ], [pre_fechas, trans_fechas, tot_fechas, post_fechas])
        pre_viajes_line = pre_viajes_desde
        dur_viajes_line = trans_viajes_desde + tot_viajes_desde
        post_viajes_line = post_viajes_desde
        text_7 = interpretar_7(pre_viajes_line, dur_viajes_line, post_viajes_line)

    # Viajes donde la comuna es Destino
    if len(comunas) > 1:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Destino IN {}".format(vd, comunas) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    else:
        base_query = "SELECT Fecha, SUM(Viajes) from '{}' WHERE Destino='{}'".format(vd, comunas[0]) + " AND Fecha >= '{}' AND FECHA <= '{}' GROUP BY Fecha"
    viajes = engine.execute(base_query.format(pre_fechas[0], post_fechas[1])).fetchall()
    fechas = [string_to_date(i[0].split(" ")[0]) for i in viajes]
    if len(fechas) < 7:
        text_8 = "No hay información disponible para esta comuna, posiblemente porque solo está para RM."
    else:
        viajes = [i[1] for i in viajes]
        viajes_suma = [sum(viajes[i-7:i])/7 for i in range(7, len(viajes))]
        fechas = fechas[7:]
        pre_viajes_desde, trans_viajes_desde, tot_viajes_desde, post_viajes_desde = map(lambda x: [
            viajes_suma[i] for i in range(len(fechas)) if fechas[i] >= x[0] and fechas[i] <= x[1]
        ], [pre_fechas, trans_fechas, tot_fechas, post_fechas])
        pre_viajes_line = pre_viajes_desde
        dur_viajes_line = trans_viajes_desde + tot_viajes_desde
        post_viajes_line = post_viajes_desde
        text_8 = interpretar_8(pre_viajes_line, dur_viajes_line, post_viajes_line)


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
        text_5=text_5,
        text_6=text_6,
        text_7=text_7,
        text_8=text_8
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