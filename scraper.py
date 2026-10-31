import json
import os
import re

ARCHIVO_JSON = "resultados.json"

def leer_archivo(nombre_archivo):
    if not os.path.exists(nombre_archivo):
        return []
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        return f.readlines()

def procesar_lineas(lineas, juego):
    sorteos = []
    fecha_actual = ""
    turno_actual = ""
    
    for linea in lineas:
        linea = linea.strip()
        
        # Detectar la fecha
        match_fecha = re.search(r'Draw Date:\s*(\d{2}/\d{2}/\d{4})', linea)
        if match_fecha:
            fecha_raw = match_fecha.group(1)
            dia, mes, anio = fecha_raw.split('/')
            fecha_actual = f"{dia}-{mes}-{anio}"
            
        # Detectar el turno (Midday = T, Evening = N)
        if "MIDDAY" in linea:
            turno_actual = "T"
        elif "EVENING" in linea:
            turno_actual = "N"
            
        # Detectar los números
        match_numeros = re.search(r'Numbers:\s*\[\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?\s*\]', linea)
        if match_numeros and fecha_actual and turno_actual:
            if juego == "P3":
                n1 = match_numeros.group(1)
                n2 = match_numeros.group(2)
                n3 = match_numeros.group(3)
                # Formato App: cent=n1, fijo=n2+n3, c1=00, c2=00
                sorteos.append({
                    "fecha": fecha_actual, 
                    "turno": turno_actual, 
                    "cent": n1, 
                    "fijo": n2 + n3, 
                    "c1": "00", 
                    "c2": "00"
                })
            elif juego == "P4":
                n1 = match_numeros.group(1)
                n2 = match_numeros.group(2)
                n3 = match_numeros.group(3)
                n4 = match_numeros.group(4)
                # Formato App: cent=n1, fijo=n2+n3, c1=n4+0, c2=00
                if n4:
                    sorteos.append({
                        "fecha": fecha_actual, 
                        "turno": turno_actual, 
                        "cent": n1, 
                        "fijo": n2 + n3, 
                        "c1": n4 + "0", 
                        "c2": "00"
                    })
    return sorteos

def main():
    # Leer el JSON existente o crear uno nuevo
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = {"sorteos": []}
    else:
        data = {"sorteos": []}
        
    # Leer los archivos que generó la herramienta
    lineas_p3 = leer_archivo("p3_output.txt")
    lineas_p4 = leer_archivo("p4_output.txt")
    
    # Procesar los sorteos
    nuevos_p3 = procesar_lineas(lineas_p3, "P3")
    nuevos_p4 = procesar_lineas(lineas_p4, "P4")
    nuevos = nuevos_p3 + nuevos_p4
    
    # Lógica anti-duplicados
    for n in nuevos:
        existe = False
        for existente in data["sorteos"]:
            if existente["fecha"] == n["fecha"] and existente["turno"] == n["turno"]:
                existe = True
                break
        if not existe:
            data["sorteos"].append(n)
            print(f"Agregado: {n['fecha']} - {n['turno']} - {n['cent']}{n['fijo']}")
        else:
            print(f"Ya existe: {n['fecha']} - {n['turno']}")
            
    # Guardar en el JSON
    with open(ARCHIVO_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Proceso terminado con éxito.")

if __name__ == "__main__":
    main()
