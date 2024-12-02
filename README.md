# 🚀 **BackEnd de las estrellas en paralelo con python**
> Este servidor obtiene y procesa datos de estrellas provenientes de la base de datos de Gaia, organizándolos en cuadrantes específicos.

---

## 👥 **Integrantes**  
- **Irving Geyler Cupul Uc**   
- **Ibis Carrillo Araujo**   
- **Edwin Apolonio Martin Ake**  

---

## ✨ **Características**  
- **Paralelización eficiente:** Utiliza el módulo `multiprocessing` para ejecutar consultas en paralelo, aprovechando múltiples núcleos del procesador. Esto mejora el rendimiento al manejar grandes volúmenes de datos astronómicos. 
- **Procesamiento de cuadrantes:** Los datos se dividen en cuadrantes definidos por rangos de ascensión recta (RA) y declinación (Dec). Cada cuadrante se procesa en paralelo o secuencialmente según la configuración.  
- **Consulta a Gaia:** Realiza consultas ADQL a la API de Gaia, procesa las respuestas en formato XML y decodifica datos desde Base64 para obtener coordenadas.
- **Conversión de coordenadas:** Convierte las coordenadas esféricas (RA, Dec, paralaje) en coordenadas cartesianas tridimensionales (x, y, z) para su representación en 3D.

---

## 🛢️ **Servidor**  
- **Configuración de cuadrantes:**  
  Define una lista fija de cuadrantes que sirven como base para distribuir el trabajo en paralelo.
- **Endpoint `/api/stars`:**  
  Devuelve datos de estrellas en formato JSON. Decide si ejecutar consultas de forma secuencial o en paralelo según el número de procesos especificados.  
- **Paralelismo:** Usa `multiprocessing.Pool` para dividir la carga entre procesos. Si hay más procesos que cuadrantes, subdivide estos para maximizar la eficiencia.  
- **Procesamiento:** Cada proceso ejecuta la función `fetch_star_data` para obtener y transformar datos de estrellas en coordenadas cartesianas.

---

## ⚡️ **Speedup**  
![Tabla](/speedup.png)

---

## 🛠️ **Instalación**  
Sigue estos pasos para instalar el proyecto:  

```bash
# Clona este repositorio
git clone https://github.com/Irving-8man/back-python-paralelo  

# Entra en el directorio del proyecto
cd back-python-paralelo  

# Instala las dependencias
pip install Flask Flask-Cors requests

# Correr el servidor
python app.py

# Visualizar datos
localhost/http://localhost:3000/api/stars
