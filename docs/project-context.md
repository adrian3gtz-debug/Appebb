# Football Intelligence Lab — contexto y continuidad

Documento de entrada para retomar el proyecto en otra conversación. Resume decisiones vigentes y enlaza sus detalles técnicos; no es una transcripción del chat.

**Fecha de esta referencia:** 25 de octubre de 2026, zona America/Mexico_City.  
**Base de código al escribirla:** `9d5e1c1`, rama `phase1-foundation`. Este commit se subió correctamente a GitHub durante la conversación. Un commit posterior de documentación puede avanzar el HEAD sin cambiar esta base funcional.

## 1. Cómo retomar

1. Leer este documento y el [README](../README.md).
2. Confirmar el directorio disponible, las instrucciones locales aplicables, `git status`, la rama, el último commit y el remoto. El entorno de un chat nuevo puede ser diferente.
3. Consultar la documentación y el código del área que se vaya a trabajar. El estado real del repositorio tiene prioridad sobre una referencia histórica de este documento.
4. Explicar al usuario lo implementado, lo pendiente y el plan de la siguiente etapa. Esperar su aprobación antes de programar.
5. No interpretar las tareas propuestas aquí como autorización para implementarlas, subir cambios o consumir servicios.

No depender de archivos temporales, servidores o capturas de otro chat. Este documento y la documentación enlazada deben bastar para reconstruir el contexto.

## 2. Producto y objetivos

**Producto:** Football Intelligence Lab.  
**Experiencia principal:** Match Story Engine.  
**Propuesta de valor:** “From match events to explainable football intelligence.”

Queremos convertir eventos de fútbol en métricas, cambios observables y explicaciones trazables. La experiencia debe permitir reproducir un partido sintético, explorar acciones en una cancha y comprobar qué evidencia respalda una explicación.

El usuario busca participar en un hackathon, aprender React/TypeScript/Python/Git y construir un portafolio sólido de frontend, full-stack y análisis futbolístico. Le interesa acercarse al análisis profesional; no quiere conclusiones tácticas inventadas ni una demostración superficial de IA.

Contexto del hackathon aportado por el usuario:

- **Microsoft Inside the Game Developer Hackathon.**
- Reto: **The Synthetic Match Insights Engine for Premier League Studio**.
- Fecha límite comunicada: **27 de octubre de 2026**. Verificar las condiciones oficiales antes de preparar la entrega; esta fecha no se ha comprobado independientemente aquí.
- Flujo deseado: **Ingest → Interpret → Explain → Render → Personalize**.
- Debe funcionar con eventos sintéticos futbolísticamente razonables; el reto no proporciona partidos reales.
- La visión incluye Microsoft Foundry y componentes desplegados en Azure. El despliegue actual en Vercel no completa esa integración.

## 3. Usuario y forma de colaboración

El usuario es estudiante de Ingeniería en Tecnología de Software y tiene experiencia profesional en web. Conoce Vue 3, Quasar, JavaScript y `script setup`; para backend utiliza Go/Gin y también ha trabajado con Python y APIs.

Reglas y preferencias acordadas:

- Conversar en español y explicar brevemente decisiones importantes; relacionar conceptos con Vue/Quasar o Go/Gin cuando ayude.
- **Primero discutir la idea, después explicar el plan y los archivos afectados, y esperar aprobación para programar.** “Hazlo” o “ponte a trabajar” autorizan el alcance presentado.
- Trabajar por etapas pequeñas, verificar lo disponible y corregir errores antes de ampliar funciones.
- Al cerrar una etapa: explicar el resultado, cómo probarlo, las limitaciones y un mensaje de commit sugerido.
- **Solicitar autorización específica antes de hacer push, modificar remotos o desplegar.** La autorización de una subida anterior no autoriza la siguiente. Advertir que subir a la rama seguida por Vercel activa despliegues automáticos.
- Evitar servicios de pago sin aprobación. No guardar credenciales en el repositorio ni en variables públicas del frontend.
- Revisar archivos existentes antes de modificarlos. Respetar cambios del usuario.
- Mantener el repositorio y la carpeta existentes; no crear otro repositorio ni otra carpeta principal.
- No limitarse a darle la razón: investigar, contrastar propuestas y señalar restricciones o conclusiones que los datos no sostienen.
- El usuario a veces trabaja desde el teléfono. Dar enlaces estables y pasos concretos; cuando comparte una captura, basar la orientación en lo que muestra.
- El diseño elegido es **claro**, limpio y con pocos elementos decorativos. El pedido inicial de tema oscuro fue reemplazado por esta preferencia.
- Mantener español e inglés en la interfaz y README en inglés. Este documento de continuidad está en español para facilitar su revisión con el usuario.

## 4. Repositorio y despliegue conocidos

| Elemento | Estado conocido |
| --- | --- |
| Carpeta del usuario en Windows | `C:\proyectos\football-intelligence-lab` |
| Checkout de este entorno al escribir | `/workspace/Appebb`; verificar su existencia en otro chat |
| Remoto privado | `https://github.com/adrian3gtz-debug/Appebb` |
| Rama de trabajo y producción configurada en Vercel | `phase1-foundation` |
| Nombre pendiente del repositorio | Se prevé renombrarlo a `football-intelligence-lab`; todavía se llama `Appebb` |
| Frontend en Vercel | Proyecto `futbolify`, Root Directory `frontend`, preset Vite |
| Web estable | <https://futbolify-psi.vercel.app> |
| Backend en Vercel | Proyecto **`api-futblify`**, Root Directory del repositorio `./`, preset FastAPI |
| API estable | <https://api-futblify.vercel.app> |
| Salud del API | <https://api-futblify.vercel.app/api/health> |
| Documentación interactiva | <https://api-futblify.vercel.app/docs> |

Estos nombres y direcciones se obtuvieron de las capturas y la configuración realizada con el usuario. No se compró un dominio; se utilizan direcciones gratuitas `vercel.app`.

El usuario confirmó que la web y la conexión funcionaban antes de los últimos cambios. La subida de `9d5e1c1` se confirmó desde Git, pero **no se verificó el estado Ready ni la URL pública de ese último despliegue**. En este entorno, la herramienta web no pudo acceder al dominio publicado; las comprobaciones posteriores de interfaz se hicieron en navegador contra servidores locales. No afirmar una verificación pública que no ocurrió.

Los dos proyectos siguen la misma rama. Al subir un commit deben iniciarse sus builds automáticos; revisar el commit y el estado Ready en ambos antes de dar por publicada una nueva función. Cambiar variables de entorno requiere un nuevo despliegue para aplicarlas.

Configuración conocida:

- Frontend: `VITE_API_BASE_URL=https://api-futblify.vercel.app`, entorno Production y tipo **Config** en Vercel. La URL es pública por diseño; el prefijo `VITE_` la expone al navegador.
- API: `BACKEND_CORS_ORIGINS=https://futbolify-psi.vercel.app`, entorno Production. Son orígenes exactos, sin rutas ni barra final.
- CORS permite solicitudes desde esos orígenes; no es autenticación.
- La raíz `/` del API puede responder `{"detail":"Not Found"}`. La ruta de salud es `/api/health`.

### Problemas de despliegue ya resueltos

- Vercel rechazó requisitos Python incluidos desde el archivo raíz: `requirements.txt` ahora contiene la lista plana; `backend/requirements.txt` la reutiliza para instalaciones locales.
- Fijar FastAPI en la configuración raíz interfirió con el frontend. La raíz ya no fuerza un framework; `frontend/vercel.json` selecciona Vite y el proyecto API usa su preset FastAPI.
- Root `main.py` expone la aplicación y conserva el acceso a `backend/app/` y `data/synthetic/`. No cambiar el Root Directory del API a `backend` sin revisar el empaquetado de datos.
- La guía de despliegue conserva algunos nombres sugeridos para crear proyectos; el nombre real del API utilizado es `api-futblify`.

Detalles: [guía de Vercel](vercel-deployment.md).

## 5. Implementado y verificado hasta ahora

| Área | Función actual |
| --- | --- |
| Fundación | Monorepo React + TypeScript estricto + Vite + Tailwind; FastAPI + Pydantic; endpoint de salud, CORS y configuración por entorno. |
| Modelado | Equipos de once jugadores, roles, eventos validados y línea de tiempo de control del balón. |
| Reproducción | Marcador, reloj, pausa, reinicio, desplazamiento temporal y velocidades 1×/10×/30×/60×. Comienza pausada y a 30×. |
| Interfaz | Tema claro, EN/ES, controles compactos que permanecen visibles al desplazarse, análisis/cancha primero y estadísticas/eventos desplegables. |
| Estadísticas | Posesión, pases intentados/completados, precisión, tiros, goles y desglose de tiros hasta el corte temporal. |
| Recuperaciones | Recuperaciones adelantadas, seguimiento de posesiones hasta tiro/pérdida/interrupción y comparación entre ventanas cerradas. |
| Evidencia | Cancha SVG seleccionable, acciones registradas de la posesión, conteos, reglas y límites consultables. |
| Generación | Escenarios guionizados de regresión y generador variado `varied-v1`, con semilla y duraciones/desenlaces variables. |
| Diagnóstico | Auditoría independiente de continuidad, receptores, reinicios y límites físicos asumidos; resúmenes de distribuciones. |
| Publicación | Frontend y backend separados en Vercel; confirmar el último despliegue como se indica arriba. |

Hitos recientes:

| Commit | Cambio |
| --- | --- |
| `9d5e1c1` | Generador variado y diagnósticos |
| `2c12733` | Reorganización de UI/UX |
| `7c63315` | Estadísticas con corte temporal e investigación |
| `767abc4` | Separación de configuración Vite/FastAPI |
| `86ccc47` | Primera funcionalidad de recuperaciones con evidencia |

**Última verificación registrada de código:** 109 pruebas backend, 9 frontend y compilación frontend correctas. Se comprobaron veinte semillas y se recorrió el nuevo escenario en Chromium local con API real local: estadísticas, marcador final, pausa/reinicio/retroceso, idiomas, conservación del escenario guionizado y móvil sin desbordamiento horizontal. Estos son resultados históricos de la etapa anterior, no una ejecución nueva al escribir esta documentación.

## 6. Arquitectura y archivos de entrada

Flujo implementado:

```text
JSON o generador sintético → Match validado con Pydantic
                          → estadísticas y análisis de recuperaciones en Python
                          → evidencia estructurada por API
                          → React: textos por plantillas, cancha y tablas
```

| Ubicación | Responsabilidad |
| --- | --- |
| `backend/app/models/` | Contratos de eventos, partido, posesión, estadísticas y evidencia |
| `backend/app/services/match_repository.py` | Selección de escenarios; caché del partido variado de demo |
| `backend/app/services/varied_generator.py` | Generador nuevo; semilla por defecto 7, versión `varied-v1` |
| `backend/app/services/synthetic_audit.py` | Diagnóstico desde eventos e intervalos, sin etiquetas del generador |
| `backend/app/services/synthetic_generator.py` | Escenario original de circulación/contraataque |
| `backend/app/services/recovery_scenarios.py` | Tres escenarios guionizados para comprobar recuperaciones |
| `backend/app/analytics/` | Cálculos deterministas de posesión, estadísticas y recuperaciones |
| `backend/app/api/matches.py` | Endpoints de partidos y análisis |
| `frontend/src/features/replay/` | Reloj, controles, selector y eventos |
| `frontend/src/features/recoveries/` | Explicaciones por plantillas, evidencia y cancha |
| `frontend/src/features/statistics/` | Consulta compartida de análisis y panel de estadísticas |
| `frontend/src/services/` y `frontend/src/types/` | Acceso al API y tipos del frontend |
| `frontend/src/i18n.ts` | Idioma, traducciones generales y preferencia persistida |
| `main.py`, `vercel.json`, `frontend/vercel.json` | Entradas y configuración para Vercel |

API actual:

- `GET /api/health` → `{"status":"ok"}`.
- `GET /api/matches/demo?scenario=varied` → partido completo validado y origen sintético.
- `GET /api/matches/demo/analysis?scenario=varied&second=1200` → estadísticas y recuperaciones del mismo partido y corte.
- `GET /api/matches/demo/recoveries?scenario=higher_recoveries&second=1200` → endpoint de evidencia conservado.
- `/docs` → documentación de FastAPI.

**Diferencia deliberada:** la UI comienza en `varied`, pero el API sin parámetro de escenario sigue usando `original` por compatibilidad. El partido variado del navegador utiliza siempre la semilla 7; reiniciar no genera uno nuevo. La CLI permite otras semillas.

El navegador descarga el partido completo y reproduce una secuencia grabada. No hay ingesta de eventos en directo, SSE ni WebSockets. El payload descargado contiene eventos futuros, aunque la interfaz y los análisis por corte los ocultan hasta su momento. El análisis comparte una consulta cada 500 ms como máximo durante el polling normal, sin duplicarla por panel; limita solicitudes simultáneas y muestra su hora real de evidencia.

## 7. Contratos y principios que deben conservarse

- Coordenadas fijas `x,y` en 0–100; no son metros. El equipo local ataca hacia x=100 en el primer tiempo y hacia x=0 en el segundo; el visitante al revés.
- Partido de 5,400 segundos, cambio de tiempo en 2,700; sin tiempo añadido ni prórroga. Los eventos no ocurren en 5,400.
- Tipos actuales: pase, conducción, recuperación, presión y tiro. Un tackle puede aparecer como método de recuperación; no hay cobertura completa de todas las acciones defensivas.
- Los intervalos `controlled`, `contested` y `out_of_play` son semiabiertos `[inicio, fin)`. Si existen, deben cubrir todo el reloj sin huecos ni solapamientos.
- Posesión = tiempo controlado del equipo / tiempo controlado de ambos. El disputado y fuera de juego se contabilizan aparte. No inferir posesión desde cantidad de pases.
- Los eventos se incluyen cuando `event.second <= corte`; los intervalos se recortan al tiempo observado. El modelo considera disponible el resultado de una acción en su marca registrada, sin mensajes separados de salida/llegada del balón.
- Cero y falta de datos son distintos: una precisión sin intentos o una posesión sin denominador disponible se muestran como `—`.
- Los goles salen de tiros registrados con resultado `goal`. Volumen de tiros no equivale a calidad de ocasiones; precisión y posesión no prueban superioridad.
- Una recuperación adelantada ocurre en el último tercio según la dirección de ataque. Las comparaciones actuales usan ventanas consecutivas de diez minutos dentro de cada tiempo; sus conteos se congelan al cierre.
- El criterio de destacar recuperaciones es una regla editorial explícita, no una prueba de significancia estadística ni una medición validada de presión.
- El analizador recibe eventos y parámetros numéricos, nunca la etiqueta de comportamiento que el generador intenta producir.
- No generar insights si no se cumple una regla. No atribuir cambios de formación, instrucciones del entrenador o causalidad a observaciones que no los prueban.
- La futura IA comunicará evidencia ya calculada. No será responsable de inventar cifras ni descubrir patrones sin un motor verificable.

Definiciones completas: [esquema](event-schema.md), [estadísticas](match-statistics.md), [recuperaciones](recovery-analysis.md).

## 8. Datos sintéticos: qué cambió y qué falta

| Escenario | Propósito |
| --- | --- |
| `varied` | Explorar posesiones variables, con decisiones por zona/contexto, circulación, progresión, bandas y transición. No garantiza un insight. |
| `higher_recoveries` | Contraste guionizado: en la primera comparación, recuperaciones adelantadas de 1 a 6 y 3 secuencias posteriores con tiro dentro de la ventana. |
| `stable` | Contraejemplo guionizado sin aumento destacado. |
| `recoveries_without_shots` | Aumento guionizado de recuperaciones sin tiros posteriores. |
| `original` | Circulación frente a contraataque: más posesión con menos tiros y derrota del local. |

Los escenarios guionizados se mantienen como pruebas; no describen encuentros reales ni garantizan resultados universales. En `varied-v1`, la semilla modifica acciones, tiempos y resultados; la misma semilla y versión reproducen lo mismo. Los parámetros son supuestos de ingeniería, no tasas entrenadas con partidos profesionales.

La auditoría observa continuidad y distribuciones, sin emitir una nota de “realismo”. Veinte semillas pasaron los controles implementados. **Esto valida esas propiedades estructurales, no la representatividad estadística.**

Limitaciones conocidas:

- Sin calibración empírica frente a una muestra real comparable.
- Faltan faltas, fuera de juego, sustituciones, lesiones, córners y rebotes del mismo equipo tras un bloqueo.
- El tiempo efectivo puede resultar demasiado alto al faltar tipos de interrupción. Es una prioridad para la comparación futura.
- No se reconstruyen posiciones ni trayectorias de los 22 jugadores. Los puntos del SVG son acciones registradas.
- Los límites de velocidad usan un campo hipotético de 105×68 m. No son mediciones de velocidad del balón ni de jugadores.
- Los pesos internos de desenlaces de tiro son heurísticos. No se presentan como xG.

Metodología, supuestos, resultados de semillas y comandos: [generador variado](varied-synthetic-matches.md). El [escenario original](synthetic-scenario.md) conserva su documentación independiente.

## 9. Investigación consultada y conclusiones

El usuario pidió investigar proyectos similares y técnicas avanzadas. La investigación está registrada en [football-analytics-research.md](football-analytics-research.md); retomarla desde sus fuentes, sin afirmar que ya se implementaron sus modelos.

| Fuente | Aporte estudiado | Decisión vigente |
| --- | --- | --- |
| [socceraction, KU Leuven: xT](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/xT.html) | Valor de movimientos según el cambio de amenaza entre zonas | Posible primera extensión aprendida tras revisar datos, licencias y evaluación. Todavía no implementada. |
| [socceraction: VAEP](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/vaep.html) | Valor de acciones según cambios en probabilidades de marcar/recibir gol, con acciones previas y contexto | Requiere entrenamiento y validación histórica. Los escenarios guionizados no son una base suficiente para entrenarlo. |
| [Friends of Tracking: LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking) | Pitch Control, seguimiento y EPV para opciones de pase | Requiere tracking sincronizado. Nuestros endpoints de eventos no permiten reconstruir defensores ni control espacial. |
| [StatsBomb: Upgrading Expected Goals](https://blogarchive.statsbomb.com/articles/soccer/upgrading-expected-goals/) | Modelos de xG con contexto y separación entre ocasión y ejecución | Mantener tiros y desenlaces observados. Un modelo simple también necesitaría datos y calibración. |
| [Karun Singh: Introducing Expected Threat](https://karun.in/blog/expected-threat.html) | Decisiones de movimiento/tiro condicionadas por ubicación | Referencia conceptual para el generador por estados. No se aprendieron sus probabilidades ni se implementó xT. |
| [Hudl / StatsBomb Open Data](https://github.com/hudl/open-data) | Referencia futura de eventos y documentación de competiciones seleccionadas | Se consultó el repositorio. No se importaron registros reales, distribuciones de referencia ni parámetros entrenados. Revisar cobertura y licencia completa antes de usarlos. |

Conclusión vigente: la calidad y representatividad de los datos es el principal límite. Añadir un algoritmo más complejo no establece exactitud. Los modelos probabilísticos futuros necesitan trazabilidad, evaluación con partidos separados de los usados para ajustar y revisión de calibración/cobertura.

No llamar PPDA al conteo actual de recuperaciones: faltan acciones defensivas necesarias para una definición completa. Antes de interpretar cambios de recuperación, considerar oportunidades de recuperar, tiempo sin balón y actividad rival.

## 10. Siguiente etapa propuesta, todavía sin implementar

**Validar el generador frente a una referencia apropiada.** La última decisión de prioridad fue mejorar datos antes de añadir IA; no volver automáticamente a priorizar el resumen o el proveedor de lenguaje por una propuesta anterior del chat.

Plan para discutir y aprobar con el usuario:

1. Elegir una muestra de referencia y revisar licencia, cobertura y restricciones. StatsBomb Open Data es una candidata, no una selección ya cerrada.
2. Acordar las definiciones comparables: posesión, reinicios, tiempos, coordenadas, pases, tiros y pérdidas. Los eventos aislados no permiten asumir segundos exactos de control real.
3. Comparar distribuciones del generador y la muestra: duraciones, pases por posesión, zonas de tiros/pérdidas, frecuencias de reinicio y tiempo efectivo cuando sea medible de forma compatible.
4. Identificar diferencias y corregir reglas justificadas; separar la muestra utilizada para ajustar de la reservada para evaluar. Versionar cambios del generador.
5. Documentar resultados, incertidumbres y lo que siga sin poder compararse. Conservar las pruebas guionizadas y las propiedades estructurales.

Resultado esperado de esa etapa: un informe reproducible de diferencias y cambios sustentados, no una certificación genérica de “realismo”. No hay una muestra descargada, un adaptador real ni umbrales empíricos aprobados.

## 11. Trabajo posterior del producto

Pendientes, sujetos a priorización y aprobación:

- Progresión y entradas al último tercio, distribución por sectores y otras comparaciones tácticas con metodología explícita.
- Resumen final trazable desde métricas y eventos.
- Experiencias de aficionado y analista: mismos hechos, distinto detalle y lenguaje. EN/ES sí existe; estos dos modos todavía no.
- Contrato de insights más amplio y tarjetas compactas para transmisión.
- Interfaz de proveedor y Microsoft Foundry, con plantillas de desarrollo identificadas y validación de las explicaciones.
- Integración/despliegue en Azure y comprobación de requisitos oficiales del hackathon.
- Pruebas integrales publicadas, README final, diagrama de arquitectura y video demostrativo de menos de dos minutos.

Visión posterior: adaptador de partidos históricos reales al modelo común, tras revisar cobertura/licencias. Reconocimiento o tracking con YOLO/ByteTrack/BoT-SORT es opcional y posterior a estabilizar lo anterior. No hay visión por computadora implementada.

No se han integrado Foundry, un proveedor real de IA, xT, VAEP, xG, una base de datos, transmisión real ni un simulador físico completo. No presentar las plantillas actuales como IA ni los resultados sintéticos como observaciones de Premier League.

## 12. Comandos para Windows

Para actualizar la copia existente, revisar primero que los cambios locales estén atendidos. No descartar cambios para sincronizar.

```powershell
cd C:\proyectos\football-intelligence-lab
git status
git fetch origin
git switch phase1-foundation
git pull --ff-only origin phase1-foundation
```

Con dependencias instaladas, usar dos terminales desde la raíz del repositorio:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

Abrir <http://localhost:5173>. Para la instalación inicial, versiones requeridas y alternativas a activar el entorno, consultar el [README](../README.md). Vite usa un proxy local para `/api` si `VITE_API_BASE_URL` está vacío. `frontend/.env` no configura el proceso Python; la variable de CORS se define en su entorno.

Generar otro partido y diagnóstico desde `backend/`, con el entorno activo:

```powershell
python -m app.services.generate_match --mode varied --seed 19 --audit --output ../data/synthetic/varied-19.json
```

El archivo de salida debe ser nuevo: el comando rechaza sobrescrituras. El JSON contiene el contrato común; el informe y la procedencia se imprimen aparte.

Verificaciones según el cambio:

```powershell
# En backend/, con el entorno activo
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

```powershell
# En frontend/
npm test
npm run build
```

Nota de este entorno de ejecución: `TestClient` llegó a bloquearse dentro del aislamiento de herramientas; la misma prueba pasó fuera de ese aislamiento. No modificar el producto para ocultar un problema del entorno. Tampoco asumir que ese bloqueo ocurrirá en Windows.

## 13. Índice de documentación

| Documento | Consultar para |
| --- | --- |
| [README](../README.md) | Instalar, ejecutar y recorrer la demo |
| [Esquema de eventos](event-schema.md) | Contratos, coordenadas y control del balón |
| [Escenario original](synthetic-scenario.md) | Circulación/contraataque y sus desenlaces guionizados |
| [Generador variado](varied-synthetic-matches.md) | Estados, supuestos, auditoría y limitaciones |
| [Recuperaciones](recovery-analysis.md) | Secuencias, ventanas, umbrales y evidencia |
| [Estadísticas](match-statistics.md) | Fórmulas, denominadores y corte temporal |
| [Investigación](football-analytics-research.md) | Fuentes primarias, técnicas estudiadas y decisiones |
| [Vercel](vercel-deployment.md) | Configuración, variables y problemas de despliegue |

Actualizar este contexto después de cada etapa relevante: base de código, cambios implementados, verificaciones reales, límites y siguiente objetivo acordado. Mantener fórmulas y detalles extensos en sus documentos enlazados para evitar versiones contradictorias.

## 14. Mensaje para iniciar el próximo chat

> Estamos desarrollando Football Intelligence Lab. Lee `docs/project-context.md`, el README y la documentación del generador y de investigación. Verifica el repositorio, el estado de Git y la rama antes de proponer cambios. Quiero continuar con la validación de los datos sintéticos frente a una referencia apropiada. Primero explícame lo que hay, los límites y tu plan; espera mi aprobación para programar. No subas cambios ni consumas servicios de pago sin autorización. Explícame las decisiones en español y contrasta mis propuestas cuando la evidencia lo justifique.
