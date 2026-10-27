import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { MatchRecap } from '../../types/recap'
import type { MatchStatistics } from '../../types/statistics'
import { formatClock } from '../replay/playback'
import { playerLabel, teamLabel } from '../replay/displayNames'
import type { Audience } from './audience'
import { summaryCopy } from './copy'
import { summaryNarrative } from './narrative'

interface Props {
  match: Match; stats: MatchStatistics; recap: MatchRecap; language: Language;
  audience: Audience; onSeek: (second: number) => void
}

export function MatchSummary({ match, stats, recap, language, audience, onSeek }: Props) {
  const copy = summaryCopy[language]
  const narrative = summaryNarrative(match, stats, recap, language, audience)
  const number = new Intl.NumberFormat(language, { maximumFractionDigits: 1 })
  const percent = (value: number | null | undefined) => value == null ? copy.unavailable : `${number.format(value)}%`
  return <section className="mt-5 rounded-2xl border border-[#c8d6c9] bg-[#e8f0e8] p-4 sm:p-6" aria-label={recap.phase === 'full_time' ? copy.finalTitle : copy.liveTitle}>
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h2 className="text-lg font-semibold">{recap.phase === 'full_time' ? copy.finalTitle : copy.liveTitle}</h2>
      <p className="text-xs tabular-nums text-[#53675b]">{copy.through} {formatClock(recap.as_of_second)}</p>
    </div>
    <p className="mt-3 text-xl font-semibold tracking-tight sm:text-2xl">{narrative.headline}</p>
    <p className="mt-2 text-sm leading-6 text-[#365044]">{narrative.shots}</p>
    {narrative.observation && <p className="mt-3 max-w-3xl text-sm leading-6 text-[#365044]">{narrative.observation}</p>}
    {audience === 'analyst' && <div className="mt-4 grid gap-3 sm:grid-cols-2">
      {([['home', stats.home, match.home_team], ['away', stats.away, match.away_team]] as const).map(([side, team, roster]) => <div key={team.team_id} className="rounded-xl bg-white/70 p-3 text-sm">
        <h3 className="font-semibold">{teamLabel(roster.name)}</h3><dl>
        <div className="mt-2 flex flex-wrap justify-between gap-x-2"><dt>{copy.passes}</dt><dd className="tabular-nums">{team.passes_completed} / {team.passes_attempted}</dd></div>
        <div className="mt-1 flex flex-wrap justify-between gap-x-2"><dt>{copy.accuracy}</dt><dd className="tabular-nums">{percent(team.pass_accuracy_percent)}</dd></div>
        <div className="mt-1 flex flex-wrap justify-between gap-x-2"><dt>{copy.control}</dt><dd className="tabular-nums">{percent(stats.possession?.[side === 'home' ? 'home_share_percent' : 'away_share_percent'])}</dd></div>
      </dl></div>)}
    </div>}
    <details className="mt-4 border-t border-[#c8d6c9] pt-3 text-sm">
      <summary className="cursor-pointer font-medium">{copy.goals} · {recap.goals.length}</summary>
      {recap.goals.length === 0 ? <p className="mt-3 text-[#53675b]">{copy.noGoals}</p> : <ol className="mt-2 divide-y divide-[#c8d6c9]">
        {recap.goals.map((goal) => {
          const team = goal.team_id === match.home_team.id ? match.home_team : match.away_team
          const player = team.players.find((item) => item.id === goal.player_id)!
          return <li key={goal.event_id} className="flex flex-wrap items-baseline gap-x-3 gap-y-1 py-2">
            <button type="button" aria-label={copy.inspectGoal(formatClock(goal.second))} onClick={() => onSeek(goal.second)} className="min-h-11 font-semibold tabular-nums underline decoration-[#205c41] underline-offset-4">{formatClock(goal.second)}</button>
            <span className="font-semibold tabular-nums">{goal.home_score}–{goal.away_score}</span>
            <span>{teamLabel(team.name)} · {playerLabel(player.name, team.name)}</span>
          </li>
        })}
      </ol>}
      <p className="mt-3 text-xs leading-5 text-[#53675b]">{copy.method}</p>
    </details>
  </section>
}
