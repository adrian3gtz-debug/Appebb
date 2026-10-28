# Paquete para preparar la entrega

## Estado antes de enviar

Fecha de revisión: **27 de octubre de 2026, Ciudad de México**.
Este paquete prepara materiales; **no certifica que la entrega esté terminada**.

| Elemento | Evidencia disponible | Pendiente |
| --- | --- | --- |
| Código | Base publicada `e300090`; cambio Groq y documentos preparados, subida autorizada | Verificar el commit remoto y los builds posteriores. |
| Reproducción, estadísticas, evidencia y modos | Pruebas y navegador local; también visibles en la captura pública del usuario | Recorrido final en la URL enviada. |
| IA de recuperaciones | Una respuesta real local en «Recuperaciones sin remate»: 1→6 y 0 posesiones con tiro, coincidente con Python | Verificar también el caso de 3 remates, EN/ES y audiencias. |
| Relato general/final | Implementado; suite total de 230 pruebas backend, 19 frontend y build; navegador con IA simulada | Evaluar con Groq real los nuevos textos. |
| IA pública | Azure devuelve 401; suscripción suspendida; Groq implementado con mocks | Subida autorizada; usuario ya tiene clave. Verificar variables, nuevos builds e inferencia real. |
| GitHub | Consultado: repositorio privado, rama predeterminada `main` | Hacer público con autorización. Enlazar la rama que contiene la aplicación. |
| Video | Guion preparado abajo | Grabar una ejecución real, subir y comprobar enlace público de menos de 2 minutos. |
| Portal | El usuario confirmó inscripción y acceso | Completar campos, enviar y guardar comprobante. |

Cierre verificado: **28/10/2026 a las 00:59 en Ciudad de México**
(27/10/2026, 23:59 Pacific). Las [reglas oficiales](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md)
prevalecen ante cualquier cambio. Este documento no afirma un envío realizado.

## Enlaces a utilizar

- Aplicación: <https://futbolify-psi.vercel.app>
- API: <https://api-futblify.vercel.app/api/health>
- Código de la aplicación: <https://github.com/adrian3gtz-debug/Appebb/tree/phase1-foundation>
- Documentación API: <https://api-futblify.vercel.app/docs>

El enlace de código solo será accesible a los jueces al hacer público el repo.
La rama predeterminada es `main`; usar el enlace explícito a `phase1-foundation`
evita dirigirlos a una rama diferente de la aplicación. No hace falta renombrar
el repositorio ni cambiar ramas para usar este enlace.

## Textos de propuesta (inglés)

Los siguientes textos describen el producto implementado. Usar la versión como
capacidad demostrada **después de resolver y verificar la IA pública**. Mientras
tanto, conservar explícita la limitación de configuración y validación.

### Title

Football Intelligence Lab — Match Story Engine

### Short pitch

Turn synthetic football events into match stories you can inspect: synchronized
replay, audience-specific AI narration and final reports linked to calculated evidence.

### Project description

Football Intelligence Lab helps fans and analysts understand the events behind a
scoreline. It replays reproducible synthetic football matches and calculates the
score, shots, passing, controlled-ball time and recovery-to-shot sequences through
the selected match clock.

A selectable AI adapter receives a bounded set of calculated facts. The alternate
provider is Groq with GPT-OSS 120B; the Azure GPT-5 mini adapter remains available
in code, but its subscription is suspended. Real Groq inference must be verified
before presenting it as demonstrated functionality. The application supports a whole-match explanation at a
chosen instant, an optional milestone-based follow mode, a final report at full
time after activation, and explanations of highlighted recovery changes.

Fans receive a short, accessible account; analysts receive a more detailed account
covering passing, control and recent shot activity. Both experiences support English
and Spanish. Paragraphs cite facts that viewers can inspect. Rewinding removes
future narration and goal evidence from the view.

Python remains responsible for the calculations. Response checks reject unknown
references, numbers absent from cited facts, incorrect home-away headline scores
and selected unsupported interpretations. These checks do not prove complete
semantic correctness, so the evidence and calculated summaries remain available.

An offline comparison with the licensed Wyscout/Pappalardo Premier League 2017/18
dataset informs a limited, versioned generator adjustment. The public replay uses
synthetic data. We report remaining differences rather than claiming professional
calibration, tactical causality or live match-feed ingestion.

### Technologies actually used

- Groq Chat Completions / GPT-OSS 120B: implemented; live verification pending.
- Microsoft Foundry / Azure OpenAI Responses v1: historical local recovery call verified; currently suspended.
- Python, FastAPI, Pydantic and HTTPX for evidence, response checks and API services.
- React, TypeScript, Vite and Tailwind for synchronized replay and audience views.
- GitHub for source and Vercel for separate frontend and API deployments.
- Pytest, Vitest and Chromium browser checks.

Do not list Agent Framework, MCP orchestration, AKS, Fabric, Cosmos DB, databases
or external live feeds as implemented technologies. There are no collaborating
runtime agents in the current application.

### Suggested category

Check the actual category requirements in the portal before submitting. A Groq-only
runtime must not be described as Microsoft Foundry usage. Third-party APIs are
allowed by the general rules, but that does not establish eligibility for a
Microsoft-specific category. Report the suspended Azure integration honestly.

### Validation and limitations field, if available

The code passed 230 backend tests, 19 frontend tests and the frontend production
build. Browser checks cover clock boundaries, citations, audience/language changes,
future-result cancellation and final-report activation with simulated provider
responses. One real local recovery explanation matched its calculated facts.
The new general/final prompts and production inference require separate verification;
update this statement with only the results actually observed before submission.

The generator models a simplified 90-minute match. Pass volume, timing and direction
still differ from the historical reference. There is no xG model, tracking data,
formation inference or causal tactical analysis. Provider checks are conservative
guards, not a proof that every sentence is factually grounded. Request budgets and
caches are per worker rather than a global spending cap.

## Video: 110 segundos, con narración preparada

Grabar la app real **después de comprobar la IA**. Mantener visibles los cortes.
Si una respuesta tarda, puede prepararse antes de grabar; no simular una petición
exitosa ni presentar respuestas de mocks como inferencia real. Dejar margen hasta
2:00 para títulos y cierre. La tabla propone duración total de 1:50.

| Tiempo | Mostrar | Voz sugerida en inglés |
| --- | --- | --- |
| 0–10 s | Nombre, replay y aviso de datos sintéticos | “A score tells us the result. Football Intelligence Lab lets us inspect the events behind the story.” |
| 10–28 s | Relato general a un corte comprobado; abrir una referencia | “Our Python engine calculates facts through the selected clock. The selected AI provider turns those facts into a match account, with references viewers can inspect.” |
| 28–43 s | Aficionado/Analista y versiones ES/EN comprobadas | “Fans get a concise story. Analysts get passing, controlled-ball time and recent shot activity. Both use the same evidence, in English or Spanish.” |
| 43–60 s | Mayores recuperaciones a 20:00; cancha y secuencia | “Here, final-third recoveries rise from one to six. Three possessions in the second window end in a shot. We show the recorded sequences without inventing a tactical cause.” |
| 60–82 s | Escenario original a 90:00, crónica con IA y marcador | “At full time, the activated AI generates a final report. The home side loses nil–two despite more controlled-ball time. Possession alone does not establish superiority.” |
| 82–98 s | Primer gol y retroceso anterior a un corte de IA | “Select a goal to inspect its moment. Rewind, and later goals and future AI narration disappear. Every account belongs to a visible evidence cutoff.” |
| 98–110 s | Arquitectura y vista móvil | “Reproducible scenarios test patterns and counterexamples. Python calculates, the selected provider explains, and React keeps the evidence synchronized.” |

## Instrucciones para jueces

Preparar estas instrucciones para el portal una vez comprobadas las URLs públicas:

1. Open the application URL and choose English or Spanish.
2. Select **More high recoveries** and seek to **20:00**. Inspect the increase from
   1 to 6 recoveries and the 3 possessions ending in a shot in the second window.
3. Use **Explain the match now** for an overview. Expand paragraph facts to inspect
   the source counts. Switch Casual fan/Analyst to compare the amount of detail.
4. Select **Circulation vs counterattack**. Activate AI with a manual request,
   then seek to **90:00** for the final report; the home-away score is **0–2**.
5. Select the first goal in the calculated recap and rewind. Later goals and any
   AI result belonging to a future cutoff must disappear.

AI requests may take several seconds and can reach provider/per-worker limits.
Calculated summaries, statistics and event evidence remain usable if generation
fails. Do not ask judges to supply their own API key or access an Azure account.

## Antes de pulsar enviar

- Confirmar el acceso público a app, repo/rama y video en una sesión sin iniciar cuenta.
- Comprobar inferencia real en la URL enviada y el marcador de la crónica final.
- Verificar ES/EN y Aficionado/Analista; anotar cualquier limitación observada.
- Revisar descripción/categoría contra los campos y reglas del portal.
- Confirmar video menor a 2:00 y sonido entendible.
- Enviar y conservar confirmación, enlace del proyecto y hora del envío.

Hacer público el repositorio, subir documentos y publicar/reconfigurar servicios
requieren la autorización aplicable. Preparar este paquete no realiza esas acciones.
