import json
import os
import pandas as pd
from datetime import datetime

ARCHIVO_JSON = "resultados.json"
URL_P3 = "https://www.lotteryusa.com/florida/pick-3-evening/"
URL_P4 = "https://www.lotteryusa.com/florida/pick-4-evening/"

def extraer_web(url, juego):
    print(f"Buscando en respaldo: {url}")
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
                                resultados.append({"fecha": fecha_str, "turno": "N", "cent": nums[0], "fijo": nums[1], "c1": nums[2], "c2": "00"})
                            elif juego == "P4" and len(nums) >= 4:
                                resultados.append({"fecha": fecha_str, "turno": "N", "cent": nums[0], "fijo": nums[1], "c1": nums[2], "c2": nums[3]})
                    except:
                        continue
        return resultados
    except Exception as e:
        print(f"Error en {url}: {e}")
        return []

def main():
    if not os.path.exists(ARCHIVO_JSON):
        return

    with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nuevos_web = extraer_web(URL_P3, "P3") + extraer_web(URL_P4, "P4")
    
    actualizados = 0
    for n in nuevos_web:
        existe = False
        for existente in data["sorteos"]:
            if existente["fecha"] == n["fecha"] and existente["turno"] == n["turno"]:
                # Si existe pero tiene 00, lo actualizamos con los datos de la web
                if existente["c1"] == "00" or existente["c2"] == "00":
                    existente["cent"] = n["cent"]
                    existente["fijo"] = n["fijo"]
                    existente["c1"] = n["c1"]
                    existente["c2"] = n["c2"]
                    actualizados += 1
                existe = True
                break
        if not existe:
            data["sorteos"].append(n)
            print(f"Agregado desde web: {n['fecha']} - {n['turno']}")
            
    if actualizados > 0:
        print(f"Se actualizaron {actualizados} sorteos que tenían 00.")

    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Proceso de respaldo terminado.")

if __name__ == "__main__":
    main()
