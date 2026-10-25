import type { KeyboardEvent } from 'react'
import type { Language } from '../../i18n'
import type { MatchEvent } from '../../types/match'
import type { RecoverySequence } from '../../types/recoveries'
import { recoveryCopy } from './copy'

interface Props {
  sequences: RecoverySequence[]
  events: Map<string, MatchEvent>
  selected: RecoverySequence | undefined
  attacksRight: boolean
  language: Language
  onSelect: (id: string) => void
}

const x = (value: number) => value + 5
const y = (value: number) => value * 0.64 + 5

export function RecoveryPitch({ sequences, events, selected, attacksRight, language, onSelect }: Props) {
  const copy = recoveryCopy[language]
  const chain = selected?.event_ids.map((id) => events.get(id)!).filter(Boolean) ?? []
  function selectWithKey(event: KeyboardEvent<SVGGElement>, id: string) {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(id) }
  }
  return <>
    <p className="mb-2 text-right text-sm font-medium text-[#205c41]">{attacksRight ? copy.attackRight : copy.attackLeft}</p>
    <svg viewBox="0 0 110 74" role="group" aria-label={copy.pitch} className="w-full rounded-xl bg-[#286348]">
      <rect x={attacksRight ? 5 + 200 / 3 : 5} y="5" width={100 / 3} height="64" fill="#77ad88" opacity="0.35" />
      <g fill="none" stroke="#e5eee4" strokeWidth="0.35" aria-hidden="true">
        <rect x="5" y="5" width="100" height="64" />
        <line x1="55" y1="5" x2="55" y2="69" />
        <circle cx="55" cy="37" r="9" />
        <rect x="5" y="17" width="16" height="40" />
        <rect x="89" y="17" width="16" height="40" />
        <rect x="5" y="28" width="6" height="18" />
        <rect x="99" y="28" width="6" height="18" />
      </g>
      {chain.map((event) => (event.type === 'pass' || event.type === 'carry') && (
        <g key={event.id} aria-hidden="true">
          <line x1={x(event.location.x)} y1={y(event.location.y)} x2={x(event.end_location.x)} y2={y(event.end_location.y)} stroke={event.type === 'carry' ? '#fbd382' : '#ffffff'} strokeWidth="0.65" strokeDasharray={event.type === 'carry' ? '1.2 1' : undefined} />
          <circle cx={x(event.end_location.x)} cy={y(event.end_location.y)} r="0.8" fill={event.type === 'carry' ? '#fbd382' : '#ffffff'} />
        </g>
      ))}
      {chain.filter((event) => event.type === 'shot').map((event) => (
        <path key={event.id} d={`M ${x(event.location.x)-1.4} ${y(event.location.y)-1.4} l 2.8 2.8 m 0 -2.8 l -2.8 2.8`} stroke="#fbd382" strokeWidth="0.8" aria-hidden="true" />
      ))}
      {sequences.map((sequence) => {
        const event = events.get(sequence.recovery_event_id)!
        const active = selected?.recovery_event_id === event.id
        return <g key={event.id} role="button" tabIndex={0} aria-pressed={active} aria-label={`${copy.recovery} ${Math.floor(event.second / 60)}:${String(event.second % 60).padStart(2, '0')}`} onClick={() => onSelect(event.id)} onKeyDown={(key) => selectWithKey(key, event.id)} className="cursor-pointer focus:outline-2 focus:outline-white">
          <circle cx={x(event.location.x)} cy={y(event.location.y)} r="3.5" fill="transparent" />
          <circle cx={x(event.location.x)} cy={y(event.location.y)} r={active ? 1.8 : 1.2} fill={active ? '#fbd382' : '#e5eee4'} stroke="#19332a" strokeWidth="0.4" />
        </g>
      })}
    </svg>
    <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-[#53675b]" aria-hidden="true">
      <span>● {copy.recovery}</span><span>─ {copy.pass}</span><span>┄ {copy.carry}</span><span>× {copy.shot}</span>
    </div>
    <p className="mt-3 text-sm leading-6 text-[#53675b]">{copy.pitchHelp}</p>
  </>
}
