import json
import os
import requests
from datetime import datetime

ARCHIVO_JSON = "resultados.json"
URL_API_FLORIDA = "https://apim-website-prod-eastus.azure-api.net/drawgamesapp/getLatestDrawGames"

def obtener_datos_api():
    print("1. Consultando API Oficial de Florida...")
    headers = {"Accept": "application/json", "x-partner": "web", "User-Agent": "Mozilla/5.0"}
    
    datos = {}
    
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
            # Convertir a strings de 2 dígitos
            numeros = [str(n.get("NumberPick")).zfill(2) for n in nums]
            
            clave = f"{fecha}_{turno}"
            if clave not in datos:
                datos[clave] = {}

            # PROCESAR PICK 3
            if name == "PICK 3":
                if len(numeros) >= 3:
                    # Centena = 1º, Fijo = 2º + 3º
                    datos[clave]["cent"] = numeros[0]
                    datos[clave]["fijo"] = numeros[1] + numeros[2]
                    
            # PROCESAR PICK 4
            elif name == "PICK 4":
                if len(numeros) >= 4:
                    # C1 = 1º + 2º, C2 = 3º + 4º
                    datos[clave]["c1"] = numeros[0] + numeros[1]
                    datos[clave]["c2"] = numeros[2] + numeros[3]
                    
        print(f"   -> Se encontraron datos para {len(datos)} días/turnos.")
        return datos
    except Exception as e:
        print(f"   -> Error en API: {e}")
        return {}

def main():
    datos_api = obtener_datos_api()
    
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

    print("2. Guardando en JSON...")
    
    for clave, info in datos_api.items():
        if clave in existentes:
            continue
            
        fecha, turno = clave.split("_")
        
        # Solo guardamos si tenemos al menos la centena y el fijo
        if "cent" in info and "fijo" in info:
            nuevo_sorteo = {
                "fecha": fecha,
                "turno": turno,
                "cent": info.get("cent", "0"),
                "fijo": info.get("fijo", "00"),
                "c1": info.get("c1", "00"),
                "c2": info.get("c2", "00")
            }
            
            data["sorteos"].append(nuevo_sorteo)
            existentes.add(clave)
            agregados += 1
            print(f"   [+] {fecha} {turno} -> Cent: {nuevo_sorteo['cent']} | Fijo: {nuevo_sorteo['fijo']} | C1: {nuevo_sorteo['c1']} | C2: {nuevo_sorteo['c2']}")

    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"\nProceso terminado. Se agregaron {agregados} sorteos nuevos al JSON.")

if __name__ == "__main__":
    main()
