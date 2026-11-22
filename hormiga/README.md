# Hormiga buscadora (BFS / DFS) con CrewAI + PyQt5

Un equipo de 3 agentes (Arquitecto, Programador de algoritmos, Programador de interfaz)
genera un programa PyQt5 que visualiza búsqueda por anchura y profundidad.

## Pasos para ejecutarlo

1. Entra a la carpeta del proyecto
   cd hormiga_crew

2. Crea y activa un entorno virtual
   python3 -m venv venv
   source venv/bin/activate

3. Instala las dependencias
   pip install -r requirements.txt

4. Descarga el modelo local (Ollama debe estar corriendo)
   ollama pull qwen2.5-coder:7b

5. Crea tu archivo de configuración
   cp .env.example .env
   - Para usar Gemini en el agente de interfaz, pega tu API key en GEMINI_API_KEY.
   - Si la dejas vacía, todo corre con el modelo local.
   - Revisa el nombre vigente del modelo de Gemini en su documentación.

6. Corre el equipo de agentes
   python main.py
   Los agentes trabajan en orden y al final se guardan en la carpeta salida/:
   arquitectura.md, algoritmos.py e interfaz.py

7. Abre el juego generado
   cd salida
   python interfaz.py

## Si algo falla

- El código de un modelo pequeño puede traer errores. Lee el mensaje de error, corrígelo
  a mano o vuelve a correr main.py (cada corrida genera código distinto).
- "Connection refused" en Ollama: verifica que corra con `ollama list`.
- No subas tu .env a ningún repositorio.
