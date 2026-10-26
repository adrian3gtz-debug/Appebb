import { useEffect, useState } from 'react'
import { MatchReplay } from './features/replay/MatchReplay'
import { apiBaseUrl } from './services/api'
import { initialLanguage, saveLanguage, translations } from './i18n'
import type { Language } from './i18n'

type ConnectionStatus = 'checking' | 'connected' | 'unavailable'
type HealthResponse = { status: string }

function App() {
  const [language, setLanguage] = useState<Language>(initialLanguage)
  const [connection, setConnection] = useState<ConnectionStatus>('checking')
  const copy = translations[language]

  useEffect(() => {
    document.documentElement.lang = language
    saveLanguage(language)
  }, [language])

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
    checking: copy.checking,
    connected: copy.connected,
    unavailable: copy.unavailable,
  }[connection]

  return (
    <main className="min-h-screen bg-[#f7f8f5] text-[#19332a]">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 sm:px-8">
        <header className="flex items-center justify-between gap-3 border-b border-[#dce5db] py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-[#205c41] font-bold text-white" aria-hidden="true">F</div>
            <span className="text-sm font-semibold tracking-tight sm:text-lg">Football Intelligence Lab</span>
          </div>
          <div className="flex flex-wrap items-center gap-5">
            <div role="group" aria-label={copy.languageLabel} className="flex gap-1 rounded-lg border border-[#dce5db] p-1">
              {(['en', 'es'] as const).map((option) => (
                <button
                  key={option}
                  type="button"
                  aria-pressed={language === option}
                  onClick={() => setLanguage(option)}
                  className={`rounded-md px-3 py-1 text-sm font-semibold transition-colors ${language === option ? 'bg-[#205c41] text-white' : 'text-[#4c6256] hover:bg-[#e8f0e8]'}`}
                >
                  {option.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </header>

        <section className="flex-1 py-5 sm:py-7">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{copy.replayTitle}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#53675b]">{copy.syntheticNotice}</p>
          <MatchReplay language={language} />
        </section>
        <footer className="border-t border-[#dce5db] py-4">
          <p role="status" className="flex items-center gap-2 text-sm text-[#53675b]">
            <span className={`size-2 rounded-full ${connection === 'connected' ? 'bg-[#3b9a68]' : connection === 'checking' ? 'bg-amber-500' : 'bg-red-500'}`} />
            {statusText}
          </p>
        </footer>
      </div>
    </main>
  )
}

export default App
