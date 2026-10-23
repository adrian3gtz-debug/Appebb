import { useEffect, useState } from 'react'
import { MatchReplay } from './features/replay/MatchReplay'
import { initialLanguage, saveLanguage, translations } from './i18n'
import type { Language } from './i18n'

type ConnectionStatus = 'checking' | 'connected' | 'unavailable'
type HealthResponse = { status: string }

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

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
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 sm:px-10">
        <header className="flex flex-wrap items-center justify-between gap-5 border-b border-[#dce5db] py-7">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-xl bg-[#205c41] text-xl font-bold text-white" aria-hidden="true">F</div>
            <span className="text-base font-semibold tracking-tight sm:text-lg">Football Intelligence Lab</span>
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
            <div role="status" aria-live="polite" className="flex items-center gap-2 text-sm font-medium text-[#4c6256]">
              <span className={`size-2.5 rounded-full ${connection === 'connected' ? 'bg-[#3b9a68]' : connection === 'checking' ? 'bg-amber-500' : 'bg-red-500'}`} />
              {statusText}
            </div>
          </div>
        </header>

        <section className="flex-1 py-10 sm:py-14">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{copy.replayTitle}</h1>
          <p className="mt-3 max-w-3xl leading-7 text-[#53675b]">{copy.syntheticNotice}</p>
          <MatchReplay language={language} />
        </section>
      </div>
    </main>
  )
}

export default App
