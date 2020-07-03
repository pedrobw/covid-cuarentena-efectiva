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
# dn = 'Decesos nuevos' # Nota: Disponible desde el 14 de junio

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
# urls[dn] = 'https://raw.githubusercontent.com/MinCiencia/Datos-COVID19/master/output/producto38/CasosFallecidosPorComuna.csv'
# Trazabilidad - Nada por comuna
# Disponibilidad - Nada por comuna
# Otros - Nada por comuna
