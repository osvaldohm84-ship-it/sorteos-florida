import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

ARCHIVO_JSON = "resultados.json"

# URLS
URL_API_FLORIDA = "https://apim-website-prod-eastus.azure-api.net/drawgamesapp/getLatestDrawGames"
URL_WEB_DOMINICANA = "https://loteriasdominicanas.com/loteria-de-florida"

def obtener_centena_api():
    """Saca la Centena (y los números del P3) desde la API oficial"""
    print("1. Consultando API Oficial para la Centena...")
    headers = {"Accept": "application/json", "x-partner": "web", "User-Agent": "Mozilla/5.0"}
    centenas = {}
    
    try:
        res = requests.get(URL_API_FLORIDA, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        
        for game in data:
            name = game.get("GameName", "").upper()
            draw = game.get("DrawType", "").upper()
            
            if name == "PICK 3" and draw in ["EVENING", "EVE", "MIDDAY"]:
                turno = "N" if draw in ["EVENING", "EVE"] else "T"
                fecha_cruda = game.get("DrawDate", "").split(" ")[0]
                try:
                    fecha = datetime.strptime(fecha_cruda, "%Y-%m-%d").strftime("%d-%m-%Y")
                except:
                    fecha = fecha_cruda
                
                nums = game.get("DrawNumbers", [])
                if len(nums) >= 1:
                    # Guardamos la centena usando fecha_turno como clave
                    centenas[f"{fecha}_{turno}"] = str(nums[0].get("NumberPick"))
                    
        print(f"   -> Se encontraron {len(centenas)} centenas en la API.")
        return centenas
    except Exception as e:
        print(f"   -> Error en API: {e}")
        return {}

def obtener_resto_web():
    """Saca el Fijo y Corridos desde Loterias Dominicanas"""
    print("2. Consultando Web Dominicana para Fijo y Corridos...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    sorteos_web = {}
    
    try:
        res = requests.get(URL_WEB_DOMINICANA, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscamos los bloques de juegos
        bloques = soup.find_all('div', class_='game-block')
        
        for bloque in bloques:
            try:
                # Extraer título y fecha (esto depende del HTML real, ponemos un try genérico)
                titulo_tag = bloque.find('span')
                fecha_tag = bloque.find('div', class_='session-date')
                
                if not titulo_tag or not fecha_tag: continue
                
                titulo = titulo_tag.get_text(strip=True).upper()
                fecha_texto = fecha_tag.get_text(strip=True)
                
                # Identificar turno y juego
                if "PICK 3" in titulo:
                    turno = "N" if "NOCHE" in titulo else "T"
                    try:
                        fecha = datetime.strptime(fecha_texto, "%d/%m/%Y").strftime("%d-%m-%Y")
                    except:
                        # Si la fecha viene en otro formato (ej. 06-11-2025)
                        fecha = fecha_texto.replace("/", "-")
                    
                    # Buscar números (bolitas)
                    bolitas = bloque.find_all('span', class_='score')
                    if len(bolitas) >= 3:
                        fijo = str(bolitas[0].get_text(strip=True)).zfill(2)
                        c1 = str(bolitas[1].get_text(strip=True)).zfill(2)
                        c2 = str(bolitas[2].get_text(strip=True)).zfill(2)
                        
                        sorteos_web[f"{fecha}_{turno}"] = {
                            "fijo": fijo, "c1": c1, "c2": c2
                        }
            except Exception:
                continue
                
        print(f"   -> Se encontraron {len(sorteos_web)} sorteos en la web.")
        return sorteos_web
    except Exception as e:
        print(f"   -> Error en Web: {e}")
        return {}

def main():
    # 1. Obtener datos de ambas fuentes
    centenas_api = obtener_centena_api()
    datos_web = obtener_resto_web()
    
    # 2. Leer JSON existente
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {"sorteos": []}
    else:
        data = {"sorteos": []}

    existentes = {f"{s['fecha']}_{s['turno']}" for s in data.get("sorteos", [])}
    agregados = 0

    # 3. Fusionar datos
    print("3. Fusionando datos...")
    for clave, info_web in datos_web.items():
        if clave in existentes:
            continue # Ya existe, lo saltamos
            
        # Separar fecha y turno de la clave
        fecha, turno = clave.split("_")
        
        # Si tenemos la centena de la API, la usamos. Si no, ponemos "0" (o podrías usar la del P4)
        centena = centenas_api.get(clave, "0")
        
        nuevo_sorteo = {
            "fecha": fecha,
            "turno": turno,
            "cent": centena,
            "fijo": info_web["fijo"],
            "c1": info_web["c1"],
            "c2": info_web["c2"]
        }
        
        data["sorteos"].append(nuevo_sorteo)
        existentes.add(clave)
        agregados += 1
        print(f"   [+] Agregado: {fecha} {turno} -> Cent: {centena} | Fijo: {info_web['fijo']} | C1: {info_web['c1']} | C2: {info_web['c2']}")

    # 4. Guardar JSON
    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"\nProceso terminado. Se agregaron {agregados} sorteos nuevos al JSON.")

if __name__ == "__main__":
    main()
