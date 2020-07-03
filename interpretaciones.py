from aux_funcs import calcular_pendiente

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

# Confirmados nuevos por 100k hab.
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

# Tiempo de duplicación
def interpretar_6(pre_x, pre_y, post_x, post_y, pre_fechas_line, post_fechas_line):
    t = """Se que el tiempo de duplicación {} desde el inicio de la plenitud de la cuarentena, es decir, 
    el efecto ha sido {}. Además, nótese que el tpo de duplicación final es de {}, cuando el contagio sin 
    retricciones se duplica en aprox. 2 días, y con medidas básicas, en aprox. 6 días.""".format(
        "ha disminuido" if post_y[1] < post_y[0] else "ha aumentado" if post_y[1]> post_y[0] else "se ha mantenido",
        "negativo" if post_y[1] < post_y[0] else "positivo" if post_y[1]> post_y[0] else "neutro",
        post_y[1]
    )
    if len(pre_fechas_line) > 1 and len(post_fechas_line) > 1:
        m_pre = calcular_pendiente(pre_x, pre_y)
        m_post = calcular_pendiente(post_x, post_y)
        if m_post > 0 and m_post < m_pre:
            t += """ Se agrega que desde que la cuarentena es plenamente efectiva, el ritmo de 
            duplicación de los casos ha descendido en un 
            {:.1f}% en su variación promedio.""".format(
                100 * (m_post - m_pre)/m_pre
            )
        elif m_pre < 0 and m_post > 0:
            t += """ Por lo demás, se ha pasado de un ritmo de cambio negativo a uno positivo, lo cual puede ser 
            considerado una mejora considerable."""
        elif m_pre > 0 and m_post > m_pre:
            t += """ Además, desde que la cuarentena es plenamente efectiva, el ritmo de contagio ha decrecido. 
            Más precisamente, ha habido aumento de un {:.1f}% en la variación promedio del tiempo de duplicación.""".format(
                100 * (m_post - m_pre)/m_pre
            )
    return t

def interpretar_7(pre_viajes_line, dur_viajes_line, post_viajes_line):
    if len(pre_viajes_line) > 1:
        s = "se puede observar que existía una tendencia {} antes de iniciar la cuarentena".format(
            "al alza" if pre_viajes_line[0] < pre_viajes_line[1] else "a la baja" if pre_viajes_line[0] > pre_viajes_line[1] else "constante"
        )
    else:
        s = "no se puede conocer la tendencia previa a iniciar la cuarentena"
    if len(dur_viajes_line) > 1:
        r = "Por otra parte, durante la cuarentena, se aprecia una tendencia más bien {}".format(
            "al alza" if dur_viajes_line[0] < dur_viajes_line[1] else "a la baja" if dur_viajes_line[0] > dur_viajes_line[1] else "constante"
        )
    else:
        r = "Los datos son insuficientes para determinar lo ocurrido durante la cuarentena"
    if len(post_viajes_line) > 1:
        v = " Es interesante notar que en este caso la cuarentena fue levantada y que se observa una tendencia posterior {}.".format(
            "al alza" if post_viajes_line[0] < post_viajes_line[1] else "a la baja" if post_viajes_line[0] > post_viajes_line[1] else "constante"
        )
    else:
        v = ""
    if len(pre_viajes_line) > 0 and len(post_viajes_line) > 0:
        x = 100 * (post_viajes_line[-1] - pre_viajes_line[0]) / pre_viajes_line[0]
        w = """ Finalmente, obsérvese que desde el primer registro disponible desde dos semanas antes de la cuarentena hasta el fin de la misma, 
        la circulación ha variado en un {:.1f}%  , lo que es {}.""".format(
            x,
            "altamente positivo" if x < -0.5 else "más bien positivo" if x < -0.2 else "poco relevante" if x < 0 else "considerablemente negativo"
        )
    else:
        w = ""
    t = """Nótese primero con la información disponible, {}. {}.{}{}""".format(s, r, v, w)
    return t

def interpretar_8(pre_viajes_line, dur_viajes_line, post_viajes_line):
    if len(pre_viajes_line) > 1:
        s = "se puede observar que existía una tendencia {} antes de iniciar la cuarentena".format(
            "al alza" if pre_viajes_line[0] < pre_viajes_line[1] else "a la baja" if pre_viajes_line[0] > pre_viajes_line[1] else "constante"
        )
    else:
        s = "no se puede conocer la tendencia previa a iniciar la cuarentena"
    if len(dur_viajes_line) > 1:
        r = "Por otra parte, durante la cuarentena, se aprecia una tendencia más bien {}".format(
            "al alza" if dur_viajes_line[0] < dur_viajes_line[1] else "a la baja" if dur_viajes_line[0] > dur_viajes_line[1] else "constante"
        )
    else:
        r = "Los datos son insuficientes para determinar lo ocurrido durante la cuarentena"
    if len(post_viajes_line) > 1:
        v = " Es interesante notar que en este caso la cuarentena fue levantada y que se observa una tendencia posterior {}.".format(
            "al alza" if post_viajes_line[0] < post_viajes_line[1] else "a la baja" if post_viajes_line[0] > post_viajes_line[1] else "constante"
        )
    else:
        v = ""
    if len(pre_viajes_line) > 0 and len(post_viajes_line) > 0:
        x = 100 * (post_viajes_line[-1] - pre_viajes_line[0]) / pre_viajes_line[0]
        w = """ Finalmente, obsérvese que desde el primer registro disponible desde dos semanas antes de la cuarentena hasta el fin de la misma, 
        la circulación ha variado en un {:.1f}%  , lo que es {}.""".format(
            x,
            "altamente positivo" if x < -0.5 else "más bien positivo" if x < -0.2 else "poco relevante" if x < 0 else "considerablemente negativo"
        )
    else:
        w = ""
    t = """Nótese primero con la información disponible, {}. {}.{}{}""".format(s, r, v, w)
    return t
