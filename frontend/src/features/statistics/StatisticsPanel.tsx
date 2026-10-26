import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { MatchStatistics } from '../../types/statistics'
import { formatClock } from '../replay/playback'
import { statisticsCopy } from './copy'
import { teamLabel } from '../replay/displayNames'

export function StatisticsPanel({ match, data, language, embedded = false }: { match: Match; data: MatchStatistics; language: Language; embedded?: boolean }) {
  const copy = statisticsCopy[language]
  const { home, away, possession } = data
  const number = new Intl.NumberFormat(language, { maximumFractionDigits: 1 })
  const percentage = (value: number | null) => value === null ? '—' : `${number.format(value)}%`
  const rows = [
    [copy.possession, percentage(possession?.home_share_percent ?? null), percentage(possession?.away_share_percent ?? null)],
    [copy.attempted, home.passes_attempted, away.passes_attempted],
    [copy.completed, home.passes_completed, away.passes_completed],
    [copy.accuracy, percentage(home.pass_accuracy_percent), percentage(away.pass_accuracy_percent)],
    [copy.shots, home.shots, away.shots],
    [copy.goals, home.goals, away.goals],
  ] as const

  return <section className={embedded ? 'mt-4' : 'mt-10 rounded-2xl border border-[#dce5db] bg-white p-5 sm:p-8'} aria-label={copy.title}>
    <div className="flex flex-wrap items-baseline justify-between gap-3">
      {!embedded && <h2 className="text-2xl font-semibold tracking-tight">{copy.title}</h2>}
      <p className="text-sm tabular-nums text-[#53675b]">{copy.through} {formatClock(data.as_of_second)}</p>
    </div>
    <table className="mt-5 w-full table-fixed text-sm sm:text-base">
      <thead><tr className="border-b border-[#dce5db]">
        <th scope="col" className="w-[42%] py-3 pr-3 text-left font-medium text-[#53675b]">{copy.metric}</th>
        <th scope="col" className="break-words px-1 py-3 text-center font-semibold">{teamLabel(match.home_team.name)}</th>
        <th scope="col" className="break-words px-1 py-3 text-center font-semibold">{teamLabel(match.away_team.name)}</th>
      </tr></thead>
      <tbody>{rows.map(([label, homeValue, awayValue]) => <tr key={label} className="border-b border-[#edf1eb]">
        <th scope="row" className="py-3 pr-3 text-left font-medium">{label}</th>
        <td className="py-3 text-center tabular-nums">{homeValue}</td>
        <td className="py-3 text-center tabular-nums">{awayValue}</td>
      </tr>)}</tbody>
    </table>
    <p className="mt-5 max-w-3xl text-sm leading-6 text-[#53675b]">{copy.context}</p>
    <details className="mt-5 border-t border-[#dce5db] pt-4 text-sm leading-6">
      <summary className="cursor-pointer font-medium">{copy.shotDetails}</summary>
      <table className="mt-3 w-full table-fixed">
        <thead><tr><th scope="col" className="w-[42%] text-left">{copy.metric}</th><th scope="col" className="break-words px-1">{teamLabel(match.home_team.name)}</th><th scope="col" className="break-words px-1">{teamLabel(match.away_team.name)}</th></tr></thead>
        <tbody>{([
          [copy.goals, 'goals'], [copy.saved, 'shots_saved'], [copy.offTarget, 'shots_off_target'], [copy.blocked, 'shots_blocked'],
        ] as const).map(([label, key]) => <tr key={key} className="border-b border-[#edf1eb]"><th scope="row" className="py-2 pr-2 text-left font-normal">{label}</th><td className="text-center tabular-nums">{home[key]}</td><td className="text-center tabular-nums">{away[key]}</td></tr>)}</tbody>
      </table>
    </details>
    <details className="mt-4 border-t border-[#dce5db] pt-4 text-sm leading-6 text-[#53675b]">
      <summary className="cursor-pointer font-medium text-[#19332a]">{copy.methodology}</summary>
      <p className="mt-3">{copy.method}</p>
      <p className="mt-3">{copy.shotMethod}</p>
      {possession ? <dl className="mt-3 grid gap-2 sm:grid-cols-2">
        <div><dt>{copy.control} · {teamLabel(match.home_team.name)}</dt><dd className="tabular-nums">{formatClock(possession.home_seconds)}</dd></div>
        <div><dt>{copy.control} · {teamLabel(match.away_team.name)}</dt><dd className="tabular-nums">{formatClock(possession.away_seconds)}</dd></div>
        <div><dt>{copy.contested}</dt><dd className="tabular-nums">{formatClock(possession.contested_seconds)}</dd></div>
        <div><dt>{copy.outOfPlay}</dt><dd className="tabular-nums">{formatClock(possession.out_of_play_seconds)}</dd></div>
      </dl> : <p className="mt-3">{copy.unavailable}</p>}
    </details>
  </section>
}
