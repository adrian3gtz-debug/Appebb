# Proveedores de IA: Groq y Azure

El backend permite elegir **Groq** para las explicaciones de recuperaciones y el
relato general/final. Se conserva el adaptador de Azure. La selección es explícita:
no hay conmutación automática ni una segunda llamada al fallar un proveedor.

## Activar Groq en Vercel

1. Crear una clave privada en <https://console.groq.com/keys>.
2. En **api-futblify → Settings → Environment Variables**, configurar **Production**:

   | Key | Value | Tipo |
   | --- | --- | --- |
   | `AI_PROVIDER` | `groq` | Config |
   | `GROQ_API_KEY` | La clave privada de Groq | Secret |
   | `GROQ_MODEL` | `openai/gpt-oss-120b` | Config |

3. Guardar y redeplegar el **backend** después de publicar el código del adaptador.
   Publicar también el frontend actualizado para que acepte `generation: "groq"`.
4. En la aplicación, solicitar una explicación manual. La respuesta de `/narrative`
   debe ser 200, identificar `generation: "groq"` y mostrar referencias válidas.
5. Comprobar inicio, 20:00, 89:59 y final; Aficionado/Analista y ES/EN. En el escenario
   original, el marcador final local–visitante es **0–2**.

No cambiar CORS ni la URL del frontend. Las variables de Azure pueden conservarse:
no se leen al seleccionar Groq. La clave de Azure no sirve como clave de Groq.
No introducir secretos en `VITE_`, Git, capturas ni el chat.

Para uso local, colocar las mismas tres variables en `backend/.env` y reiniciar:

```powershell
cd backend
python -m uvicorn app.main:app --reload --env-file .env
```

## Contrato y límites

- Modelo predeterminado Groq: `openai/gpt-oss-120b`; también se admite
  `openai/gpt-oss-20b`. Ambos tienen soporte documentado de JSON Schema estricto.
- Chat Completions HTTPS en un endpoint fijo de Groq, autenticación Bearer,
  mensajes de sistema y hechos calculados; sin herramientas ni historial.
- `reasoning_effort=low`, `include_reasoning=false`; presupuesto de 4,096 tokens
  de completado, incluyendo razonamiento. Solo se extrae el texto final de una
  respuesta terminada con `finish_reason=stop`.
- Los hechos, referencias, restricciones de cifras, cortes temporales y controles
  de interpretación siguen verificándose en Python para ambos proveedores.
  Los controles no prueban fidelidad semántica completa; se conserva la evidencia.
- Caché por proveedor, modelo, endpoint, hechos, versión, idioma y audiencia.
  Una llamada simultánea y seis intentos/minuto por worker, compartidos entre
  ambos endpoints. No es un límite global entre réplicas de Vercel.
- HTTP 25 s, conexión 5 s, plazo total 30 s, sin reintentos. Los errores exponen
  categoría y estado HTTP, sin cuerpo del proveedor ni credenciales. Un 429
  mantiene el análisis calculado disponible y permite reintentar más tarde.
- El plan gratuito de Groq tiene límites por organización y modelo; revisar la
  cuota de la cuenta. No se activa ningún plan de pago desde la aplicación.

Sin `AI_PROVIDER`, se mantiene Azure por compatibilidad. Para volver a Azure usar
`AI_PROVIDER=azure_openai` y las tres variables `AZURE_OPENAI_*` del ejemplo.
Un proveedor desconocido, modelo no admitido o clave ausente devuelve 503.

## Estado comprobado

El usuario autorizó el cambio tras ver que Azure deshabilitó su suscripción por
una alerta de actividad sospechosa. La última llamada pública a Azure devolvió
401 (expuesto por nuestro API como 502). La causa de la alerta sigue sin conocerse;
el registro de `Microsoft.ResourceHealth` no reactiva la inferencia.

La integración Groq se verificó con transporte HTTP simulado, sin clave ni llamadas
reales: **230 pruebas backend, 19 frontend y build correctos**. También pasó Chromium con respuestas Groq simuladas: etiquetas del proveedor,
ES/EN, audiencias, retroceso, final automático, errores y vista móvil.
La inferencia real y el despliegue actualizado requieren la clave privada del usuario y verificación
en la URL pública; no se presentan como completados.

Para la entrega, identificar el proveedor realmente utilizado. Una respuesta de
Groq no es una respuesta de Microsoft Foundry. Las reglas permiten integraciones
de terceros, pero eso no garantiza elegibilidad para una categoría de Microsoft.
La suscripción de Azure debe resolverse con soporte por separado.

Fuentes: [Structured Outputs](https://console.groq.com/docs/structured-outputs),
[razonamiento](https://console.groq.com/docs/reasoning),
[límites](https://console.groq.com/docs/rate-limits).
