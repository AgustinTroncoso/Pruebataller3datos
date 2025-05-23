import requests
import time
import pandas as pd
import json
import os

API_KEY = os.getenv("TOKEN")
REGION = "la1"
RIOT_API_URL = f"https://{REGION}.api.riotgames.com"

# --- CONFIGURACIÓN DEL LÍMITE DE PETICIONES ---
MAX_API_CALLS = 1000
api_call_counter = 0

# --- Funciones de ayuda para obtener datos de la API (sin cambios, excepto para el contador) ---
def get_challenger_players(api_key, region):
    global api_call_counter # Indicar que modificaremos la variable global
    url = f"https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={api_key}"
    response = requests.get(url)
    api_call_counter += 1 # Contar esta petición
    response.raise_for_status()
    entries = response.json()['entries']
    top_players = sorted(entries, key=lambda x: x['leaguePoints'], reverse=True)[:50]

    puuids = []
    for player in top_players:
        if api_call_counter >= MAX_API_CALLS:
            print(f"Límite de {MAX_API_CALLS} peticiones alcanzado. Deteniendo la búsqueda de PUUIDs.")
            break
        summoner_id = player['summonerId']
        summoner_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={api_key}"
        s_response = requests.get(summoner_url)
        api_call_counter += 1 # Contar esta petición
        if s_response.status_code == 200:
            puuids.append(s_response.json()['puuid'])
        time.sleep(0.1)
    return puuids

def get_match_ids_by_puuid(puuid, api_key, region_routing="americas", count=100):
    global api_call_counter # Indicar que modificaremos la variable global
    if api_call_counter >= MAX_API_CALLS:
        print(f"Límite de {MAX_API_CALLS} peticiones alcanzado. No se obtendrán más IDs de partidas.")
        return [] # Devolver lista vacía para detener el procesamiento
    url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count={count}&api_key={api_key}"
    response = requests.get(url)
    api_call_counter += 1 # Contar esta petición
    response.raise_for_status()
    return response.json()

def get_match_details(match_id, api_key, region_routing="americas"):
    global api_call_counter # Indicar que modificaremos la variable global
    if api_call_counter >= MAX_API_CALLS:
        print(f"Límite de {MAX_API_CALLS} peticiones alcanzado. No se descargarán más detalles de partidas.")
        return None # Devolver None para indicar que no se obtuvo el detalle
    url = f"https://{region_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    response = requests.get(url)
    api_call_counter += 1 # Contar esta petición
    response.raise_for_status()
    return response.json()

# --- Función para obtener nombres de campeones de Data Dragon (sin cambios, no cuenta para el límite) ---
def get_champion_id_to_name_map():
    versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(versions_url)
    response.raise_for_status()
    latest_version = response.json()[0]

    champions_data_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
    response = requests.get(champions_data_url)
    response.raise_for_status()
    champions_data = response.json()['data']

    champion_id_to_name = {int(champ_data['key']): champ_data['name'] for champ_name, champ_data in champions_data.items()}
    champion_id_to_name[0] = "UNKNOWN_CHAMPION" # Para los 0 de relleno
    return champion_id_to_name

# Cargar el mapa de campeones una vez al inicio
champion_id_to_name_map = get_champion_id_to_name_map()
print("Mapa de IDs de Campeones cargado exitosamente.")

# --- Proceso principal de recopilación de datos (ADAPTADO para el límite) ---
all_match_ids = set()
puuids_to_collect = get_challenger_players(API_KEY, REGION) # get_challenger_players ya tiene su propio control de límite

for puuid in puuids_to_collect:
    if api_call_counter >= MAX_API_CALLS:
        print(f"Límite de {MAX_API_CALLS} peticiones alcanzado. Deteniendo la búsqueda de IDs de partidas por PUUID.")
        break
    print(f"Buscando partidas para PUUID: {puuid}")
    try:
        match_ids = get_match_ids_by_puuid(puuid, API_KEY)
        for mid in match_ids:
            all_match_ids.add(mid)
        time.sleep(1.5)
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener match IDs para {puuid}: {e}")
        time.sleep(5)

print(f"Total de IDs de partidas únicas encontradas: {len(all_match_ids)}")
print(f"Peticiones de API realizadas hasta ahora: {api_call_counter}")

match_data = []
unique_match_ids = list(all_match_ids)
# Solo intentar descargar hasta que el contador alcance el límite
for i, match_id in enumerate(unique_match_ids):
    if api_call_counter >= MAX_API_CALLS:
        print(f"Límite de {MAX_API_CALLS} peticiones alcanzado. Procesando las partidas ya descargadas.")
        break # Salir del bucle de descarga

    print(f"Descargando partida {i+1}/{len(unique_match_ids)}: {match_id}")
    try:
        details = get_match_details(match_id, API_KEY)
        if details: # Asegurarse de que se obtuvieron los detalles (no es None por el límite)
            match_data.append(details)
        time.sleep(1)
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar partida {match_id}: {e}")
        time.sleep(5)

print(f"\nTotal de partidas descargadas: {len(match_data)}")
print(f"Peticiones de API finales: {api_call_counter}")

# Guardar los datos brutos (opcional)
with open('raw_lol_matches_full_champs_with_names_limited.json', 'w') as f:
    json.dump(match_data, f)

# --- Preprocesamiento y Ingeniería de Características (sin cambios, se aplica a 'match_data') ---
processed_data = []

for match in match_data:
    if match['info']['gameDuration'] < 300:
        continue

    team_blue_stats = {
        'teamId': 100,
        'totalGold': 0, 'totalKills': 0, 'totalDamageDealtToChampions': 0,
        'wardsPlaced': 0, 'championPicks': [], 'win': 0
    }
    team_red_stats = {
        'teamId': 200,
        'totalGold': 0, 'totalKills': 0, 'totalDamageDealtToChampions': 0,
        'wardsPlaced': 0, 'championPicks': [], 'win': 0
    }

    for team in match['info']['teams']:
        if team['teamId'] == 100:
            team_blue_stats['win'] = 1 if team['win'] else 0
        elif team['teamId'] == 200:
            team_red_stats['win'] = 1 if team['win'] else 0

    for participant in match['info']['participants']:
        team_id = participant['teamId']
        stats_target = team_blue_stats if team_id == 100 else team_red_stats

        stats_target['totalGold'] += participant['goldEarned']
        stats_target['totalKills'] += participant['kills']
        stats_target['totalDamageDealtToChampions'] += participant['totalDamageDealtToChampions']
        stats_target['wardsPlaced'] += participant['wardsPlaced']
        stats_target['championPicks'].append(participant['championId'])

    first_blood_blue = 0
    for team in match['info']['teams']:
        if team['teamId'] == 100 and team['objectives']['champion']['first']:
            first_blood_blue = 1
            break

    row = {
        'matchId': match['metadata']['matchId'],
        'gameDuration': match['info']['gameDuration'],

        # 7 Características Numéricas
        'diff_gold': team_blue_stats['totalGold'] - team_red_stats['totalGold'],
        'diff_kills': team_blue_stats['totalKills'] - team_red_stats['totalKills'],
        'blue_totalDamageDealtToChampions': team_blue_stats['totalDamageDealtToChampions'],
        'red_totalDamageDealtToChampions': team_red_stats['totalDamageDealtToChampions'],
        'blue_wardsPlaced': team_blue_stats['wardsPlaced'],
        'red_wardsPlaced': team_red_stats['wardsPlaced'],

        # 11 Características Categóricas (NOMBRES de los 5 campeones de cada equipo + firstBlood)
        'blue_champ1_name': champion_id_to_name_map.get(team_blue_stats['championPicks'][0], "UNKNOWN") if len(team_blue_stats['championPicks']) > 0 else "NONE",
        'blue_champ2_name': champion_id_to_name_map.get(team_blue_stats['championPicks'][1], "UNKNOWN") if len(team_blue_stats['championPicks']) > 1 else "NONE",
        'blue_champ3_name': champion_id_to_name_map.get(team_blue_stats['championPicks'][2], "UNKNOWN") if len(team_blue_stats['championPicks']) > 2 else "NONE",
        'blue_champ4_name': champion_id_to_name_map.get(team_blue_stats['championPicks'][3], "UNKNOWN") if len(team_blue_stats['championPicks']) > 3 else "NONE",
        'blue_champ5_name': champion_id_to_name_map.get(team_blue_stats['championPicks'][4], "UNKNOWN") if len(team_blue_stats['championPicks']) > 4 else "NONE",

        'red_champ1_name': champion_id_to_name_map.get(team_red_stats['championPicks'][0], "UNKNOWN") if len(team_red_stats['championPicks']) > 0 else "NONE",
        'red_champ2_name': champion_id_to_name_map.get(team_red_stats['championPicks'][1], "UNKNOWN") if len(team_red_stats['championPicks']) > 1 else "NONE",
        'red_champ3_name': champion_id_to_name_map.get(team_red_stats['championPicks'][2], "UNKNOWN") if len(team_red_stats['championPicks']) > 2 else "NONE",
        'red_champ4_name': champion_id_to_name_map.get(team_red_stats['championPicks'][3], "UNKNOWN") if len(team_red_stats['championPicks']) > 3 else "NONE",
        'red_champ5_name': champion_id_to_name_map.get(team_red_stats['championPicks'][4], "UNKNOWN") if len(team_red_stats['championPicks']) > 4 else "NONE",

        'firstBlood': first_blood_blue,

        'blue_win': team_blue_stats['win']
    }
    processed_data.append(row)

df = pd.DataFrame(processed_data)
print(df.head())
df.to_csv('datos/partidas_lol.csv', index=False)

# --- Verificación de las columnas ---
print(f"\nColumnas en el DataFrame: {df.columns.tolist()}")
print(f"Número de columnas: {len(df.columns)}")

numerical_cols = ['gameDuration', 'diff_gold', 'diff_kills',
                  'blue_totalDamageDealtToChampions', 'red_totalDamageDealtToChampions',
                  'blue_wardsPlaced', 'red_wardsPlaced']

categorical_cols = [
    'blue_champ1_name', 'blue_champ2_name', 'blue_champ3_name', 'blue_champ4_name', 'blue_champ5_name',
    'red_champ1_name', 'red_champ2_name', 'red_champ3_name', 'red_champ4_name', 'red_champ5_name',
    'firstBlood'
]

print(f"\nColumnas numéricas (7): {numerical_cols}")
print(f"Columnas categóricas (11): {categorical_cols}")
print(f"Columna objetivo: 'blue_win'")