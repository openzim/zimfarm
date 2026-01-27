/**
 * Classifies YouTube IDs and generates corresponding YouTube URLs.
 *
 * This is a heuristic-based approach since YouTube ID formats
 * are not officially documented.
 *
 * References:
 * - https://stackoverflow.com/questions/19795987/youtube-channel-and-playlist-id-prefixes
 */

export type YoutubeLinkKind = 'channel' | 'playlist' | 'video' | 'handle' | 'unknown'

export interface YoutubeLinkItem {
  raw: string
  kind: YoutubeLinkKind
  url?: string
}

function classifyYoutubeId(raw: string): YoutubeLinkItem {
  const value = raw.trim()
  if (!value) return { raw, kind: 'unknown' }

  // Handle YouTube handles (e.g., @channelname)
  if (value.startsWith('@')) {
    return { raw, kind: 'handle', url: `https://www.youtube.com/${value}` }
  }

  // Channel IDs typically start with "UC"
  if (value.startsWith('UC')) {
    return { raw, kind: 'channel', url: `https://www.youtube.com/channel/${value}` }
  }

  // Playlist IDs typically start with these prefixes
  const playlistPrefixes = ['PL', 'RD', 'UU', 'LL', 'FL', 'WL']
  if (playlistPrefixes.some((prefix) => value.startsWith(prefix))) {
    return { raw, kind: 'playlist', url: `https://www.youtube.com/playlist?list=${value}` }
  }

  // Video IDs are typically 11 characters long
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
