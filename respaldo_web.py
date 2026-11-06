import json
import os
import requests
import pandas as pd
from datetime import datetime

ARCHIVO_JSON = "resultados.json"

# NUEVAS URLs de LotteryUSA (Las antiguas daban error 404)
URLS = {
    "P3_TARDE": "https://www.lotteryusa.com/florida/midday-pick-3/",
    "P4_TARDE": "https://www.lotteryusa.com/florida/midday-pick-4/",
    "P3_NOCHE": "https://www.lotteryusa.com/florida/pick-3/",
    "P4_NOCHE": "https://www.lotteryusa.com/florida/pick-4/"
}

def extraer_tabla(url):
    """Extrae la fecha y los números de una tabla de LotteryUSA"""
    print(f"-> Conectando a: {url}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        tablas = pd.read_html(response.text)
        
        for df in tablas:
            df.columns = [str(c).strip() for c in df.columns]
            if 'Date' in df.columns and ('Numbers' in df.columns or 'Winning Numbers' in df.columns):
                df = df.dropna(subset=['Date'])
                if len(df) > 0:
                    # Tomamos la fila más reciente (la primera)
                    row = df.iloc[0]
                    fecha_texto = str(row['Date']).strip()
                    col_nums = 'Numbers' if 'Numbers' in df.columns else 'Winning Numbers'
                    nums = [n for n in str(row[col_nums]).split() if n.isdigit()]
                    
                    try:
                        # Intentamos leer formatos como "Nov 5, 2026" o "Nov 05, 2026"
                        fecha_obj = datetime.strptime(fecha_texto, "%b %d, %Y")
                        fecha_str = fecha_obj.strftime("%d-%m-%Y")
                        print(f"   [OK] Fecha: {fecha_str} | Números: {nums}")
                        return fecha_str, nums
                    except Exception as e:
                        print(f"   [ERROR] No se pudo leer la fecha '{fecha_texto}': {e}")
                        return None, []
        print(f"   [ERROR] No se encontró la tabla con columnas 'Date' y 'Numbers'.")
        return None, []
    except Exception as e:
        print(f"   [ERROR] Al conectar a la URL: {e}")
        return None, []

def main():
    if not os.path.exists(ARCHIVO_JSON):
        data = {"sorteos": []}
    else:
        with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {"sorteos": []}

    # --- PROCESAMOS LA TARDE ---
    print("\n--- PROCESANDO TARDE ---")
    fecha_p3_t, nums_p3_t = extraer_tabla(URLS["P3_TARDE"])
    fecha_p4_t, nums_p4_t = extraer_tabla(URLS["P4_TARDE"])
    
    if fecha_p3_t and nums_p3_t and fecha_p4_t and nums_p4_t:
        if len(nums_p3_t) >= 3 and len(nums_p4_t) >= 4:
            sorteo_t = {
                "fecha": fecha_p3_t,
                "turno": "T",
                "cent": nums_p3_t[0],                # 1º del P3
                "fijo": nums_p3_t[1] + nums_p3_t[2], # 2º + 3º del P3
                "c1": nums_p4_t[0] + nums_p4_t[1],   # 1º + 2º del P4
                "c2": nums_p4_t[2] + nums_p4_t[3]    # 3º + 4º del P4
            }
            print(f"   [GUARDANDO] Sorteo Tarde combinado: {sorteo_t}")
            existe = False
            for i, existente in enumerate(data["sorteos"]):
                if existente["fecha"] == sorteo_t["fecha"] and existente["turno"] == "T":
                    data["sorteos"][i] = sorteo_t
                    existe = True
                    break
            if not existe:
                data["sorteos"].append(sorteo_t)
    else:
        print("   [AVISO] No se pudo procesar la Tarde por falta de datos.")

    # --- PROCESAMOS LA NOCHE ---
    print("\n--- PROCESANDO NOCHE ---")
    fecha_p3_n, nums_p3_n = extraer_tabla(URLS["P3_NOCHE"])
    fecha_p4_n, nums_p4_n = extraer_tabla(URLS["P4_NOCHE"])
    
    if fecha_p3_n and nums_p3_n and fecha_p4_n and nums_p4_n:
        if len(nums_p3_n) >= 3 and len(nums_p4_n) >= 4:
            sorteo_n = {
                "fecha": fecha_p3_n,
                "turno": "N",
                "cent": nums_p3_n[0],                # 1º del P3
                "fijo": nums_p3_n[1] + nums_p3_n[2], # 2º + 3º del P3
                "c1": nums_p4_n[0] + nums_p4_n[1],   # 1º + 2º del P4
                "c2": nums_p4_n[2] + nums_p4_n[3]    # 3º + 4º del P4
            }
            print(f"   [GUARDANDO] Sorteo Noche combinado: {sorteo_n}")
            existe = False
            for i, existente in enumerate(data["sorteos"]):
                if existente["fecha"] == sorteo_n["fecha"] and existente["turno"] == "N":
                    data["sorteos"][i] = sorteo_n
                    existe = True
                    break
            if not existe:
                data["sorteos"].append(sorteo_n)
    else:
        print("   [AVISO] No se pudo procesar la Noche por falta de datos.")

    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("\nProceso terminado.")

if __name__ == "__main__":
    main()
