export type YoutubeLinkKind = 'channel' | 'playlist' | 'video' | 'handle' | 'user' | 'unknown'

export interface YoutubeLinkItem {
  raw: string
  kind: YoutubeLinkKind
  url?: string
}

const playlistPrefixes = ['PL', 'RD', 'UU', 'LL', 'FL', 'WL']

function normalizeYoutubeUrlCandidate(value: string) {
  if (/^[a-z]+:\/\//i.test(value)) return value
  if (value.startsWith('www.')) return `https://${value}`
  if (value.includes('youtube.com') || value.includes('youtu.be')) return `https://${value}`
  return value
}

function parseYoutubeUrl(raw: string): YoutubeLinkItem | null {
  const normalized = normalizeYoutubeUrlCandidate(raw)
  if (!/^[a-z]+:\/\//i.test(normalized)) return null

  let url: URL
  try {
    url = new URL(normalized)
  } catch {
    return null
  }

  const hostname = url.hostname.toLowerCase()
  const pathname = url.pathname || ''

  if (hostname === 'youtu.be') {
    const id = pathname.replace(/^\/+/, '').split('/')[0]
    if (!id) return null
    return { raw, kind: 'video', url: `https://youtu.be/${id}` }
  }

  if (!hostname.endsWith('youtube.com') && !hostname.endsWith('youtube-nocookie.com')) {
    return null
  }

  if (pathname.startsWith('/watch')) {
    const id = url.searchParams.get('v')
    if (!id) return null
    return { raw, kind: 'video', url: `https://www.youtube.com/watch?v=${id}` }
  }

  if (pathname.startsWith('/playlist')) {
    const id = url.searchParams.get('list')
    if (!id) return null
    return { raw, kind: 'playlist', url: `https://www.youtube.com/playlist?list=${id}` }
  }

  if (pathname.startsWith('/channel/')) {
    const id = pathname.replace('/channel/', '').split('/')[0]
    if (!id) return null
    return { raw, kind: 'channel', url: `https://www.youtube.com/channel/${id}` }
  }

  if (pathname.startsWith('/user/')) {
    const id = pathname.replace('/user/', '').split('/')[0]
    if (!id) return null
    return { raw, kind: 'user', url: `https://www.youtube.com/user/${id}` }
  }

  if (pathname.startsWith('/c/')) {
    const id = pathname.replace('/c/', '').split('/')[0]
    if (!id) return null
    return { raw, kind: 'user', url: `https://www.youtube.com/c/${id}` }
  }

  if (pathname.startsWith('/@')) {
    const handle = pathname.split('/')[1]
    if (!handle) return null
    return { raw, kind: 'handle', url: `https://www.youtube.com/@${handle}` }
  }

  if (pathname.startsWith('/shorts/')) {
    const id = pathname.replace('/shorts/', '').split('/')[0]
    if (!id) return null
    return { raw, kind: 'video', url: `https://www.youtube.com/watch?v=${id}` }
  }

  return null
}

function classifyYoutubeId(raw: string): YoutubeLinkItem {
  const value = raw.trim()
  if (!value) return { raw, kind: 'unknown' }

  const urlMatch = parseYoutubeUrl(value)
  if (urlMatch) return urlMatch

  if (value.startsWith('@')) {
    return { raw, kind: 'handle', url: `https://www.youtube.com/${value}` }
  }

  if (value.startsWith('UC')) {
    return { raw, kind: 'channel', url: `https://www.youtube.com/channel/${value}` }
  }

  if (playlistPrefixes.some((prefix) => value.startsWith(prefix))) {
    return { raw, kind: 'playlist', url: `https://www.youtube.com/playlist?list=${value}` }
  }

  if (value.length === 11) {
    return { raw, kind: 'video', url: `https://www.youtube.com/watch?v=${value}` }
  }

  return { raw, kind: 'unknown' }
}

export function buildYoutubeLinks(input: string): YoutubeLinkItem[] {
  if (!input) return []
  return input
    .split(',')
    .map((value) => value.trim())
    .filter((value) => value.length > 0)
    .map((value) => classifyYoutubeId(value))
}
