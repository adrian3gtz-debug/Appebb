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
    preparation: 'We are preparing the first synthetic match for this lab.',
    emptyTitle: 'No match on screen yet',
    emptyDescription: 'Events will appear here when we add the simulator.',
    connectionHelp: 'Start the backend on port 8000 and refresh the page.',
  },
  es: {
    languageLabel: 'Idioma',
    checking: 'Comprobando conexión',
    connected: 'API conectada',
    unavailable: 'API sin conexión',
    headline: 'El fútbol, explicado con datos.',
    introduction: 'Un espacio para seguir el partido, explorar sus eventos y entender qué muestran los datos.',
    preparation: 'Estamos preparando el primer partido sintético para este laboratorio.',
    emptyTitle: 'Todavía no hay un partido en pantalla',
    emptyDescription: 'Aquí aparecerán los eventos cuando incorporemos el simulador.',
    connectionHelp: 'Inicia el backend en el puerto 8000 y actualiza la página.',
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
