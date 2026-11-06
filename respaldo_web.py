import json
import os
import pandas as pd
from datetime import datetime

ARCHIVO_JSON = "resultados.json"

# URLs para Tarde (Midday) y Noche (Evening)
URL_P3_TARDE = "https://www.lotteryusa.com/florida/pick-3-midday/"
URL_P3_NOCHE = "https://www.lotteryusa.com/florida/pick-3-evening/"
URL_P4_TARDE = "https://www.lotteryusa.com/florida/pick-4-midday/"
URL_P4_NOCHE = "https://www.lotteryusa.com/florida/pick-4-evening/"

def extraer_web(url, juego, turno):
    print(f"Buscando en: {url} (Turno: {turno})")
    resultados = []
    try:
        tablas = pd.read_html(url)
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
                                # Centena, Fijo (2 dígitos), C1 (2 dígitos), C2 (00)
                                resultados.append({
                                    "fecha": fecha_str, 
                                    "turno": turno, 
                                    "cent": nums[0], 
                                    "fijo": nums[1].zfill(2), 
                                    "c1": nums[2].zfill(2), 
                                    "c2": "00"
                                })
                            elif juego == "P4" and len(nums) >= 4:
                                # Los 4 números reales
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

    # Recopilamos todos los datos de las 4 URLs
    nuevos_web = []
    nuevos_web.extend(extraer_web(URL_P3_TARDE, "P3", "T"))
    nuevos_web.extend(extraer_web(URL_P3_NOCHE, "P3", "N"))
    nuevos_web.extend(extraer_web(URL_P4_TARDE, "P4", "T"))
    nuevos_web.extend(extraer_web(URL_P4_NOCHE, "P4", "N"))
    
    actualizados = 0
    agregados = 0
    
    for n in nuevos_web:
        existe = False
        for i, existente in enumerate(data["sorteos"]):
            if existente["fecha"] == n["fecha"] and existente["turno"] == n["turno"]:
                # SIEMPRE SOBRESCRIBIMOS CON LOS DATOS DE LA WEB
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

    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Proceso de respaldo terminado.")

if __name__ == "__main__":
    main()
