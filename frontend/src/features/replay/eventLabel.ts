import { translations } from '../../i18n'
import type { Language } from '../../i18n'
import type { MatchEvent } from '../../types/match'

export function eventLabel(event: MatchEvent, language: Language): string {
  const copy = translations[language]
  if (event.type === 'pass' && event.pass_context && event.pass_context !== 'open_play') {
    return copy.passContexts[event.pass_context]
  }
  return copy.events[event.type]
}
