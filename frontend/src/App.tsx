import { useEffect, useState } from 'react'

type ConnectionStatus = 'checking' | 'connected' | 'unavailable'
type HealthResponse = { status: string }

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

function App() {
  const [connection, setConnection] = useState<ConnectionStatus>('checking')

  useEffect(() => {
    const controller = new AbortController()

    async function checkConnection() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/health`, {
          signal: controller.signal,
        })
        if (!response.ok) throw new Error('Health check failed')

        const health: HealthResponse = await response.json()
        setConnection(health.status === 'ok' ? 'connected' : 'unavailable')
      } catch {
        if (!controller.signal.aborted) setConnection('unavailable')
      }
    }

    void checkConnection()
    return () => controller.abort()
  }, [])

  const statusText = {
    checking: 'Comprobando conexión',
    connected: 'API conectada',
    unavailable: 'API sin conexión',
  }[connection]

  return (
    <main className="min-h-screen bg-[#f7f8f5] text-[#19332a]">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 sm:px-10">
        <header className="flex flex-wrap items-center justify-between gap-5 border-b border-[#dce5db] py-7">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-xl bg-[#205c41] text-xl font-bold text-white" aria-hidden="true">F</div>
            <span className="text-base font-semibold tracking-tight sm:text-lg">Football Intelligence Lab</span>
          </div>
          <div role="status" aria-live="polite" className="flex items-center gap-2 text-sm font-medium text-[#4c6256]">
            <span className={`size-2.5 rounded-full ${connection === 'connected' ? 'bg-[#3b9a68]' : connection === 'checking' ? 'bg-amber-500' : 'bg-red-500'}`} />
            {statusText}
          </div>
        </header>

        <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1fr_1fr] lg:gap-20">
          <div className="max-w-xl">
            <h1 className="text-5xl font-semibold leading-[1.1] tracking-tight sm:text-6xl">El fútbol, explicado con datos.</h1>
            <p className="mt-7 text-lg leading-8 text-[#53675b]">Un espacio para seguir el partido, explorar sus eventos y entender qué muestran los datos.</p>
            <p className="mt-8 text-base leading-7 text-[#53675b]">Estamos preparando el primer partido sintético para este laboratorio.</p>
          </div>

          <div className="overflow-hidden rounded-3xl border border-[#dce5db] bg-white shadow-[0_20px_60px_-45px_rgba(25,51,42,0.35)]">
            <div className="bg-[#e8f0e8] p-5 sm:p-8">
              <svg viewBox="0 0 520 320" className="h-auto w-full rounded-xl bg-[#3d8b60]" aria-hidden="true">
                <rect x="15" y="15" width="490" height="290" fill="none" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
                <line x1="260" y1="15" x2="260" y2="305" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
                <circle cx="260" cy="160" r="46" fill="none" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
                <circle cx="260" cy="160" r="3" fill="white" />
                <rect x="15" y="85" width="75" height="150" fill="none" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
                <rect x="430" y="85" width="75" height="150" fill="none" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
                <rect x="15" y="120" width="28" height="80" fill="none" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
                <rect x="477" y="120" width="28" height="80" fill="none" stroke="white" strokeOpacity="0.8" strokeWidth="2" />
              </svg>
            </div>
            <div className="p-6 sm:p-8">
              <h2 className="text-xl font-semibold">Todavía no hay un partido en pantalla</h2>
              <p className="mt-2 leading-7 text-[#64766a]">Aquí aparecerán los eventos cuando incorporemos el simulador.</p>
              {connection === 'unavailable' && <p className="mt-4 font-medium text-red-700">Inicia el backend en el puerto 8000 y actualiza la página.</p>}
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}

export default App
