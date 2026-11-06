import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

ARCHIVO_JSON = "resultados.json"

# URLs de dominicanaloterias.com
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
        
        # Buscamos la tabla histórica
        filas = soup.find_all('tr')
        
        if not filas:
            print(f"ADVERTENCIA: No se encontraron filas en {url}")
            return []
        
        for fila in filas:
            celdas = fila.find_all('td')
            if len(celdas) < 2:
                continue
            
            # La primera celda tiene la fecha
            texto_fecha = celdas[0].get_text(strip=True)
            
            # Buscar los números (pueden estar en <li> o en <span>)
            # En la web de dominicanaloterias, los números están en una lista <ul><li>...</li></ul>
            lista_numeros = fila.find_all('li')
            
            numeros = []
            if lista_numeros:
                for li in lista_numeros:
                    # Limpiamos el texto, quitando guiones, comas, etc.
                    texto_limpio = re.sub(r'[^0-9]', '', li.get_text(strip=True))
                    if texto_limpio:
                        numeros.append(texto_limpio)
            else:
                # Si no hay <li>, intentamos buscar en celdas (por si acaso)
                for celda in celdas[1:]:
                    texto_limpio = re.sub(r'[^0-9]', '', celda.get_text(strip=True))
                    if texto_limpio:
                        numeros.append(texto_limpio)
            
            # Si encontramos al menos 3 números, procesamos la fila
            if len(numeros) >= 3:
                try:
                    fecha_str = None
                    # Formato típico: "04 de nov 2026" o "04 de noviembre 2026"
                    # Limpiamos el texto para que sea "04 nov 2026"
                    fecha_limpia = texto_fecha.lower().replace(" de ", " ").replace(".", "")
                    
                    # Intentamos parsear la fecha
                    for fmt in ("%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%d-%m-%Y"):
                        try:
                            fecha_obj = datetime.strptime(fecha_limpia, fmt)
                            fecha_str = fecha_obj.strftime("%d-%m-%Y")
                            break
                        except:
                            continue
                    
                    if not fecha_str:
                        continue
                    
                    if juego == "P3":
                        resultados.append({
                            "fecha": fecha_str, 
                            "turno": turno, 
                            "cent": numeros[0], 
                            "fijo": numeros[1].zfill(2), 
                            "c1": numeros[2].zfill(2), 
                            "c2": numeros[3].zfill(2) if len(numeros) > 3 else "00"
                        })
                    elif juego == "P4" and len(numeros) >= 4:
                        resultados.append({
                            "fecha": fecha_str, 
                            "turno": turno, 
                            "cent": numeros[0], 
                            "fijo": numeros[1].zfill(2), 
                            "c1": numeros[2].zfill(2), 
                            "c2": numeros[3].zfill(2)
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
