import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# URL ÚNICA de USA Today con todos los juegos
URL_USATODAY = "https://www.usatoday.com/lottery/us-fl"
ARCHIVO_JSON = "resultados.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def extraer_sorteos():
    sorteos = []
    try:
        session = requests.Session()
        response = session.get(URL_USATODAY, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # USA Today pone los resultados en tablas o contenedores.
        # Buscamos los números que están en las bolitas blancas.
        # (El robot ignorará las bolas rojas del Fireball)
        
        # Aquí buscamos TODOS los números de la página
        todos_los_numeros = []
        for div in soup.find_all(['div', 'span'], class_=True):
            clase = ' '.join(div.get('class')).lower()
            # Buscamos las bolitas blancas (suelen tener clase 'number' o 'ball')
            if ('number' in clase or 'ball' in clase) and 'red' not in clase and 'fireball' not in clase:
                texto = div.get_text(strip=True)
                if texto.isdigit() and len(texto) <= 2:
                    todos_los_numeros.append(texto)

        # Si la página cargó los números, los agrupamos.
        # Normalmente el primer grupo es el Pick 3, el segundo el Pick 4, etc.
        # Vamos a guardar los primeros 3 como Pick 3 y los siguientes 4 como Pick 4.
        
        hoy = datetime.now().strftime("%d-%m-%Y")
        
        if len(todos_los_numeros) >= 3:
            # Guardar Pick 3 (primeros 3 números)
            n1, n2, n3 = todos_los_numeros[0], todos_los_numeros[1], todos_los_numeros[2]
            sorteos.append({"fecha": hoy, "turno": "T", "cent": n1, "fijo": n2 + n3, "c1": "00", "c2": "00"})
            
        if len(todos_los_numeros) >= 7:
            # Guardar Pick 4 (siguientes 4 números, asumiendo que vienen después del Pick 3)
            n1, n2, n3, n4 = todos_los_numeros[3], todos_los_numeros[4], todos_los_numeros[5], todos_los_numeros[6]
            sorteos.append({"fecha": hoy, "turno": "T", "cent": n1, "fijo": n2 + n3, "c1": n4 + "0", "c2": "00"})

    except Exception as e:
        print(f"Error: {e}")
    return sorteos

def main():
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, 'r') as f:
            data = json.load(f)
    else:
        data = {"sorteos": []}
        
    nuevos = extraer_sorteos()
    
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
