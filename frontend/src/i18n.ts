export type Language = 'en' | 'es'

const storageKey = 'fil-language'

export const translations = {
  en: {
    languageLabel: 'Language',
    checking: 'Checking connection',
    connected: 'API connected',
    unavailable: 'API unavailable',
    headline: 'Football, explained through data.',
    introduction: 'A place to follow the match, explore its events, and understand what the data shows.',
    replayTitle: 'Match replay',
    syntheticNotice: 'Synthetic test match with fictional teams. This is a recorded sequence, not a live match.',
    loading: 'Loading match…', loadError: 'Could not load the match. Check that the backend is running on port 8000.', retry: 'Try again',
    play: 'Play', pause: 'Pause', reset: 'Restart', speed: 'Speed',
    firstHalf: 'First half', secondHalf: 'Second half', finished: 'Full time',
    paused: 'Paused', playing: 'Playing', progress: 'Match progress',
    latestEvents: 'Latest events', noEvents: 'Press Play to see the first events.',
    demoHelp: 'At 60×, 90 match minutes take 90 seconds. Restart returns to kickoff and pauses playback.',
    events: { pass: 'Pass', carry: 'Carry', recovery: 'Recovery', pressure: 'Pressure', shot: 'Shot' },
    outcomes: { complete: 'Completed', incomplete: 'Incomplete', goal: 'Goal', saved: 'Saved', off_target: 'Off target', blocked: 'Blocked' },
  },
  es: {
    languageLabel: 'Idioma',
    checking: 'Comprobando conexión',
    connected: 'API conectada',
    unavailable: 'API sin conexión',
    headline: 'El fútbol, explicado con datos.',
    introduction: 'Un espacio para seguir el partido, explorar sus eventos y entender qué muestran los datos.',
    replayTitle: 'Reproducción del partido',
    syntheticNotice: 'Partido sintético de prueba con equipos ficticios. Es una secuencia grabada, no un partido en directo.',
    loading: 'Cargando partido…', loadError: 'No se pudo cargar el partido. Comprueba que el backend esté ejecutándose en el puerto 8000.', retry: 'Reintentar',
    play: 'Iniciar', pause: 'Pausar', reset: 'Reiniciar', speed: 'Velocidad',
    firstHalf: 'Primer tiempo', secondHalf: 'Segundo tiempo', finished: 'Final del partido',
    paused: 'En pausa', playing: 'Reproduciendo', progress: 'Progreso del partido',
    latestEvents: 'Últimos eventos', noEvents: 'Pulsa Iniciar para ver los primeros eventos.',
    demoHelp: 'A 60×, los 90 minutos del partido duran 90 segundos. Reiniciar vuelve al comienzo y pausa la reproducción.',
    events: { pass: 'Pase', carry: 'Conducción', recovery: 'Recuperación', pressure: 'Presión', shot: 'Tiro' },
    outcomes: { complete: 'Completado', incomplete: 'Incompleto', goal: 'Gol', saved: 'Atajado', off_target: 'Fuera de portería', blocked: 'Bloqueado' },
  },
} as const

export function initialLanguage(): Language {
  const saved = localStorage.getItem(storageKey)
  if (saved === 'en' || saved === 'es') return saved

  return navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en'
}

export function saveLanguage(language: Language): void {
  localStorage.setItem(storageKey, language)
}
