from flask import Flask, jsonify, request
import requests
import json
import asyncio
from fastmcp import Client

app = Flask(__name__)

OLLAMA_API_URL = "http://10.0.0.0:11434/api/chat" # MODIFICAR
MODELO = 'qwen2.5:3b'

SYS_PROMPT = """Eres un asistente de voz conversacional con acceso a herramientas.

Herramientas disponibles:
- obtener_clima(ciudad): Obtiene el clima actual de una ciudad

Cuando necesites usar una herramienta, responde EXACTAMENTE en este formato:
USE_TOOL: nombre_herramienta
ARGS: {"argumento": "valor"}

Ejemplo:
Si el usuario pregunta "¿Cómo está el clima en Madrid?"
Debes responder:
USE_TOOL: obtener_clima
ARGS: {"ciudad": "Madrid"}

Características importantes:
- Responde de forma concisa y directa (máximo 3-4 oraciones)
- Sé natural y conversacional
- Si no sabes algo, admítelo honestamente
- Responde SIEMPRE en ESPAÑOL
- NO uses tags como <think>, <reasoning> o similares
- Da respuestas directas y claras"""


async def ejecutar_herramienta_mcp_async(nombre_herramienta: str, args: dict):
    """Ejecuta una herramienta del servidor MCP usando el cliente FastMCP"""
    try:
        # Conectar al servidor MCP via HTTP
        async with Client("http://localhost:8000/mcp") as client:
            # Llamar a la herramienta
            result = await client.call_tool(nombre_herramienta, args)
            
            # Extraer el contenido del resultado
            if hasattr(result, 'content'):
                # Si es un objeto con contenido, extraerlo
                if isinstance(result.content, list) and len(result.content) > 0:
                    # Tomar el primer elemento del contenido
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        # Si tiene texto, devolverlo parseado como JSON si es posible
                        try:
                            return json.loads(content.text)
                        except:
                            return content.text
                    return str(content)
                return result.content
            
            # Si no tiene estructura especial, convertir a string
            return str(result)
            
    except Exception as e:
        return {"error": f"Error ejecutando herramienta: {str(e)}"}


def ejecutar_herramienta_mcp(nombre_herramienta: str, args: dict):
    """Wrapper síncrono para ejecutar herramientas MCP"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(ejecutar_herramienta_mcp_async(nombre_herramienta, args))
        return result
    finally:
        loop.close()


def procesar_con_herramientas(prompt: str, historial: list = None):
    """Procesa el prompt y maneja el uso de herramientas si es necesario"""
    
    if historial is None:
        historial = []
    
    # Construir mensajes para Ollama
    mensajes = [{"role": "system", "content": SYS_PROMPT}]
    mensajes.extend(historial)
    mensajes.append({"role": "user", "content": prompt})
    
    # Hacer request a Ollama
    payload = {
        "model": MODELO,
        "messages": mensajes,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        
        respuesta = response.json()['message']['content']
        
        # Verificar si el modelo quiere usar una herramienta
        if "USE_TOOL:" in respuesta:
            # Extraer nombre de herramienta y argumentos
            lines = respuesta.strip().split('\n')
            tool_name = None
            tool_args = {}
            
            for line in lines:
                if line.startswith("USE_TOOL:"):
                    tool_name = line.replace("USE_TOOL:", "").strip()
                elif line.startswith("ARGS:"):
                    args_str = line.replace("ARGS:", "").strip()
                    try:
                        tool_args = json.loads(args_str)
                    except:
                        pass
            
            if tool_name:
                # Ejecutar la herramienta
                resultado = ejecutar_herramienta_mcp(tool_name, tool_args)
                
                # Formatear el resultado para el modelo
                resultado_str = json.dumps(resultado, ensure_ascii=False)
                
                # Agregar al historial
                historial.append({"role": "assistant", "content": respuesta})
                historial.append({
                    "role": "user", 
                    "content": f"Resultado de {tool_name}: {resultado_str}"
                })
                
                # Hacer segunda llamada para que el modelo interprete el resultado
                payload['messages'] = [{"role": "system", "content": SYS_PROMPT}] + historial
                response = requests.post(OLLAMA_API_URL, json=payload)
                response.raise_for_status()
                respuesta_final = response.json()['message']['content']
                
                return respuesta_final
        
        return respuesta
        
    except requests.exceptions.RequestException as e:
        return f"Error de conexión: {e}"


@app.route("/ask-ia", methods=["POST"])
def askIa():
    """Endpoint de chat con soporte para herramientas MCP"""
    try:
        data = request.json
        user_prompt = data.get('prompt')
        historial = data.get('historial', [])
        
        if not user_prompt:
            return jsonify({"error": "No se encontró 'prompt' en el JSON"}), 400
    except:
        return jsonify({"error": "Request inválido, se esperaba JSON"}), 400
    
    respuesta = procesar_con_herramientas(user_prompt, historial)
    

    return jsonify({
        "response": respuesta
        })


@app.route("/health", methods=["GET"])
def health():
    """Endpoint de salud"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)