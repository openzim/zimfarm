/**
 * Generates YouTube URLs from YouTube IDs
 * Supports channels, playlists, handles, users, and videos
 */

/**
 * Generates a YouTube URL for a given ID
 * @param id - YouTube ID (channel, playlist, handle, user, or video ID)
 * @returns YouTube URL or null if ID is invalid
 */
export function generateYouTubeUrl(id: string): string | null {
  if (!id || typeof id !== 'string') {
    return null
  }

  const trimmedId = id.trim()
  if (!trimmedId) {
    return null
  }

  // Handle format (starts with @) - check this first as it's unambiguous
  if (trimmedId.startsWith('@')) {
    return `https://www.youtube.com/${trimmedId}`
  }

  // Playlist IDs typically start with PL, FL, RD, etc. (at least 13 characters)
  // Common prefixes: PL (playlist), FL (favorites), RD (radio), UU (user uploads)
  if (/^(PL|FL|RD|UU|OL|LL)[a-zA-Z0-9_-]{11,}$/.test(trimmedId)) {
    return `https://www.youtube.com/playlist?list=${trimmedId}`
  }

  // Channel IDs typically start with UC, HC, etc. (exactly 24 characters)
  // UC = user channel, HC = legacy channel
  if (/^[UH]C[a-zA-Z0-9_-]{22}$/.test(trimmedId)) {
    return `https://www.youtube.com/channel/${trimmedId}`
  }

  // Video IDs are exactly 11 characters (alphanumeric, hyphens, underscores)
  if (/^[a-zA-Z0-9_-]{11}$/.test(trimmedId)) {
    return `https://www.youtube.com/watch?v=${trimmedId}`
  }

  // For other IDs, try channel format first (most common for YouTube recipe editor)
  // This handles custom channel names and other formats
  // If it doesn't work, user can still copy the ID and try manually
  return `https://www.youtube.com/channel/${trimmedId}`
}

/**
 * Generates YouTube URLs for multiple IDs (comma-separated)
 * @param ids - Comma-separated YouTube IDs
 * @returns Array of YouTube URLs
 */
export function generateYouTubeUrls(ids: string): Array<{ id: string; url: string }> {
  if (!ids || typeof ids !== 'string') {
    return []
  }

  return ids
    .split(',')
    .map((id) => id.trim())
    .filter((id) => id.length > 0)
    .map((id) => {
      const url = generateYouTubeUrl(id)
      return { id, url: url || '' }
    })
    .filter((item) => item.url !== '')
}

