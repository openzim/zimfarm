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

function isYoutubeHost(hostname: string) {
  return hostname.endsWith('youtube.com') || hostname.endsWith('youtube-nocookie.com')
}

function extractPathId(path: string, prefix: string) {
  return path.startsWith(prefix) ? path.replace(prefix, '').split('/')[0] : null
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
    return id ? { raw, kind: 'video', url: `https://youtu.be/${id}` } : null
  }

  if (!isYoutubeHost(hostname)) return null

  if (pathname.startsWith('/watch')) {
    const id = url.searchParams.get('v')
    return id ? { raw, kind: 'video', url: `https://www.youtube.com/watch?v=${id}` } : null
  }

  if (pathname.startsWith('/playlist')) {
    const id = url.searchParams.get('list')
    return id ? { raw, kind: 'playlist', url: `https://www.youtube.com/playlist?list=${id}` } : null
  }

  const channelId = extractPathId(pathname, '/channel/')
  if (channelId) {
    return { raw, kind: 'channel', url: `https://www.youtube.com/channel/${channelId}` }
  }

  const userId = extractPathId(pathname, '/user/') || extractPathId(pathname, '/c/')
  if (userId) {
    return { raw, kind: 'user', url: `https://www.youtube.com/c/${userId}` }
  }

  if (pathname.startsWith('/@')) {
    const handle = pathname.split('/')[1]
    return handle ? { raw, kind: 'handle', url: `https://www.youtube.com/@${handle}` } : null
  }

  const shortId = extractPathId(pathname, '/shorts/')
  if (shortId) return { raw, kind: 'video', url: `https://www.youtube.com/watch?v=${shortId}` }

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
