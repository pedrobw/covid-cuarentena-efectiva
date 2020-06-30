# Análisis de la efectividad de las cuarentenas en Chile

Este repositorio contiene toda la estructura de una aplicación web en python con microframework de desarrollo web Flask que automatiza el análisis de los datos publicados por el gobierno para estimar la efectividad de las cuarentenas implementadas en Chile en respuesta al COVID-19. Actualmente, el proyecto no ha sido puesto en producción, por lo que es necesario ejecutarlo en local.

## Dependencias

Necesitar tener instalado Python3 con su módulo pip, además de las siguientes librerías:
- Flask: ``python -m pip install Flask``
- Pandas: ``python -m pip install pandas``
- SQLAlchemy: ``python -m  pip install SQLAlchemy``
- Matplotlib: ``python -m pip install matplotlib``
- Numpy: ``python -m pip install numpy``
(dependiendo de tu configuración, puede que necesites usar el comando ``py`` o ``python3`` para acceder a Python3, pero si estás instalando esto, me imagino que sabes de qué hablo).

## Ejecución

Así de simple y ya se puede ejecutar el programa. Para esto hay dos alternativas:
- Modo debug: Desde la consola, en la carpeta de este repositorio, ejecuta ``python app.py``. Esto ejecutará el ``app.run(debug=True)`` que está al final del archivo ``app.py``. En modo debug, sin embargo, hace dos veces las requests iniciales porque se reinicia para hacer stats. Como esto es lo que más demora, puede ser preferible la siguiente alternativa.
- Desde Flask: También desde la consola y en la misma carpeta, ejecuta ``flask run``. Esto detectará automáticamente el archivo ``app.py`` y lo ejecutará igual, pero no en el modo debug.

# Información adicional

El siguiente proyecto fue realizado para el Instituto Milenio Fundamentos de los Datos en el contexto de una postulación laboral. El proyecto autocontiene una descripción de sus propósitos así como también las decisiones de diseño y las fuentes de los datos.
