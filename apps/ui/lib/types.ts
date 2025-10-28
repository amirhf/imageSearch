export type ImageSummary = {
  id: string
  caption: string
  score?: number
  origin?: 'local' | 'cloud'
  confidence?: number
  thumbnail_url?: string
  download_url?: string
  width?: number
  height?: number
  format?: string
}

export type ImageDetail = ImageSummary & {
  payload?: Record<string, any>
  caption_local?: string
  caption_cloud?: string
  caption_origin?: 'local' | 'cloud'
  caption_confidence?: number
}

export type SearchResponse = {
  query: string
  results: ImageSummary[]
}
