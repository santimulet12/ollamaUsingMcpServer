from fastmcp import FastMCP
import requests
import uvicorn

# Crear instancia del servidor MCP
mcp = FastMCP("Mi Servidor MCP")

# === HERRAMIENTAS (TOOLS) ===

@mcp.tool()
def obtener_clima(ciudad: str) -> dict:
    """
    Obtiene el clima actual de una ciudad especificada
    
    Args:
        ciudad: Nombre de la ciudad (ej: "Buenos Aires", "Madrid", "New York")
    """
    
    try:
        # Usar wttr.in, un servicio gratuito de clima
        url = f"https://wttr.in/{ciudad}?format=j1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer información relevante
            current = data['current_condition'][0]
            location = data['nearest_area'][0]
            
            return {
                "ciudad": location['areaName'][0]['value'],
                "pais": location['country'][0]['value'],
                "temperatura_c": current['temp_C'],
                "sensacion_termica_c": current['FeelsLikeC'],
                "descripcion": current['weatherDesc'][0]['value'],
                "humedad": current['humidity'],
                "velocidad_viento": current['windspeedKmph'],
                "presion_mb": current['pressure'],
                "visibilidad_km": current['visibility'],
                "uv_index": current['uvIndex']
            }
        else:
            return {"error": f"No se pudo obtener el clima de {ciudad}"}
            
    except requests.exceptions.Timeout:
        return {"error": "Tiempo de espera agotado al consultar el clima"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error de conexión: {str(e)}"}
    except Exception as e:
        return {"error": f"Error al obtener clima: {str(e)}"}


# Configurar para usar HTTP transport (Streamable HTTP)
# El cliente se conectará a http://localhost:8000/mcp
mcp.settings.streamable_http_path = "/mcp"

# Obtener la aplicación ASGI
mcp_app = mcp.streamable_http_app()

# Iniciar el servidor
if __name__ == "__main__":
    print("🚀 Servidor MCP iniciado en http://localhost:8000/mcp")
    print("📡 Herramientas disponibles: obtener_clima")
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)