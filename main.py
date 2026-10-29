# Carga las librerías principales de FastAPI para el manejo de rutas y errores, 
# Pydantic para validación de datos, SQLite para persistencia local, 
# os y dotenv para la gestión segura de variables de entorno, y el cliente oficial de Google GenAI.

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import os
from dotenv import load_dotenv
from google import genai

# Carga las variables definidas en el archivo .env hacia el entorno de ejecución
load_dotenv()

app = FastAPI(title="API Inteligente - Reseñas de Negocio Local", version="1.0.0")

# CONFIGURACIÓN DE LA BASE DE DATOS (SQLITE)
# Define las funciones auxiliares para abrir conexiones a la base de datos local 'reviews.db'
# y asegura la creación automática de la tabla 'reviews' con su estructura base al arrancar.

def get_db_connection():
    conn = sqlite3.connect("reviews.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            comentario TEXT NOT NULL,
            calificacion INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# MODELOS DE VALIDACIÓN DE DATOS (PYDANTIC)
# Establece los esquemas estrictos de entrada y salida para los datos,
# aplicando restricciones como longitudes mínimas en textos y rangos numéricos permitidos (ge, le).

class Review(BaseModel):
    cliente: str = Field(..., min_length=2, description="Nombre del cliente")
    comentario: str = Field(..., min_length=5, description="Texto de la reseña")
    calificacion: int = Field(..., ge=1, le=5, description="Calificación de 1 a 5")

class ReviewDB(Review):
    id: int

# ENDPOINTS DE LAS OPERACIONES CRUD (SQLITE)
# Implementa los cinco métodos HTTP fundamentales para la gestión local de las reseñas:
# 1. POST: Crear nueva reseña.
# 2. GET: Listar todas las reseñas registradas.
# 3. GET por ID: Consultar una reseña específica (con manejo de error 404).
# 4. PUT: Actualizar una reseña existente validando su existencia previa.
# 5. DELETE: Eliminar una reseña por su identificador único.

@app.post("/reviews/", response_model=ReviewDB, status_code=status.HTTP_201_CREATED)
def create_review(review: Review):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (cliente, comentario, calificacion) VALUES (?, ?, ?)",
        (review.cliente, review.comentario, review.calificacion)
    )
    conn.commit()
    review_id = cursor.lastrowid
    conn.close()
    return ReviewDB(id=review_id, **review.model_dump())

@app.get("/reviews/", response_model=List[ReviewDB])
def list_reviews():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/reviews/{review_id}", response_model=ReviewDB)
def get_review(review_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return dict(row)

@app.put("/reviews/{review_id}", response_model=ReviewDB)
def update_review(review_id: int, review_update: Review):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Reseña no encontrada para actualizar")
    
    cursor.execute(
        "UPDATE reviews SET cliente = ?, comentario = ?, calificacion = ? WHERE id = ?",
        (review_update.cliente, review_update.comentario, review_update.calificacion, review_id)
    )
    conn.commit()
    conn.close()
    return ReviewDB(id=review_id, **review_update.model_dump())

@app.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Reseña no encontrada para eliminar")
    
    cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    conn.commit()
    conn.close()
    return None

# ENDPOINT DE ANÁLISIS INTELIGENTE CON GOOGLE GEMINI
# Consulta una reseña específica almacenada en la base de datos, extrae la clave secreta 
# del entorno de manera segura, construye un prompt optimizado (soporta Positivo, Negativo, Neutral o Mixto)
# y procesa la solicitud mediante el cliente de inteligencia artificial, gestionando cualquier posible error.

@app.post("/reviews/{review_id}/analizar", status_code=status.HTTP_200_OK)
def analizar_review_con_ia(review_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Reseña no encontrada para analizar")
    
    review_data = dict(row)
    
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        prompt = (
            f"Analiza la siguiente reseña de un cliente:\n"
            f"Cliente: {review_data['cliente']}\n"
            f"Comentario: {review_data['comentario']}\n"
            f"Calificación: {review_data['calificacion']}/5\n\n"
            f"Devuelve estrictamente el resultado indicando el Sentimiento (Positivo, Neutral, Negativo o Mixto) "
            f"y un breve Resumen de lo que opina el cliente."
        )
        
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt
        )
        
        return {
            "review_id": review_id,
            "analisis_ia": response.text
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la inteligencia artificial: {str(e)}"
        )