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
    checking: 'Checking connection',
    connected: 'Backend connected',
    unavailable: 'Backend unavailable',
  }[connection]

  return (
    <main className="min-h-screen bg-[#07121b] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-8 sm:px-10">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-6">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-emerald-400/30 bg-emerald-400/10 text-xl font-black text-emerald-300" aria-hidden="true">F</div>
            <div>
              <p className="text-sm font-bold tracking-wide">FOOTBALL INTELLIGENCE LAB</p>
              <p className="text-xs text-slate-400">Match Story Engine</p>
            </div>
          </div>
          <div role="status" className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200">
            <span className={`size-2 rounded-full ${connection === 'connected' ? 'bg-emerald-400' : connection === 'checking' ? 'bg-amber-400' : 'bg-rose-400'}`} />
            {statusText}
          </div>
        </header>

        <section className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-300">Foundation · Phase 1</span>
            <h1 className="mt-7 max-w-2xl text-5xl font-semibold leading-tight tracking-tight sm:text-6xl">See the story <span className="text-emerald-300">behind the match.</span></h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-300">A workspace for explainable football analysis. Match events, evidence, and clear narratives will come together here.</p>
            <p className="mt-8 text-sm text-slate-400">The foundation is running. No match data or insights are loaded yet.</p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-[#10212b] p-6 shadow-2xl shadow-black/20 sm:p-8">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">System status</p>
                <h2 className="mt-2 text-2xl font-semibold">Ready for kickoff</h2>
              </div>
              <span className="text-3xl text-emerald-300" aria-hidden="true">◎</span>
            </div>
            <div className="mt-8 space-y-4">
              <StatusRow label="Interface" value="React + TypeScript" />
              <StatusRow label="API" value="FastAPI + Pydantic" />
              <StatusRow label="Connection" value={statusText} />
            </div>
            {connection === 'unavailable' && <p className="mt-6 text-sm leading-6 text-amber-200">Start the backend on port 8000, then refresh this page.</p>}
          </div>
        </section>

        <footer className="border-t border-white/10 pt-5 text-xs text-slate-500">Built for synthetic, evidence based match analysis.</footer>
      </div>
    </main>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-4 text-sm"><span className="text-slate-400">{label}</span><span className="text-right font-medium text-slate-100">{value}</span></div>
}

export default App
