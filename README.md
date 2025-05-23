# taller-3-ing-datos

Desarrollo del taller 3 de Ingenieria de Datos con datos extraidos desde la api de Riot Games especificamente del juego League of Legends, para determinar el desenlace de la partida en la victoria para el equipo azul o rojo en base de datos determinantes para la misma como la diferencia de oro obtenido, diferencia de muertes, campeones utilizados entre otros datos, relevantes en el flujo del juego.

## Creacion de entorno e instalacion de dependencias

1. Crear entorno virtual python:

```
python -m venv .venv
```

O

```
py -m venv .venv
```

2. Activar entorno virtual:

```
.\.venv\Scripts\Activate
```

3. Instalar dependencias:

```
pip install -r requirements.txt
```

## CREACIÓN ARCHIVO .env

En la raíz del proyecto se debe crear el archivo .env, luego dentro del archivo se debe agregar lo siguiente:
```
TOKEN=[aqui va tu token]
```

y reemplazas el "[aqui va tu token]" contenido por tu token personal.

## Obtencion de la API KEY de Riot Games
Para obtener la API KEY para el funcionamiento de la app de extracción de datos, primero se debe ingresar al portal de desarrolladores

[Riot Developer Portal](https://developer.riotgames.com/)

Luego se inicia sesion con una cuenta de riot games **si es que cuenta con una**, de no ser el caso debe crear una cuenta de riot games para generar la KEY.

Una vez iniciada la sesion en el portal de desarrolladores se debe hacer clic en el boton **I UNDERSTAND** hasta llegar al boton que diga **CREATE ACCOUNT**, despues de hacer clic en el boton, bajamos y buscamos el captcha y la opcion que diga **REGENERATE API KEY**, hacemos ambas y se generara la KEY, lo copiamos y lo agregamos al archivo *.env* en con el nombre TOKEN, **como se muestra en la seccion anterior** .