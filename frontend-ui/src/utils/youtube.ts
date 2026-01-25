export interface YouTubeLink {
  id: string
  url: string
}

/**
 * Generates YouTube URLs from various ID formats.
 * Handles:
 * - Channel IDs (UC...)
 * - Usernames/Handles (@...)
 * - Playlist IDs (PL...)
 * - Comma-separated lists of the above
 *
 * @param input The input string containing one or more identifiers
 * @returns An array of YouTubeLink objects
 */
export const getYouTubeUrls = (input: string | null | undefined): YouTubeLink[] => {
  if (!input || typeof input !== 'string') {
    return []
  }

  // Split by comma or whitespace to handle multiple IDs
  const parts = input.split(/[\s,]+/).filter((part) => part.trim().length > 0)
  const links: YouTubeLink[] = []

  for (const part of parts) {
    const id = part.trim()
    let url = ''

    if (id.startsWith('UC')) {
      // Channel ID
      url = `https://www.youtube.com/channel/${id}`
    } else if (id.startsWith('@')) {
      // Handle / Username
      url = `https://www.youtube.com/@${id.substring(1)}`
    } else if (id.startsWith('PL')) {
      // Playlist ID
      url = `https://www.youtube.com/playlist?list=${id}`
    } else {
      // Fallback: Assume it's a channel ID or username without @?
      // Or maybe a video ID?
      // For safety, if it looks like a handle (starts with word char), treat as handle if we want?
      // But purely alphanumeric could be channel ID too.
      // Reviewer asked to ensure "valid YouTube context".
      // If we are unsure, maybe we shouldn't link it, or link to search?
      // Given the requirement "Ensure the helper logic doesn’t break or produce invalid URLs",
      // let's stick to known prefixes if possible.
      // However, the PR description says "various ID formats".
      // Let's assume common formats.
      if (id.length > 0) {
        if (id.length === 24 && id.startsWith('U')) {
             // Likely a channel ID (e.g. UCxxxxxxxx) - mostly covered by UC check, but just in case
             url = `https://www.youtube.com/channel/${id}`
        } else {
            // Assume it is a handle if it doesn't match others?
            // Or maybe a channel custom URL?
            // Let's treat as handle but prepend @ if missing?
            // "zimfarm" -> https://www.youtube.com/@zimfarm
            url = `https://www.youtube.com/@${id}`
        }
      }
    }

    if (url) {
      links.push({ id, url })
    }
  }

  return links
}
