import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

ARCHIVO_JSON = "resultados.json"

URLS = {
    "P3_DIA": "https://dominicanaloterias.com/loteria/loteria-de-florida/pick-3-dia",
    "P3_NOCHE": "https://dominicanaloterias.com/loteria/loteria-de-florida/pick-3-noche",
    "P4_DIA": "https://dominicanaloterias.com/loteria/loteria-de-florida/pick-4-dia",
    "P4_NOCHE": "https://dominicanaloterias.com/loteria/loteria-de-florida/pick-4-noche"
}

def extraer_web(url, juego, turno):
    print(f"Buscando en: {url} (Turno: {turno})")
    resultados = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        filas = soup.find_all('tr')
        
        if not filas:
            print(f"ADVERTENCIA: No se encontraron filas en {url}")
            return []
        
        for fila in filas:
            celdas = fila.find_all('td')
            if len(celdas) < 2:
                continue
            
            texto_fecha = celdas[0].get_text(strip=True)
            
            # Extraer los números (vienen en etiquetas <li>)
            lista_numeros = fila.find_all('li')
            numeros = []
            if lista_numeros:
                for li in lista_numeros:
                    # Extrae solo dígitos
                    texto_limpio = re.sub(r'[^0-9]', '', li.get_text(strip=True))
                    if texto_limpio:
                        numeros.append(texto_limpio)
            
            # Procesamos si hay al menos 3 números (Pick 3)
            if len(numeros) >= 3:
                try:
                    # Limpieza de la fecha
                    fecha_limpia = texto_fecha.lower().replace(" de ", " ").replace(".", "")
                    fecha_str = None
                    for fmt in ("%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%d-%m-%Y"):
                        try:
                            fecha_obj = datetime.strptime(fecha_limpia, fmt)
                            fecha_str = fecha_obj.strftime("%d-%m-%Y")
                            break
                        except:
                            continue
                    
                    if not fecha_str:
                        continue

                    # Función auxiliar para limpiar ceros
                    def limpiar_num(n):
                        if n == "00": return "0"
                        return str(int(n))

                    if juego == "P3":
                        # En Pick 3 oficial hay 3 números. 
                        # Si la web trae 4, el último suele ser el Fireball (lo ignoramos)
                        nums_reales = numeros[:3] 
                        
                        resultados.append({
                            "fecha": fecha_str, 
                            "turno": turno, 
                            "cent": limpiar_num(nums_reales[0]), 
                            "fijo": nums_reales[1].zfill(2), 
                            "c1": nums_reales[2].zfill(2), 
                            "c2": "00" # En Pick 3 no hay C2 oficial
                        })
                        
                    elif juego == "P4" and len(numeros) >= 4:
                        # En Pick 4 oficial hay 4 números. Ignoramos el Fireball si viene de 5to.
                        nums_reales = numeros[:4]
                        
                        resultados.append({
                            "fecha": fecha_str, 
                            "turno": turno, 
                            "cent": limpiar_num(nums_reales[0]), 
                            "fijo": nums_reales[1].zfill(2), 
                            "c1": nums_reales[2].zfill(2), 
                            "c2": nums_reales[3].zfill(2)
                        })
                except Exception as e:
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
    nuevos_web.extend(extraer_web(URLS["P3_DIA"], "P3", "T"))
    nuevos_web.extend(extraer_web(URLS["P3_NOCHE"], "P3", "N"))
    nuevos_web.extend(extraer_web(URLS["P4_DIA"], "P4", "T"))
    nuevos_web.extend(extraer_web(URLS["P4_NOCHE"], "P4", "N"))
    
    actualizados = 0
    agregados = 0
    
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
        print(f"Se agregaron {agregados} sorteos y se actualizaron {actualizados}.")
    else:
        print("No se agregaron ni actualizaron sorteos.")

    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Proceso terminado.")

if __name__ == "__main__":
    main()
