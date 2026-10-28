# Relato del partido y crónica final con IA

## Experiencia

La tarjeta **«¿Qué está pasando en el partido?»** aparece al principio del análisis,
en todos los escenarios y desde 00:00. No requiere un insight de recuperaciones.
«Explicar el partido ahora» solicita una fotografía al segundo actual, incluso
durante reproducción. La explicación muestra siempre su corte real de evidencia.
Si el reloj avanza conserva el texto con un aviso de que pertenece a ese corte;
si retrocede antes del corte, lo oculta y descarta. Aborta peticiones que quedaron
en el futuro, y descarta todo resultado al cambiar partido, idioma o audiencia.

La primera consulta activa la crónica automática al llegar a 90:00. Sin uso previo
de IA, el usuario también puede solicitarla directamente con «Generar crónica
final». A 89:59 el partido sigue en juego. Una explicación anterior en curso no
se presenta como crónica final mientras llega la nueva respuesta.

**Seguimiento opcional:** «Seguir el partido con IA» solicita estados en goles
registrados, cierres de diez minutos, descanso y final. Si se activa entre hitos,
parte del hito más reciente, con su corte visible. Mantiene una petición a la vez
y agrupa cambios con una pausa mínima de 30 s reales entre llamadas automáticas,
excepto al final. Al reproducir rápido puede omitir hitos intermedios para explicar
el último disponible. No es una explicación nueva en cada tick o cada segundo.
El usuario puede consultar el segundo exacto con el botón manual.

## Contrato de backend

`POST /api/matches/demo/narrative` recibe únicamente:

```json
{"scenario":"original","second":5400,"language":"es","audience":"fan"}
```

Python construye los hechos a ese corte desde el Match validado:

- Marcador local–visitante y estado en juego/final.
- Remates acumulados y pases completos/intentos/precisión de ambos equipos.
- Participación en tiempo controlado, con sus exclusiones y valores ausentes.
- Remates de los últimos diez minutos, o desde el inicio si aún no han pasado diez.
  La ventana es `(inicio, corte]`, incluyendo eventos en cero al comienzo del partido.
- Goles observados, reloj, marcador resultante e ID de evento.
- Última comparación destacada de recuperaciones por equipo, si existe. Sus conteos
  y remates corresponden a sus ventanas cerradas, no al resto del partido.

No usa nombres reales, etiquetas editoriales de escenarios ni eventos posteriores
al corte. No envía el partido completo al proveedor. Los hechos devueltos conservan
IDs de eventos cuando procede y descripciones EN/ES para revisar las referencias.
La ausencia de datos de control o precisión permanece ausente; no se transforma en cero.

## Personalización y validación

La solicitud de aficionado pide titular y **dos párrafos** breves, lenguaje sencillo,
marcador/remates y un contraste o actividad reciente. Analista pide titular y
**tres párrafos**, incluyendo pases/precisión de ambos equipos, control y ventana
reciente. El schema contiene solo los IDs de hechos de ese corte.

El backend exige las referencias centrales según audiencia y comprueba cada
número contra los hechos citados en **ese párrafo**. El titular solo puede usar
números del marcador/reloj y debe conservar exactamente el marcador local–visitante,
sin invertirlo para colocar al ganador primero. Rechaza referencias desconocidas, duplicadas, formato
inválido, ciertos términos de causalidad/táctica y resultados finales prematuros.
Se pide no derivar calidad de ocasiones, xG, superioridad, presión o decisiones de
entrenador. **Los controles léxicos y numéricos no prueban fidelidad semántica**;
una cifra conocida puede atribuirse incorrectamente. La UI mantiene las referencias
por párrafo para contrastarlas y el resumen calculado como respaldo.

El esquema enviado a Azure omite `minItems` y `maxItems`, que no admite su
[subconjunto de JSON Schema](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs#unsupported-type-specific-keywords).
Las longitudes y cantidades siguen verificándose con Pydantic y reglas locales.

## Proveedor y coste

La selección vigente se explica en [proveedores de IA](ai-providers.md).
Groq utiliza Chat Completions con JSON Schema estricto y 4,096 tokens de
completado. Ambos adaptadores comparten hechos, controles y límites.

En Azure reutiliza la misma configuración privada y Responses v1 de
[Foundry](foundry-explanations.md): sin herramientas ni historial, `store=false`,
razonamiento mínimo. El relato permite hasta 1,800 tokens de salida, incluyendo
razonamiento. Hay un plazo total de 30 s en backend y de 35 s en el navegador;
un error permite reintentar manualmente y no oculta estadísticas.
Los errores distinguen `provider_http_error` (incluye el estado HTTP de Azure),
`provider_timeout`, `provider_connection_error` y `response_rejected`. Los registros
no imprimen excepciones, cuerpos de Azure, encabezados ni credenciales.

Recuperaciones y relato comparten caché LRU de 96 resultados y límite de seis
intentos/minuto con una llamada simultánea **por worker**. La caché distingue
corte, evidencia, idioma, audiencia, versión e implementación. No hay presupuesto
global, autenticación ni caché compartida entre réplicas; la cuota de Azure puede
limitar antes. La llamada final puede encontrar un límite y mostrar reintento.
Abortar el navegador no garantiza cancelar la inferencia o evitar su cobro.

## Probar localmente

Con ambos servidores funcionando y la clave configurada solo en `backend/.env`:

1. En cualquier escenario, consultar a 00:00, 20:00 y otro corte arbitrario.
2. Comparar Aficionado/Analista y ES/EN; los hechos deben permanecer iguales.
3. En el escenario original, consultar a 89:59 y avanzar a 90:00: la crónica final
   debe conservar el marcador local–visitante 0–2.
4. Abrir referencias y navegar al primer gol; no debe aparecer el segundo antes
   de su momento. Retroceder durante una petición debe ocultar el resultado futuro.
5. Activar seguimiento y comprobar actualizaciones por hitos, no por cada tick.

Aquí se verificó la integración con proveedor simulado y API real para datos,
215 pruebas backend, 18 frontend, build y Chromium. La llamada real observada antes de esta
etapa fue la de recuperaciones sin remate. **El nuevo relato general/final aún debe
evaluarse con un proveedor real**. Azure quedó suspendido; Groq está
implementado y probado con transporte simulado, pendiente de clave y despliegue.

## Archivos principales

- `analytics/narrative.py`: hechos y actividad reciente al corte.
- `models/narrative.py`: solicitud, párrafos, referencias y respuesta.
- `services/narratives.py`: instrucciones, schema y comprobaciones.
- `services/explanations.py`: adaptador, plazo total y límites compartidos.
- `features/summary/MatchNarrative.tsx`: consulta, seguimiento, final y retroceso.
- `features/summary/narrativeRequest.ts`: hitos, contrato y timeout del navegador.
