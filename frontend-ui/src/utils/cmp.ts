import Fuse from "fuse.js"

export function stringArrayEqual(a: string[], b: string[]): boolean {
  // shallow comparison of string arrays
  return JSON.stringify([...a].sort()) === JSON.stringify([...b].sort())
}

export const fuzzyFilter = (value: string, query: string, items: string[]) => {
  const fuse = new Fuse(items, {
    includeScore: true,
    threshold: 0.3,
  })
  const results = fuse.search(query).find(r => r.item == value)
  return !!results
}
