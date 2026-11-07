import json
import os
import requests
from datetime import datetime

ARCHIVO_JSON = "resultados.json"
URL_API_FLORIDA = "https://apim-website-prod-eastus.azure-api.net/drawgamesapp/getLatestDrawGames"

def obtener_datos_api():
    print("1. Consultando API Oficial de Florida...")
    headers = {"Accept": "application/json", "x-partner": "web", "User-Agent": "Mozilla/5.0"}
    
    # Diccionarios para guardar los datos
    datos_p3 = {}
    datos_p4 = {}
    
    try:
        res = requests.get(URL_API_FLORIDA, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        
        for game in data:
            name = game.get("GameName", "").upper()
            draw = game.get("DrawType", "").upper()
            
            if draw not in ["EVENING", "EVE", "MIDDAY"]:
                continue
                
            turno = "N" if draw in ["EVENING", "EVE"] else "T"
            fecha_cruda = game.get("DrawDate", "").split(" ")[0]
            try:
                fecha = datetime.strptime(fecha_cruda, "%Y-%m-%d").strftime("%d-%m-%Y")
            except:
                fecha = fecha_cruda
                
            nums = game.get("DrawNumbers", [])
            numeros = [str(n.get("NumberPick")).zfill(2) for n in nums]
            
            # PROCESAR PICK 3
            if name == "PICK 3":
                if len(numeros) >= 3:
                    # Centena = 1ro, Fijo = 2do + 3ro
                    cent = numeros[0]
                    fijo = numeros[1] + numeros[2]
                    datos_p3[f"{fecha}_{turno}"] = {"cent": cent, "fijo": fijo}
                    
            # PROCESAR PICK 4
            elif name == "PICK 4":
                if len(numeros) >= 4:
                    # C1 = 1ro + 2do, C2 = 3ro + 4to
                    c1 = numeros[0] + numeros[1]
                    c2 = numeros[2] + numeros[3]
                    datos_p4[f"{fecha}_{turno}"] = {"c1": c1, "c2": c2}
                    
        print(f"   -> P3 encontrados: {len(datos_p3)}")
        print(f"   -> P4 encontrados: {len(datos_p4)}")
        return datos_p3, datos_p4
    except Exception as e:
        print(f"   -> Error en API: {e}")
        return {}, {}

def main():
    datos_p3_api, datos_p4_api = obtener_datos_api()
    
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

    print("2. Fusionando datos...")
    
    # Juntamos todas las claves que tengamos
    todas_las_claves = set(datos_p3_api.keys()).union(set(datos_p4_api.keys()))
    
    for clave in todas_las_claves:
        if clave in existentes:
            continue
            
        fecha, turno = clave.split("_")
        
        info_p3 = datos_p3_api.get(clave)
        info_p4 = datos_p4_api.get(clave)
        
        # Necesitamos al menos P3 para la Centena y el Fijo
        if info_p3 is not None:
            cent = info_p3["cent"]
            fijo = info_p3["fijo"]
            c1 = info_p4["c1"] if info_p4 else "00"
            c2 = info_p4["c2"] if info_p4 else "00"
            
            nuevo_sorteo = {
                "fecha": fecha,
                "turno": turno,
                "cent": cent,
                "fijo": fijo,
                "c1": c1,
                "c2": c2
            }
            
            data["sorteos"].append(nuevo_sorteo)
            existentes.add(clave)
            agregados += 1
            print(f"   [+] {fecha} {turno} -> Cent: {cent} | Fijo: {fijo} | C1: {c1} | C2: {c2}")

    # Guardar JSON
    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"\nProceso terminado. Se agregaron {agregados} sorteos nuevos al JSON.")

if __name__ == "__main__":
    main()
