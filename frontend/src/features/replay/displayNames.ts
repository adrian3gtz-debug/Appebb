// The surrounding match notice identifies the data as synthetic once.
export function teamLabel(name: string): string {
  return name.replace(/\s*\(synthetic\)$/, '')
}

export function playerLabel(name: string, teamName: string): string {
  const prefix = `${teamName} `
  const number = name.startsWith(prefix) ? name.slice(prefix.length) : ''
  return /^\d+$/.test(number) ? `#${number}` : name
}
