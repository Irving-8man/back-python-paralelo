import time
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




def dividir_cuadrantes(cuadrantes, num_procesar):
    # Si hay más procesos que cuadrantes, subdividir
    if num_procesar > len(cuadrantes):
        proporcion = math.ceil(num_procesar / len(cuadrantes))
        sub_cuadrantes = []
        for q in cuadrantes:
            step_ra = (q['raMax'] - q['raMin']) / proporcion
            for i in range(proporcion):
                sub_cuadrantes.append({
                    'raMin': q['raMin'] + step_ra * i,
                    'raMax': q['raMin'] + step_ra * (i + 1),
                    'decMin': q['decMin'],
                    'decMax': q['decMax']
                })
        return sub_cuadrantes
    else:
        # Agrupar cuadrantes para menos procesos
        cuadrantes_agrupados = []
        tamanio_grupo = math.ceil(len(cuadrantes) / num_procesar)
        for i in range(0, len(cuadrantes), tamanio_grupo):
            cuadrante_combinado = cuadrantes[i:i + tamanio_grupo]
            cuadrantes_agrupados.append({
                'raMin': min(q['raMin'] for q in cuadrante_combinado),
                'raMax': max(q['raMax'] for q in cuadrante_combinado),
                'decMin': min(q['decMin'] for q in cuadrante_combinado),
                'decMax': max(q['decMax'] for q in cuadrante_combinado)
            })
        return cuadrantes_agrupados


@app.route('/api/stars')
def get_stars():
    cuadrantesFijo = [
        {'id': 1, 'raMin': 0, 'raMax': 90, 'decMin': -45, 'decMax': 45},
        {'id': 2, 'raMin': 90, 'raMax': 180, 'decMin': -45, 'decMax': 45},
        {'id': 3, 'raMin': 0, 'raMax': 90, 'decMin': -90, 'decMax': -45},
        {'id': 4, 'raMin': 90, 'raMax': 180, 'decMin': -90, 'decMax': -45},
    ]
    ##########secuencial
    # Ejecutar en secuencial, descomenta
    #tiempo_inicio_sec = time.time()
    #estrellas_secuenciales= [fetch_star_data(q) for q in cuadrantesFijo]
    #tiempo_fin_sec = time.time()

    # Tiempo secuencial
    #sec_tiempo = tiempo_fin_sec - tiempo_inicio_sec
    #print(f"Tiempo secuencial: {sec_tiempo:.2f}")
    #return jsonify(estrellas_secuenciales)



    #######Paralello
    numProcesos = 4 #Comienza desde 2 para paralelizar, arriba ya esta el secuencial
    resultadosParalelo = []
    #Ejecutar en paralelo y descomenta

    #Hay menos o igual de procesadores que cuandrantes, que se encargue Pool
    #if(numProcesos <= len(cuadrantesFijo)):
        # Pool de procesos para paralelismo
    #    inicio_paralelo = time.time()
    #    with Pool(processes=numProcesos) as pool:  
    #        resultados= pool.map(fetch_star_data, cuadrantesFijo)
    #        resultadosParalelo = [star for resultado in resultados for star in resultado]
    #    fin_paralelo = time.time()
    #    print(f"Tiempo paralelo en : {fin_paralelo-inicio_paralelo:.2f} con {numProcesos} procesadores")
    #else:
    #    #mas procesos que cuadrantes, a subdividir para aprovechas el proceso creado
    #    inicio_paralelo = time.time()
    #    cuadrantes_subdi = dividir_cuadrantes(cuadrantesFijo, numProcesos)
    #    with Pool(processes=numProcesos) as pool:
    #        resultadosParalelo = pool.map(fetch_star_data, cuadrantes_subdi)
    #    fin_paralelo = time.time()
    #    print(f"Tiempo paralelo en : {fin_paralelo-inicio_paralelo:.2f} con {numProcesos} procesadores")
    #return jsonify(resultadosParalelo)

if __name__ == '__main__':
    app.run(debug=True, port=3000)