import { describe, it, expect } from 'vitest'
import { generateYouTubeUrl, generateYouTubeUrls } from '../youtube'

describe('YouTube URL Generation', () => {
  describe('generateYouTubeUrl', () => {
    it('should generate channel URL for UC channel ID', () => {
      const id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
      const url = generateYouTubeUrl(id)
      expect(url).toBe(`https://www.youtube.com/channel/${id}`)
    })

    it('should generate channel URL for HC channel ID', () => {
      const id = 'HC_x5XG1OV2P6uZZ5FSM9Ttw'
      const url = generateYouTubeUrl(id)
      expect(url).toBe(`https://www.youtube.com/channel/${id}`)
    })

    it('should generate playlist URL for PL playlist ID', () => {
      const id = 'PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N'
      const url = generateYouTubeUrl(id)
      expect(url).toBe(`https://www.youtube.com/playlist?list=${id}`)
    })

    it('should generate video URL for 11-character video ID', () => {
      const id = 'dQw4w9WgXcQ'
      const url = generateYouTubeUrl(id)
      expect(url).toBe(`https://www.youtube.com/watch?v=${id}`)
    })

    it('should generate handle URL for @handle', () => {
      const id = '@channelname'
      const url = generateYouTubeUrl(id)
      expect(url).toBe(`https://www.youtube.com/${id}`)
    })

    it('should return null for empty string', () => {
      const url = generateYouTubeUrl('')
      expect(url).toBeNull()
    })

    it('should return null for null/undefined', () => {
      expect(generateYouTubeUrl(null as any)).toBeNull()
      expect(generateYouTubeUrl(undefined as any)).toBeNull()
    })

    it('should default to channel URL for unknown format', () => {
      const id = 'some-custom-id'
      const url = generateYouTubeUrl(id)
      expect(url).toBe(`https://www.youtube.com/channel/${id}`)
    })
  })

  describe('generateYouTubeUrls', () => {
    it('should handle single ID', () => {
      const ids = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
      const urls = generateYouTubeUrls(ids)
      expect(urls).toHaveLength(1)
      expect(urls[0].id).toBe(ids)
      expect(urls[0].url).toBe(`https://www.youtube.com/channel/${ids}`)
    })

    it('should handle multiple comma-separated IDs', () => {
      const ids = 'UC_x5XG1OV2P6uZZ5FSM9Ttw,PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N'
      const urls = generateYouTubeUrls(ids)
      expect(urls).toHaveLength(2)
      expect(urls[0].id).toBe('UC_x5XG1OV2P6uZZ5FSM9Ttw')
      expect(urls[1].id).toBe('PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N')
    })

    it('should trim whitespace from IDs', () => {
      const ids = ' UC_x5XG1OV2P6uZZ5FSM9Ttw , PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N '
      const urls = generateYouTubeUrls(ids)
      expect(urls).toHaveLength(2)
      expect(urls[0].id).toBe('UC_x5XG1OV2P6uZZ5FSM9Ttw')
      expect(urls[1].id).toBe('PLrAXtmRdnEQy6nuLMH1F-dN9D-t5F1N4N')
    })

    it('should return empty array for empty string', () => {
      const urls = generateYouTubeUrls('')
      expect(urls).toEqual([])
    })

    it('should return empty array for invalid input', () => {
      expect(generateYouTubeUrls(null as any)).toEqual([])
      expect(generateYouTubeUrls(undefined as any)).toEqual([])
    })
  })
})

