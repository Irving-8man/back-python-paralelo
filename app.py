from flask import Flask, jsonify
from flask_cors import CORS
from multiprocessing import Pool
import base64
import struct
import requests
import xml.etree.ElementTree as ET
import math  # Para trigonometría

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Permite todas las conexiones

# Namespace para el XML
NAMESPACE = {'vo': 'http://www.ivoa.net/xml/VOTable/v1.3'}

# Función para obtener y procesar los datos de un cuadrante
def fetch_star_data(quadrant):
    # Consulta ADQL
    query = f"""
    SELECT TOP 1000 ra, dec, parallax 
    FROM gaiadr2.gaia_source 
    WHERE ra BETWEEN {quadrant['raMin']} AND {quadrant['raMax']} 
    AND dec BETWEEN {quadrant['decMin']} AND {quadrant['decMax']}
    """
    url = f"https://gea.esac.esa.int/tap-server/tap/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=votable&QUERY={requests.utils.quote(query)}"

    # Petición a la API
    response = requests.get(url)

    try:
        # Procesar XML
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()
        
        # Procesar los datos aquí
        stream = root.find(".//vo:STREAM", namespaces=NAMESPACE)
        
        if stream is not None:
            base64_data = stream.text.strip().replace("\n", "")
            decoded_data = base64.b64decode(base64_data)
            
            stars = []
            star_data_length = 12  # 12 bytes por estrella (float32)
            total_length = len(decoded_data)
            
            for i in range(0, total_length, star_data_length):
                chunk = decoded_data[i:i + star_data_length]
                if len(chunk) == star_data_length:
                    # Decodificar 3 float32 (little-endian)
                    ra, dec, parallax = struct.unpack('<fff', chunk)  # Leer como float32
                
                    if any([ra != ra, dec != dec, parallax != parallax]):  # Verificar NaN
                        continue 

                    # Calcular las coordenadas 3D (x, y, z)
                    ra_rad = ra * (math.pi / 180)  
                    dec_rad = dec * (math.pi / 180)
                    distance = 1 / parallax if parallax != 0 else 1e10
                    # Convertir coordenadas esféricas a cartesianas
                    x = distance * math.cos(dec_rad) * math.cos(ra_rad)
                    y = distance * math.cos(dec_rad) * math.sin(ra_rad)
                    z = distance * math.sin(dec_rad)
                    
                    # Solo añadir las coordenadas y el paralaje
                    stars.append({'x': x, 'y': y, 'z': z, 'parallax': parallax})
            return stars
        else:
            return []
    except ET.ParseError:
        return []

# Lista de cuadrantes
quadrants = [
    {'raMin': 0, 'raMax': 90, 'decMin': -90, 'decMax': 0},
    {'raMin': 90, 'raMax': 180, 'decMin': -90, 'decMax': 0},
    {'raMin': 180, 'raMax': 270, 'decMin': -90, 'decMax': 0},
    {'raMin': 270, 'raMax': 360, 'decMin': -90, 'decMax': 0},
    # Agrega más cuadrantes según sea necesario
]

# Función para ejecutar en paralelo
def fetch_all_star_data(quadrants, num_processes=4):
    # Crear un pool de procesos
    with Pool(processes=num_processes) as pool:
        # Ejecutar fetch_star_data en paralelo para cada cuadrante
        results = pool.map(fetch_star_data, quadrants)
    return results

@app.route('/api/stars', methods=['GET'])
def get_stars():
    # Obtener los datos de todas las estrellas en paralelo
    results = fetch_all_star_data(quadrants)
    # Aplanar la lista de resultados
    flattened_results = [item for sublist in results for item in sublist]
    # Devolver los resultados en formato JSON
    return jsonify(flattened_results)

if __name__ == '__main__':
    # Ejecutar la aplicación Flask
    app.run(debug=True, port=3000)