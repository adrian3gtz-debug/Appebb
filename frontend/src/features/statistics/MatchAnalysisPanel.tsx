import type { Language } from '../../i18n'
import type { Match, MatchEvent } from '../../types/match'
import type { DemoScenario } from '../../types/recoveries'
import { RecoveryPanel } from '../recoveries/RecoveryPanel'
import { StatisticsPanel } from './StatisticsPanel'
import { statisticsCopy } from './copy'
import { useMatchAnalysis } from './useMatchAnalysis'
import { EventList } from '../replay/EventList'
import { translations } from '../../i18n'

interface Props { match: Match; second: number; playing: boolean; scenario: DemoScenario; language: Language; recentEvents: MatchEvent[]; onSeek: (second: number) => void }

export function MatchAnalysisPanel({ match, second, playing, scenario, language, recentEvents, onSeek }: Props) {
  const { data, error, retry } = useMatchAnalysis(scenario, second, playing)
  const copy = statisticsCopy[language]
  return <>
    {error && <div role="alert" className="mt-6 rounded-lg bg-red-50 p-4 text-red-800">{copy.error} <button onClick={retry} className="ml-2 font-semibold underline">{copy.retry}</button></div>}
    {!data ? <p role="status" className="py-8">{copy.loading}</p> : <>
      <RecoveryPanel match={match} second={data.as_of_second} data={data.recoveries} language={language} onSeek={onSeek} />
      <details className="mt-5 rounded-xl border border-[#dce5db] bg-white p-4 sm:p-6">
        <summary className="cursor-pointer text-lg font-semibold">{copy.title}</summary>
        <StatisticsPanel match={match} data={data.statistics} language={language} embedded />
      </details>
    </>}
    <details className="my-5 rounded-xl border border-[#dce5db] bg-white p-4 sm:p-6">
      <summary className="cursor-pointer text-lg font-semibold">{translations[language].latestEvents}</summary>
      <EventList match={match} events={recentEvents} language={language} />
    </details>
  </>
}
