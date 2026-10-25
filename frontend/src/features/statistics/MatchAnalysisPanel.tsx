import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { DemoScenario } from '../../types/recoveries'
import { RecoveryPanel } from '../recoveries/RecoveryPanel'
import { StatisticsPanel } from './StatisticsPanel'
import { statisticsCopy } from './copy'
import { useMatchAnalysis } from './useMatchAnalysis'

interface Props { match: Match; second: number; playing: boolean; scenario: DemoScenario; language: Language }

export function MatchAnalysisPanel({ match, second, playing, scenario, language }: Props) {
  const { data, error, retry } = useMatchAnalysis(scenario, second, playing)
  const copy = statisticsCopy[language]
  return <>
    {error && <div role="alert" className="mt-6 rounded-lg bg-red-50 p-4 text-red-800">{copy.error} <button onClick={retry} className="ml-2 font-semibold underline">{copy.retry}</button></div>}
    {!data ? <p role="status" className="py-8">{copy.loading}</p> : <>
      <StatisticsPanel match={match} data={data.statistics} language={language} />
      <RecoveryPanel match={match} second={data.as_of_second} data={data.recoveries} language={language} />
    </>}
  </>
}
