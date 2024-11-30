import requests
import xmltodict
import base64
import struct

async def fetch_star_data(quadrant):
    query = f"""
    SELECT TOP 10 ra, dec, parallax 
    FROM gaiadr2.gaia_source 
    WHERE ra BETWEEN {quadrant['raMin']} AND {quadrant['raMax']} 
    AND dec BETWEEN {quadrant['decMin']} AND {quadrant['decMax']}
    """
    url = f"https://gea.esac.esa.int/tap-server/tap/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=votable&QUERY={requests.utils.quote(query)}"
    
    try:
        # Realizar la solicitud
        response = requests.get(url)
        
        # Verificar tipo de contenido
        content_type = response.headers.get('content-type', '')
        if 'xml' not in content_type:
            raise ValueError('Formato de respuesta inesperado')
        
        # Convertir XML a diccionario
        json_data = xmltodict.parse(response.text)
        
        # Navegar por la estructura del XML (similar a JS)
        votable = json_data.get('VOTABLE', {})
        resource = votable.get('RESOURCE', [{}])[0] if isinstance(votable.get('RESOURCE'), list) else votable.get('RESOURCE', {})
        
        if not resource:
            raise ValueError('No se encontró el recurso esperado en el XML')
        
        table = resource.get('TABLE', [{}])[0] if isinstance(resource.get('TABLE'), list) else resource.get('TABLE', {})
        
        if not table:
            raise ValueError('No se encontró la tabla esperada en el XML')
        
        data = table.get('DATA', [{}])[0] if isinstance(table.get('DATA'), list) else table.get('DATA', {})
        
        if not data:
            raise ValueError('No se encontró la sección de datos en el XML')
        
        binary_data = data.get('BINARY2', {}).get('STREAM', '')
        
        if not binary_data:
            raise ValueError('No se encontraron datos binarios en el XML')
        
        # Limpiar datos base64 (quitar espacios)
        base64_data = ''.join(binary_data.split())
        
        # Decodificar buffer
        decoded_buffer = base64.b64decode(base64_data)
        
        # Procesar estrellas
        stars = []
        star_data_length = 12  # 12 bytes por estrella
        
        for i in range(0, len(decoded_buffer), star_data_length):
            ra = struct.unpack_from('<f', decoded_buffer, i)[0]
            dec = struct.unpack_from('<f', decoded_buffer, i + 4)[0]
            parallax = struct.unpack_from('<f', decoded_buffer, i + 8)[0]
            
            stars.append({
                'ra': ra,
                'dec': dec,
                'parallax': parallax
            })
        
        return stars
    
    except Exception as e:
        print(f"Error al procesar los datos: {e}")
        raise

# Nota: Esta versión es asíncrona, así que necesitarás usar `asyncio` para llamarla
import asyncio

async def main():
    quadrant = {
        'raMin': 0, 
        'raMax': 90, 
        'decMin': -45, 
        'decMax': 45
    }
    
    try:
        stars = await fetch_star_data(quadrant)
        print(f"Número de estrellas encontradas: {len(stars)}")
        print("Primeras 5 estrellas:")
        for star in stars[:5]:
            print(star)
    except Exception as e:
        print(f"Error: {e}")

# Para ejecutar en un entorno que soporte async
if __name__ == '__main__':
    asyncio.run(main())