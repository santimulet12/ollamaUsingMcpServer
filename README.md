# Sistema de Chat con Herramientas MCP

Sistema de asistente conversacional que integra Ollama con herramientas MCP (Model Context Protocol) para obtener información en tiempo real, como el clima de ciudades.

## 📋 Requisitos Previos

- Python 3.8 o superior
- Ollama instalado y ejecutándose
- Modelo Qwen 2.5:3b descargado en Ollama
- Conexión a internet

## 🔧 Instalación

### 1. Clonar o descargar el proyecto

Asegúrate de tener los archivos `MCPServer.py` y `API.py` en el mismo directorio.

### 2. Instalar dependencias

```bash
pip install fastmcp requests flask uvicorn
```

### 3. Configurar Ollama

Asegúrate de que Ollama esté instalado y ejecutándose. Si no lo tienes, instálalo desde [ollama.ai](https://ollama.ai).

Descarga el modelo requerido:

```bash
ollama pull qwen2.5:3b
```

Verifica que Ollama esté corriendo:

```bash
ollama list
```

### 4. Configurar la API

En el archivo `API.py`, modifica la línea 9 con la dirección IP correcta de tu servidor Ollama:

```python
OLLAMA_API_URL = "http://IP_AQUI:11434/api/chat"
```

Si Ollama está en la misma máquina, usa:

```python
OLLAMA_API_URL = "http://localhost:11434/api/chat"
```

## 🚀 Ejecución

### Paso 1: Iniciar el Servidor MCP

En una terminal, ejecuta:

```bash
python MCPServer.py
```

Deberías ver:

```
🚀 Servidor MCP iniciado en http://localhost:8000/mcp
📡 Herramientas disponibles: obtener_clima
```

### Paso 2: Iniciar la API Flask

En otra terminal (dejando el servidor MCP corriendo), ejecuta:

```bash
python API.py
```

La API Flask se iniciará en `http://localhost:5000`

## 📡 Uso de la API

### Endpoint de Chat

**URL:** `POST http://localhost:5000/ask-ia`

**Body (JSON):**

```json
{
  "prompt": "¿Cómo está el clima en Buenos Aires?",
  "historial": []
}
```

**Ejemplo con historial:**

```json
{
  "prompt": "¿Y en Madrid?",
  "historial": [
    {"role": "user", "content": "¿Cómo está el clima en Buenos Aires?"},
    {"role": "assistant", "content": "En Buenos Aires hace 22°C..."}
  ]
}
```

**Respuesta:**

```json
{
  "response": "En Buenos Aires actualmente hay 22°C con cielo despejado. La sensación térmica es de 21°C y hay un 65% de humedad."
}
```

### Endpoint para velificar el estado de la API

**URL:** `GET http://localhost:5000/health`

**Respuesta:**

```json
{
  "status": "ok"
}
```

## 🛠️ Herramientas Disponibles

### obtener_clima

Obtiene información meteorológica actual de cualquier ciudad del mundo.

**Parámetros:**
- `ciudad` (string): Nombre de la ciudad (ej: "Buenos Aires", "Madrid", "New York")

**Información retornada:**
- Temperatura actual y sensación térmica
- Descripción del clima
- Humedad
- Velocidad del viento
- Presión atmosférica
- Visibilidad
- Índice UV

## 🧪 Ejemplos de Uso

### Usando cURL:

```bash
curl -X POST http://localhost:5000/ask-ia \
  -H "Content-Type: application/json" \
  -d '{"prompt": "¿Qué tiempo hace en Mendoza?"}'
```

### Usando Python:

```python
import requests

response = requests.post(
    "http://localhost:5000/ask-ia",
    json={
        "prompt": "¿Cómo está el clima en Londres?",
        "historial": []
    }
)

print(response.json()["response"])
```

## 🐛 Solución de Problemas

### El servidor MCP no inicia

- Verifica que el puerto 8000 no esté en uso
- Asegúrate de tener instalado `uvicorn`: `pip install uvicorn`

### La API Flask no se conecta a Ollama

- Verifica que Ollama esté corriendo: `ollama list`
- Confirma que la URL en `API.py` sea correcta
- Asegúrate de que el modelo `qwen2.5:3b` esté descargado

### Error de conexión al servidor MCP

- Verifica que `MCPServer.py` esté corriendo
- Confirma que esté accesible en `http://localhost:8000/mcp`

### El modelo no usa las herramientas correctamente

- El modelo debe responder en el formato exacto: `USE_TOOL:` y `ARGS:`
- Si no funciona, considera ajustar el `SYS_PROMPT` en `API.py`

## 📝 Notas

- El servidor MCP debe estar corriendo antes de iniciar la API Flask
- El servicio de clima usa `wttr.in`, que es gratuito pero puede tener límites de uso
- Las respuestas están configuradas para ser concisas (3-4 oraciones máximo)
- Todo el sistema está configurado para responder en español
