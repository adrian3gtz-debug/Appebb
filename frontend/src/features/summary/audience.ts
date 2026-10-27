export type Audience = 'fan' | 'analyst'
const storageKey = 'fil-audience'

export function initialAudience(): Audience {
  try { return localStorage.getItem(storageKey) === 'analyst' ? 'analyst' : 'fan' }
  catch { return 'fan' }
}

export function saveAudience(audience: Audience): void {
  try { localStorage.setItem(storageKey, audience) } catch { /* In-memory selection still works. */ }
}
