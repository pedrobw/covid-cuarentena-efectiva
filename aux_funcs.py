# Para manejo de fechas, especialmente de headers
from datetime import date, datetime, timedelta
# Nombres auxiliares
from nombres_auxiliares import ca, ct, cn, qt, urls, vd
# Imports necesarios para trabajar base de datos
from pandas import to_datetime, read_csv # Trabajar con BDs
from sqlalchemy.types import DateTime, Integer # Especificar tipos al transformar BD
from sqlalchemy import create_engine # Para consultas

# Funciones auxiliares para procesar datos

def string_to_date(s):
    '''Convierte una fecha en un datetime'''
    return datetime(*(int(i) for i in s.split('-')))

def SE_to_date(s):
    '''Convierte una semana epidemiológica en una fecha'''
    return datetime(2020, 2, 15) + timedelta(7 * (int(s.split("SE")[1]) - 7))

def date_headers(abbv, from_to_date, dbs):
    return [col for col in dbs[abbv].columns if (
        ('2020-' in col) and ((string_to_date(col) >= from_to_date[0]) and (string_to_date(col) <= from_to_date[1]))
    )]

def SE_headers(abbv, from_to_date, dbs):
    return [col for col in dbs[abbv].columns if (
        ('SE' in col) and ((SE_to_date(col) >= from_to_date[0]) and (SE_to_date(col) <= from_to_date[1]))
    )]

def headers_to_col_query(l):
    return "`{}`".format("`, `".join(l))

def calcular_pendiente(x, y):
    return (y[1] - y[0]) / ((x[1] - x[0]).days + 0.000001)
    
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

def csv_to_db(dbs):
    ''' Se llama en cada vista que necesita requests a la db, parece necesario 
    porque Flask no reconoce la variable como global, a pesar de que en un script 
    independiente funciona sin problemas'''
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

# Engine para queries de SQLite
engine = create_engine('sqlite://', echo=False, connect_args={"check_same_thread": False})
# Datos
dbs = get_csvs()