import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

ARCHIVO_JSON = "resultados.json"

URL_API_FLORIDA = "https://apim-website-prod-eastus.azure-api.net/drawgamesapp/getLatestDrawGames"
URL_WEB_DOMINICANA = "https://loteriasdominicanas.com/loteria-de-florida"

def obtener_centena_api():
    """Saca la Centena (1er número) desde la API oficial"""
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
                    centenas[f"{fecha}_{turno}"] = str(nums[0].get("NumberPick"))
                    
        print(f"   -> Se encontraron {len(centenas)} centenas en la API.")
        return centenas
    except Exception as e:
        print(f"   -> Error en API: {e}")
        return {}

def obtener_datos_web():
    """Saca los números del P3 (Fijo) y P4 (Corridos) desde la web"""
    print("2. Consultando Web Dominicana para Fijo y Corridos...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Diccionarios separados para P3 y P4
    datos_p3 = {}
    datos_p4 = {}
    
    try:
        res = requests.get(URL_WEB_DOMINICANA, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        bloques = soup.find_all('div', class_='game-block')
        
        for bloque in bloques:
            try:
                titulo_tag = bloque.find('span')
                fecha_tag = bloque.find('div', class_='session-date')
                
                if not titulo_tag or not fecha_tag: continue
                
                titulo = titulo_tag.get_text(strip=True).upper()
                fecha_texto = fecha_tag.get_text(strip=True)
                
                # Normalizar fecha a DD-MM-YYYY
                try:
                    fecha = datetime.strptime(fecha_texto, "%d/%m/%Y").strftime("%d-%m-%Y")
                except:
                    fecha = fecha_texto.replace("/", "-")
                    
                # Extraer las bolitas de números (ignorando el Fireball)
                bolitas = bloque.find_all('span', class_='score')
                numeros = []
                for b in bolitas:
                    texto = b.get_text(strip=True)
                    if texto.isdigit():
                        numeros.append(texto)
                
                # Procesar PICK 3
                if "PICK 3" in titulo:
                    turno = "N" if "NOCHE" in titulo else "T"
                    if len(numeros) >= 3:
                        # Regla: Fijo = 2do + 3er número
                        fijo = numeros[1].zfill(2) + numeros[2].zfill(2)
                        datos_p3[f"{fecha}_{turno}"] = {"fijo": fijo}
                
                # Procesar PICK 4
                elif "PICK 4" in titulo:
                    turno = "N" if "NOCHE" in titulo else "T"
                    if len(numeros) >= 4:
                        # Regla: C1 = 1ro + 2do, C2 = 3ro + 4to
                        c1 = numeros[0].zfill(2) + numeros[1].zfill(2)
                        c2 = numeros[2].zfill(2) + numeros[3].zfill(2)
                        datos_p4[f"{fecha}_{turno}"] = {"c1": c1, "c2": c2}
                        
            except Exception as e:
                continue
                
        print(f"   -> P3 encontrados en web: {len(datos_p3)}")
        print(f"   -> P4 encontrados en web: {len(datos_p4)}")
        return datos_p3, datos_p4
    except Exception as e:
        print(f"   -> Error en Web: {e}")
        return {}, {}

def main():
    centenas_api = obtener_centena_api()
    datos_p3_web, datos_p4_web = obtener_datos_web()
    
    # Leer JSON existente
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

    print("3. Fusionando datos...")
    
    # Juntamos todas las claves (fechas_turnos) que tengamos en la web
    todas_las_claves = set(datos_p3_web.keys()).union(set(datos_p4_web.keys()))
    
    for clave in todas_las_claves:
        if clave in existentes:
            continue # Ya existe, lo saltamos
            
        fecha, turno = clave.split("_")
        
        # Buscar datos en cada fuente
        centena = centenas_api.get(clave)
        info_p3 = datos_p3_web.get(clave)
        info_p4 = datos_p4_web.get(clave)
        
        # Validar que tengamos lo mínimo necesario (Centena y Fijo al menos)
        if centena is not None and info_p3 is not None:
            
            fijo = info_p3["fijo"]
            c1 = info_p4["c1"] if info_p4 else "00"
            c2 = info_p4["c2"] if info_p4 else "00"
            
            nuevo_sorteo = {
                "fecha": fecha,
                "turno": turno,
                "cent": centena,
                "fijo": fijo,
                "c1": c1,
                "c2": c2
            }
            
            data["sorteos"].append(nuevo_sorteo)
            existentes.add(clave)
            agregados += 1
            print(f"   [+] {fecha} {turno} -> Cent: {centena} | Fijo: {fijo} | C1: {c1} | C2: {c2}")
        else:
            print(f"   [-] {fecha} {turno} -> Faltan datos (API: {centena is not None}, P3: {info_p3 is not None})")

    # Guardar JSON
    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"\nProceso terminado. Se agregaron {agregados} sorteos nuevos al JSON.")

if __name__ == "__main__":
    main()
