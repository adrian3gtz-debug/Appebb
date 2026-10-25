// Vite embeds this public URL at build time. Empty uses the local development proxy.
export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/+$/, '')
