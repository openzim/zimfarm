export function stringArrayEqual(a: string[], b: string[]): boolean {
  // shallow comparison of string arrays
  return JSON.stringify([...a].sort()) === JSON.stringify([...b].sort())
}
