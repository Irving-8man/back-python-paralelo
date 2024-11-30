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
        ET.register_namespace('', 'http://www.ivoa.net/xml/VOTable/v1.3')
        root = ET.fromstring(response.text)
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
    
    except ET.ParseError as e:
        print(f"Error al parsear el XML: {e}")
        return []
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return []
    


@app.route('/api/stars')
def get_stars():
    quadrants = [
        {'id': 1, 'raMin': 0, 'raMax': 90, 'decMin': -45, 'decMax': 45},
        {'id': 2, 'raMin': 90, 'raMax': 180, 'decMin': -45, 'decMax': 45},
        {'id': 3, 'raMin': 0, 'raMax': 90, 'decMin': -90, 'decMax': -45},
        {'id': 4, 'raMin': 90, 'raMax': 180, 'decMin': -90, 'decMax': -45},
    ]
    
    # Pool de procesos para paralelismo
    with Pool(processes=4) as pool:  
        results = pool.map(fetch_star_data, quadrants)
    # Resultados en una sola lista
    all_stars = [star for result in results for star in result]
    return jsonify(all_stars)

if __name__ == '__main__':
    app.run(debug=True, port=3000)