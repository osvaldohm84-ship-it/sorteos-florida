import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta

URL_PICK3 = "https://floridalottery.com/games/draw-games/pick-3"
URL_PICK4 = "https://floridalottery.com/games/draw-games/pick-4"
ARCHIVO_JSON = "resultados.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def obtener_sorteos(url, juego):
    sorteos = []
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscamos los números en las bolitas principales
        numeros_encontrados = []
        for div in soup.find_all(['div', 'span'], class_=True):
            clase = ' '.join(div.get('class'))
            if ('ball' in clase.lower() or 'number' in clase.lower()) and 'fireball' not in clase.lower():
                texto = div.get_text(strip=True)
                if texto.isdigit() and len(texto) <= 2:
                    numeros_encontrados.append(texto)

        if len(numeros_encontrados) >= 3:
            hoy = datetime.now().strftime("%d-%m-%Y")
            
            if juego == "P3":
                n1, n2, n3 = numeros_encontrados[0], numeros_encontrados[1], numeros_encontrados[2]
                sorteos.append({"fecha": hoy, "turno": "T", "cent": n1, "fijo": n2 + n3, "c1": "00", "c2": "00"})
            elif juego == "P4":
                if len(numeros_encontrados) >= 4:
                    n1, n2, n3, n4 = numeros_encontrados[0], numeros_encontrados[1], numeros_encontrados[2], numeros_encontrados[3]
                    sorteos.append({"fecha": hoy, "turno": "T", "cent": n1, "fijo": n2 + n3, "c1": n4 + "0", "c2": "00"})
                    
    except Exception as e:
        print(f"Error procesando {juego}: {e}")
    return sorteos

def main():
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, 'r') as f:
            data = json.load(f)
    else:
        data = {"sorteos": []}
        
    nuevos_p3 = obtener_sorteos(URL_PICK3, "P3")
    nuevos_p4 = obtener_sorteos(URL_PICK4, "P4")
    nuevos = nuevos_p3 + nuevos_p4
    
    for n in nuevos:
        existe = False
        for existente in data["sorteos"]:
            if existente["fecha"] == n["fecha"] and existente["turno"] == n["turno"]:
                existe = True
                break
        if not existe:
            data["sorteos"].append(n)
            print(f"Agregado: {n['fecha']} - {n['turno']} - {n['cent']}{n['fijo']}")
            
    with open(ARCHIVO_JSON, 'w') as f:
        json.dump(data, f, indent=4)
    print("Proceso terminado.")

if __name__ == "__main__":
    main()
