export type AIProvider = 'azure_openai' | 'groq'

export function isAIProvider(value: unknown): value is AIProvider {
  return value === 'azure_openai' || value === 'groq'
}

export function providerLabel(provider: AIProvider): string {
  return provider === 'groq' ? 'Groq' : 'Microsoft Foundry'
}
