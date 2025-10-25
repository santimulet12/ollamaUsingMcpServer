# Documentación del Sistema MCP con Ollama

## Descripción General

Este proyecto implementa un sistema de asistente conversacional que combina:
- Un servidor MCP (Model Context Protocol) para exponer herramientas
- Una API Flask que integra Ollama con el servidor MCP
- Capacidad de ejecutar herramientas externas de forma transparente

---

## MCPServer.py

### Propósito
Implementa un servidor MCP usando FastMCP que expone herramientas (tools) accesibles vía HTTP. Este servidor actúa como un proveedor de funcionalidades que pueden ser consumidas por otros servicios.

### Componentes Principales

#### Inicialización
```python
mcp = FastMCP("Mi Servidor MCP")
```
Crea una instancia del servidor MCP con un nombre identificador.

#### Herramienta: `obtener_clima`

**Función:** Consulta el clima actual de cualquier ciudad del mundo.

**Parámetros:**
- `ciudad` (str): Nombre de la ciudad a consultar

**Retorna:**
Un diccionario con la siguiente información:
- `ciudad`: Nombre de la ciudad
- `pais`: País de ubicación
- `temperatura_c`: Temperatura en Celsius
- `sensacion_termica_c`: Sensación térmica
- `descripcion`: Descripción del clima
- `humedad`: Porcentaje de humedad
- `velocidad_viento`: Velocidad del viento en km/h
- `presion_mb`: Presión atmosférica en milibares
- `visibilidad_km`: Visibilidad en kilómetros
- `uv_index`: Índice UV

**API Externa:** Utiliza wttr.in, un servicio gratuito de información meteorológica.

**Manejo de Errores:**
- Timeout: Si la consulta excede 10 segundos
- Error de conexión: Problemas de red
- Errores generales: Cualquier otra excepción

#### Configuración del Transporte

```python
mcp.settings.streamable_http_path = "/mcp"
```

El servidor expone sus herramientas mediante HTTP en el endpoint `/mcp`, permitiendo comunicación a través de HTTP Streamable Transport.

#### Ejecución

**Puerto:** 8000  
**Host:** 0.0.0.0 (accesible desde cualquier interfaz de red)  
**URL de acceso:** `http://localhost:8000/mcp`

---

## API.py

### Propósito
Implementa una API REST con Flask que actúa como intermediario entre usuarios y un modelo de lenguaje (Ollama), permitiendo que el modelo utilice herramientas del servidor MCP de forma transparente.

### Configuración

#### Constantes
- `OLLAMA_API_URL`: URL del servidor Ollama (10.0.0.0:11434)
- `MODELO`: Modelo de lenguaje a utilizar (qwen2.5:3b)
- `SYS_PROMPT`: Prompt del sistema que define el comportamiento del asistente

### Componentes Principales

#### 1. System Prompt (`SYS_PROMPT`)

Define las reglas de comportamiento del asistente:
- Respuestas concisas (3-4 oraciones máximo)
- Conversacional y natural
- Siempre en español
- Uso de herramientas mediante formato estructurado

**Formato para usar herramientas:**
```
USE_TOOL: nombre_herramienta
ARGS: {"argumento": "valor"}
```

#### 2. Función `ejecutar_herramienta_mcp_async`

**Propósito:** Ejecuta herramientas del servidor MCP de forma asíncrona.

**Parámetros:**
- `nombre_herramienta` (str): Nombre de la herramienta a ejecutar
- `args` (dict): Argumentos para la herramienta

**Proceso:**
1. Establece conexión con el servidor MCP via HTTP
2. Llama a la herramienta especificada
3. Procesa y extrae el resultado
4. Intenta parsear como JSON si es posible
5. Retorna el resultado procesado

**Manejo de resultados:**
- Extrae contenido de objetos estructurados
- Parsea texto JSON cuando es posible
- Convierte a string como fallback

#### 3. Función `ejecutar_herramienta_mcp`

**Propósito:** Wrapper síncrono para `ejecutar_herramienta_mcp_async`.

**Funcionamiento:**
- Crea un nuevo event loop
- Ejecuta la función asíncrona
- Cierra el loop al finalizar
- Permite usar código asíncrono en contexto síncrono

#### 4. Función `procesar_con_herramientas`

**Propósito:** Lógica principal que coordina el modelo de lenguaje y las herramientas.

**Parámetros:**
- `prompt` (str): Consulta del usuario
- `historial` (list): Conversaciones previas

**Flujo de ejecución:**

1. **Preparación de mensajes:**
   - Agrega el system prompt
   - Incluye historial previo
   - Añade el prompt del usuario

2. **Primera llamada a Ollama:**
   - Envía los mensajes al modelo
   - Temperatura: 0.7 (balance creatividad/precisión)
   - Sin streaming

3. **Detección de uso de herramientas:**
   - Busca el marcador "USE_TOOL:" en la respuesta
   - Extrae nombre de herramienta y argumentos
   - Parsea los argumentos JSON

4. **Ejecución de herramienta (si aplica):**
   - Llama al servidor MCP con los parámetros
   - Recibe el resultado
   - Formatea como JSON

5. **Segunda llamada a Ollama:**
   - Agrega la respuesta inicial al historial
   - Incluye el resultado de la herramienta
   - Solicita al modelo que interprete el resultado
   - Retorna la respuesta final interpretada

6. **Sin herramientas:**
   - Si no se detecta uso de herramientas, retorna la respuesta directa

### Endpoints

#### POST `/ask-ia`

**Propósito:** Endpoint principal para interactuar con el asistente.

**Body (JSON):**
```json
{
  "prompt": "¿Cómo está el clima en Madrid?",
  "historial": [
    {"role": "user", "content": "Hola"},
    {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"}
  ],
  "formato": "json"
}
```

**Parámetros:**
- `prompt` (requerido): Consulta del usuario
- `historial` (opcional): Array de mensajes previos
- `formato` (opcional): Formato de respuesta (por defecto "json")

**Respuesta exitosa:**
```json
{
  "response": "En Madrid actualmente hay 18°C con cielo despejado..."
}
```

**Respuestas de error:**
- 400: Request inválido o falta prompt
- Errores de conexión con Ollama

#### GET `/health`

**Propósito:** Verificar el estado del servidor.

**Respuesta:**
```json
{
  "status": "ok"
}
```

### Ejecución

**Puerto:** 5000  
**Host:** 0.0.0.0  
**URL base:** `http://localhost:5000`

---

## Flujo de Interacción Completo

### Ejemplo: Consulta del Clima

1. **Usuario hace request a API:**
   ```
   POST /ask-ia
   {"prompt": "¿Qué temperatura hace en Buenos Aires?"}
   ```

2. **API.py procesa:**
   - Envía prompt a Ollama con instrucciones
   - Ollama detecta necesidad de herramienta

3. **Ollama responde:**
   ```
   USE_TOOL: obtener_clima
   ARGS: {"ciudad": "Buenos Aires"}
   ```

4. **API.py ejecuta herramienta:**
   - Conecta con MCPServer.py
   - Llama a `obtener_clima("Buenos Aires")`

5. **MCPServer.py consulta:**
   - Hace request a wttr.in
   - Procesa datos meteorológicos
   - Retorna información estructurada

6. **API.py recibe resultado:**
   ```json
   {
     "ciudad": "Buenos Aires",
     "temperatura_c": "22",
     "descripcion": "Partly cloudy",
     ...
   }
   ```

7. **Segunda llamada a Ollama:**
   - Envía resultado de la herramienta
   - Ollama genera respuesta natural

8. **Respuesta final al usuario:**
   ```
   "En Buenos Aires actualmente hay 22°C con cielo 
   parcialmente nublado. La sensación térmica es de 
   20°C con una humedad del 65%."
   ```

---

## Requisitos y Dependencias

### MCPServer.py
- `fastmcp`: Framework para crear servidores MCP
- `requests`: Para consultas HTTP
- `uvicorn`: Servidor ASGI

### API.py
- `flask`: Framework web
- `requests`: Cliente HTTP
- `fastmcp`: Cliente MCP
- `asyncio`: Para operaciones asíncronas

### Servicios externos
- **Ollama**: Servidor de modelos de lenguaje (10.0.0.0:11434)
- **wttr.in**: API gratuita de información meteorológica

---

## Arquitectura del Sistema

```
Usuario
  │
  ↓
[API Flask :5000]
  │
  ├─→ [Ollama] ← Modelo de lenguaje
  │     │
  │     ↓
  │   Detecta necesidad de herramienta
  │
  └─→ [MCP Server :8000]
        │
        └─→ [wttr.in API] ← Datos del clima
```

---

## Consideraciones de Seguridad

1. **Timeout:** Solicitudes HTTP tienen timeout de 10 segundos
2. **Error handling:** Todos los componentes manejan excepciones
3. **Validación:** Se valida la presencia del prompt en requests
4. **Network exposure:** Ambos servidores expuestos en 0.0.0.0

## Posibles Mejoras

1. Agregar más herramientas al servidor MCP
2. Implementar autenticación en los endpoints
3. Agregar logging estructurado
4. Implementar caché para consultas frecuentes
5. Soporte para streaming de respuestas
6. Manejo de historial persistente
7. Rate limiting en la API
