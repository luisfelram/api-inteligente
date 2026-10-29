API Inteligente - Reseñas de Negocio Local:

API desarrollada con FastAPI, Pydantic, SQLite y la integración de Google GenAI (Gemini) en una arquitectura de archivo único (`main.py`) para facilitar su mantenimiento.

Características:
- CRUD Completo: Gestión de reseñas locales (Crear, Listar, Obtener por ID, Actualizar y Eliminar).
- Validación de Datos: Uso de Pydantic con restricciones (`min_length`, rangos numéricos `ge`, `le`).
- Persistencia Local: Almacenamiento integrado con SQLite (`reviews.db`).
- Inteligencia Artificial: Endpoint especializado (`/reviews/{review_id}/analizar`) impulsado por Gemini para evaluar el sentimiento y extraer información clave de las reseñas.

Requisitos e Instalación

1. Descargar el repositorio.
2. Instalar las siguientes dependencias requeridas:
   ```bash
   pip install fastapi uvicorn google-genai python-dotenv
3. Configurar las variables de entorno:
   - Copiar o duplicar el archivo `.env.example` y nombrarlo `.env`.
   - Agregar tu clave de la API de Gemini dentro del `.env`:
     GEMINI_API_KEY=tu_clave_real_aqui

Ejecución de la Aplicación:

uvicorn main:app --reload

Acceder a la documentación interactiva en el navegador:
http://127.0.0.1:8000/docs