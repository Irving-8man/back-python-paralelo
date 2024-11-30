import base64
import struct
import requests
import xml.etree.ElementTree as ET

# Namespace para el XML
NAMESPACE = {'vo': 'http://www.ivoa.net/xml/VOTable/v1.3'}

# Definición del cuadrante
quadrant = {
    'raMin': 0,
    'raMax': 90,
    'decMin': -45,
    'decMax': 45
}

# Consulta ADQL
query = f"""
SELECT TOP 10 ra, dec, parallax 
FROM gaiadr2.gaia_source 
WHERE ra BETWEEN {quadrant['raMin']} AND {quadrant['raMax']} 
AND dec BETWEEN {quadrant['decMin']} AND {quadrant['decMax']}
"""
url = f"https://gea.esac.esa.int/tap-server/tap/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=votable&QUERY={requests.utils.quote(query)}"

# Petición a la API
response = requests.get(url)

try:
    ET.register_namespace('', 'http://www.ivoa.net/xml/VOTable/v1.3')
    root = ET.fromstring(response.text)
    stream = root.find(".//vo:STREAM", namespaces=NAMESPACE)
    
    if stream is not None:
        base64_data = stream.text.strip().replace("\n", "")
        decoded_data = base64.b64decode(base64_data)
        
        stars = []
        star_data_length = 12  # 12 bytes por estrella (float32)
        
        total_length = len(decoded_data)
        print(f"Total bytes: {total_length}")
        
        for i in range(0, total_length, star_data_length):
            chunk = decoded_data[i:i + star_data_length]
            if len(chunk) == star_data_length:
                # Decodificar 3 float32 (little-endian)
                ra, dec, parallax = struct.unpack('<fff', chunk)  # Leer como float32
                
                # Validación básica
                if not any([ra != ra, dec != dec, parallax != parallax]):  # Evitar NaN
                    stars.append({'ra': ra, 'dec': dec, 'parallax': parallax})
        
        # Imprimir resultados
        for star in stars:
            print(star)
    
    else:
        print("No se encontró elemento STREAM")

except ET.ParseError as e:
    print(f"Error al parsear el XML: {e}")
except Exception as e:
    print(f"Ocurrió un error: {e}")
