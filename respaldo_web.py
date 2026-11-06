import json
import os
import pandas as pd
from datetime import datetime
import requests

ARCHIVO_JSON = "resultados.json"

# URLs para Tarde (Midday) y Noche (Evening)
URL_P3_TARDE = "https://www.lotteryusa.com/florida/pick-3-midday/"
URL_P3_NOCHE = "https://www.lotteryusa.com/florida/pick-3-evening/"
URL_P4_TARDE = "https://www.lotteryusa.com/florida/pick-4-midday/"
URL_P4_NOCHE = "https://www.lotteryusa.com/florida/pick-4-evening/"

def extraer_web(url, juego, turno):
    print(f"Buscando en: {url} (Turno: {turno})")
    resultados = []
    # MÁSCARA DE NAVEGADOR REAL PARA EVITAR BLOQUEOS
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Usamos requests con headers, y le pasamos el texto a pandas
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        tablas = pd.read_html(response.text)
        for df in tablas:
            df.columns = [str(c).strip() for c in df.columns]
            if 'Date' in df.columns and ('Numbers' in df.columns or 'Winning Numbers' in df.columns):
                df = df.dropna(subset=['Date'])
                for _, row in df.iterrows():
                    try:
                        fecha_texto = str(row['Date']).strip()
                        fecha_obj = datetime.strptime(fecha_texto, "%b %d, %Y")
                        fecha_str = fecha_obj.strftime("%d-%m-%Y")
                        
                        col_nums = 'Numbers' if 'Numbers' in df.columns else 'Winning Numbers'
                        nums = [n for n in str(row[col_nums]).split() if n.isdigit()]
                        
                        if len(nums) >= 3:
                            if juego == "P3":
                                resultados.append({
                                    "fecha": fecha_str, 
                                    "turno": turno, 
                                    "cent": nums[0], 
                                    "fijo": nums[1].zfill(2), 
                                    "c1": nums[2].zfill(2), 
                                    "c2": "00"
                                })
                            elif juego == "P4" and len(nums) >= 4:
                                resultados.append({
                                    "fecha": fecha_str, 
                                    "turno": turno, 
                                    "cent": nums[0], 
                                    "fijo": nums[1].zfill(2), 
                                    "c1": nums[2].zfill(2), 
                                    "c2": nums[3].zfill(2)
                                })
                    except:
                        continue
        print(f"Se encontraron {len(resultados)} sorteos en {url}")
        return resultados
    except Exception as e:
        print(f"Error en {url}: {e}")
        return []

def main():
    if not os.path.exists(ARCHIVO_JSON):
        data = {"sorteos": []}
    else:
        with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {"sorteos": []}

    nuevos_web = []
    nuevos_web.extend(extraer_web(URL_P3_TARDE, "P3", "T"))
    nuevos_web.extend(extraer_web(URL_P3_NOCHE, "P3", "N"))
    nuevos_web.extend(extraer_web(URL_P4_TARDE, "P4", "T"))
    nuevos_web.extend(extraer_web(URL_P4_NOCHE, "P4", "N"))
    
    actualizados = 0
    agregados = 0
    
    if len(nuevos_web) == 0:
        print("ADVERTENCIA: No se pudo extraer ningún sorteo de las webs. Puede ser un bloqueo temporal.")
    
    for n in nuevos_web:
        existe = False
        for i, existente in enumerate(data["sorteos"]):
            if existente["fecha"] == n["fecha"] and existente["turno"] == n["turno"]:
                data["sorteos"][i] = n
                actualizados += 1
                existe = True
                break
        if not existe:
            data["sorteos"].append(n)
            agregados += 1
            print(f"Agregado desde web: {n['fecha']} - {n['turno']}")

    if actualizados > 0 or agregados > 0:
        print(f"Se agregaron {agregados} sorteos y se actualizaron {actualizados} con los datos de la web.")
    else:
        print("No se agregaron ni actualizaron sorteos.")

    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Proceso de respaldo terminado.")

if __name__ == "__main__":
    main()
