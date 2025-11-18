'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Globe } from 'lucide-react'

interface Image {
  id: string
  caption: string
  visibility: string
  created_at: string
  thumbnail_url?: string
  download_url?: string
}

export default function ExplorePage() {
  const [images, setImages] = useState<Image[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPublicImages()
  }, [])

  async function loadPublicImages() {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams({
        limit: '50',
        offset: '0',
        visibility: 'public'
      })
      
      const res = await fetch(`/api/images?${params}`)
      
      if (!res.ok) {
        throw new Error(`Failed to load images: ${res.status}`)
      }
      
      const data = await res.json()
      setImages(data.images || [])
    } catch (err: any) {
      setError(err.message || 'Failed to load images')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="space-y-6">
        <h1 className="text-xl font-semibold">Explore Public Images</h1>
        <div className="text-sm text-gray-500">Loading...</div>
      </main>
    )
  }

  return (
    <main className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Explore Public Images</h1>
          <p className="text-sm text-gray-600 mt-1">
            Browse images shared by the community
          </p>
        </div>
        <Link
          href="/upload"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Upload Image
        </Link>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {images.length === 0 ? (
        <div className="rounded-md border border-gray-200 p-8 text-center">
          <p className="text-sm text-gray-600">
            No public images yet. Be the first to share!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {images.map((image) => (
            <Link
              key={image.id}
              href={`/image/${image.id}`}
              className="group rounded-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
            >
              {image.thumbnail_url ? (
                <img
                  src={image.thumbnail_url}
                  alt={image.caption}
                  className="w-full h-48 object-cover group-hover:opacity-90 transition-opacity"
                />
              ) : (
                <div className="w-full h-48 bg-gray-100 flex items-center justify-center">
                  <span className="text-gray-400 text-sm">No preview</span>
                </div>
              )}
              <div className="p-3 space-y-2">
                <p className="text-sm text-gray-700 line-clamp-2">{image.caption}</p>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <Globe className="w-3 h-3" />
                    Public
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
