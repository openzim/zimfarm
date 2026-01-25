import { describe, it, expect } from 'vitest'
import { getYouTubeUrls } from '../youtube'

describe('YouTube URL Generation', () => {
  describe('getYouTubeUrls', () => {
    it('should generate channel URL for UC channel ID', () => {
      const id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
      const links = getYouTubeUrls(id)
      expect(links).toHaveLength(1)
      expect(links[0].id).toBe(id)
      expect(links[0].url).toBe(`https://www.youtube.com/channel/${id}`)
    })

    it('should generate playlist URL for PL playlist ID', () => {
      const id = 'PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N'
      const links = getYouTubeUrls(id)
      expect(links).toHaveLength(1)
      expect(links[0].id).toBe(id)
      expect(links[0].url).toBe(`https://www.youtube.com/playlist?list=${id}`)
    })

    it('should generate handle URL for @handle', () => {
      const id = '@channelname'
      const links = getYouTubeUrls(id)
      expect(links).toHaveLength(1)
      expect(links[0].id).toBe(id)
      expect(links[0].url).toBe('https://www.youtube.com/@channelname')
    })

    it('should assume handle/custom URL for plain text', () => {
      const id = 'zimfarm'
      const links = getYouTubeUrls(id)
      expect(links).toHaveLength(1)
      expect(links[0].id).toBe(id)
      expect(links[0].url).toBe('https://www.youtube.com/@zimfarm')
    })

    it('should handle multiple comma-separated IDs', () => {
      const ids = 'UC_x5XG1OV2P6uZZ5FSM9Ttw,PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N'
      const links = getYouTubeUrls(ids)
      expect(links).toHaveLength(2)
      expect(links[0].id).toBe('UC_x5XG1OV2P6uZZ5FSM9Ttw')
      expect(links[0].url).toContain('channel')
      expect(links[1].id).toBe('PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N')
      expect(links[1].url).toContain('playlist')
    })

    it('should handle whitespace separated IDs', () => {
      const ids = 'UC_x5XG1OV2P6uZZ5FSM9Ttw PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N'
      const links = getYouTubeUrls(ids)
      expect(links).toHaveLength(2)
    })

    it('should return empty array for empty string', () => {
      const links = getYouTubeUrls('')
      expect(links).toEqual([])
    })

    it('should return empty array for null/undefined', () => {
      expect(getYouTubeUrls(null)).toEqual([])
      expect(getYouTubeUrls(undefined)).toEqual([])
    })
  })
})
