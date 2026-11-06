import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

ARCHIVO_JSON = "resultados.json"

# URLs de dominicanaloterias.com (según búsqueda, tienen los números)
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
        
        # ESTRATEGIA GENÉRICA: Buscamos todas las filas de tabla
        # Si no funciona, tendrás que decirme la clase exacta
        filas = soup.find_all('tr')
        
        if not filas:
            print(f"ADVERTENCIA: No se encontraron filas <tr> en {url}")
            return []
        
        for fila in filas:
            celdas = fila.find_all('td')
            if len(celdas) < 2:
                continue
            
            # Intentamos extraer la fecha de la primera celda
            texto_fecha = celdas[0].get_text(strip=True)
            
            # Intentamos extraer los números de las siguientes celdas
            numeros = []
            for celda in celdas[1:]:
                texto = celda.get_text(strip=True)
                # Buscamos dígitos o grupos de dígitos
                if texto.isdigit():
                    numeros.append(texto)
            
            if len(numeros) >= 3:
                try:
                    # Intentar parsear la fecha (puede venir como "23 de oct 2026" o "23/10/2026")
                    # Esto es un intento; si falla, se salta la fila
                    fecha_str = None
                    for fmt in ("%d de %b %Y", "%d/%m/%Y", "%d-%m-%Y"):
                        try:
                            fecha_obj = datetime.strptime(texto_fecha, fmt)
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
                            "c2": "00"
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
