# Explicaciones de recuperaciones con Microsoft Foundry

**Actualización:** Azure está suspendido por una alerta de la suscripción. Ya existe
un adaptador alternativo de Groq para ambos endpoints; consultar [selección de
proveedores](ai-providers.md). Esta guía conserva los detalles del adaptador Azure;
las pruebas reales históricas descritas abajo no certifican su disponibilidad actual.

El mismo proveedor también sirve al [relato general y la crónica final](match-narrative.md),
con idénticas variables privadas. Ambos endpoints comparten caché, concurrencia y
límite de intentos. Esta guía describe específicamente la explicación de recuperaciones.

## Alcance

`POST /api/matches/demo/explanation` permite solicitar una explicación EN/ES,
Aficionado/Analista, de un insight de recuperaciones que ya detectó Python.
El botón es explícito; el polling de análisis de 500 ms no llama al modelo.
El resumen calculado por reglas sigue disponible; el nuevo relato con IA tiene
su endpoint y controles propios. La inferencia en producción no está verificada.

El usuario creó `football-insights`, GPT-5 mini `2025-08-07`, Global Standard,
en un nuevo recurso de Foundry en North Central US. Canada Central no admite
esta combinación. Se comprobó respuesta en el playground con un caso 1→6 y
3 posesiones con remate. Posteriormente el usuario obtuvo una explicación desde
la app mediante su backend local y Foundry. El usuario confirmó el escenario
«Recuperaciones sin remate»: 1→6 recuperaciones y 0 secuencias con remate en la
captura coinciden con la evidencia calculada a 20:00. Esa llamada
real no sustituye una evaluación de todos los escenarios, idiomas y audiencias.

## Contrato y datos

El cliente envía escenario, segundo, ID de insight, idioma y audiencia; no acepta
prompts, URLs ni cifras del navegador. Python reconstruye el insight al corte
solicitado y congela sus hechos en `detected_second`. El proveedor recibe solo
equipo local/visitante, ventanas, conteos y secuencias con tiro, sin el partido
completo, información futura, etiquetas de escenarios ni datos personales.

Se utiliza Responses v1, `model` igual al nombre de implementación,
`store=false`, sin herramientas ni historial, JSON Schema estricto,
razonamiento mínimo y máximo de 1,000 tokens de salida (incluye razonamiento).
Timeout de 25 s, conexión 5 s, sin reintentos automáticos. Una respuesta truncada,
rechazada o que incumple el contrato se descarta. El error nunca incluye la
respuesta HTTP de Azure, su URL, encabezados ni credenciales.

Se validan formato, longitud, las dos referencias a hechos, números presentes
en la evidencia y términos de interpretación no permitidos. **Estos controles
léxicos no prueban fidelidad semántica**: una cifra correcta puede atribuirse al
intervalo incorrecto o un modelo puede inventar una conclusión con otras palabras.
La UI identifica la generación con IA y mantiene la evidencia para contrastarla.
Hace falta evaluar respuestas reales EN/ES en ambas audiencias antes de afirmar
calidad del modelo; un ejemplo de playground no es una evaluación suficiente.

## Coste y concurrencia

Una petición por clic. Caché LRU de 96 respuestas por contexto cerrado, idioma,
audiencia, endpoint e implementación. Volver a consultar el mismo insight más
tarde no crea hechos ni claves nuevos. Una llamada simultánea y seis intentos
por minuto por proceso; fallos también cuentan. Las respuestas en caché no
consumen más llamadas. Abortar en el navegador oculta resultados obsoletos, pero
no garantiza cancelar una llamada ya iniciada ni su cobro.

Estos límites y la caché son locales a cada worker: **no son un presupuesto
global ni autenticación**. Réplicas y reinicios de Vercel no comparten estado.
El endpoint accesible públicamente puede generar consumo externo. Antes de
publicarlo con credenciales, acordar acceso para la demo y límites en la capa de
hosting/proveedor; no describir CORS como protección frente a consumo no autorizado.
No se ha publicado ni habilitado una clave en este entorno.

## Configuración local (Windows / PowerShell)

Desde la raíz del repositorio, copiar el ejemplo:

```powershell
Copy-Item backend/.env.example backend/.env
notepad backend/.env
```

Completar **solo en ese archivo privado**:

```dotenv
AZURE_OPENAI_RESPONSES_ENDPOINT=https://adriangutierrezc-7589-resource.services.ai.azure.com/openai/v1/responses
AZURE_OPENAI_DEPLOYMENT=football-insights
AZURE_OPENAI_API_KEY=REEMPLAZAR_LOCALMENTE
```

Con el entorno Python activado y dependencias de desarrollo instaladas:

```powershell
cd backend
python -m uvicorn app.main:app --reload --env-file .env
```

En otra terminal, desde `frontend`, `npm run dev`. Elegir escenario de mayores
recuperaciones, avanzar a 20:00 o más y pulsar «Explicar con IA». Sin clave el
endpoint devuelve 503 y el análisis calculado sigue disponible. El archivo no
se carga por sí solo: se necesita `--env-file .env` o variables del proceso.
La clave no va al chat, al navegador, a Git ni a variables `VITE_`.

## Archivos

Verificación local: 175 pruebas backend, 13 frontend, build y Chromium móvil
correctos. El navegador usó respuesta de IA simulada, API real para evidencia y
API real sin configurar para comprobar el aviso de error. No hubo llamadas a Azure.

- `models/explanation.py`: solicitud acotada y respuesta trazable.
- `services/explanations.py`: hechos, adaptador Azure, controles y límites.
- `api/matches.py`: POST independiente; `main.py` permite preflight de POST.
- `features/recoveries/AiExplanation.tsx`: generación manual, aborto y comprobación
  de identidad del resultado. Cambiar contexto desmonta el componente.
- `tests/test_explanations.py`: proveedor simulado sin consumo externo.
