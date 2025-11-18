'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth/AuthContext'
import { createClient } from '@/lib/supabase/client'
import Link from 'next/link'
import { Eye, EyeOff, Trash2, Lock, Globe } from 'lucide-react'

interface Image {
  id: string
  caption: string
  visibility: string
  created_at: string
  thumbnail_url?: string
  download_url?: string
}

export default function LibraryPage() {
  const { user, loading: authLoading } = useAuth()
  const [images, setImages] = useState<Image[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'private' | 'public'>('all')

  useEffect(() => {
    if (!authLoading && user) {
      loadImages()
    } else if (!authLoading && !user) {
      setLoading(false)
    }
  }, [user, authLoading, filter])

  async function loadImages() {
    try {
      setLoading(true)
      setError(null)
      
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token
      
      if (!token) {
        setError('Please log in to view your library')
        setLoading(false)
        return
      }
      
      const params = new URLSearchParams({
        limit: '50',
        offset: '0'
      })
      
      if (filter !== 'all') {
        params.set('visibility', filter)
      }
      
      const res = await fetch(`/api/images?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
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

  async function updateVisibility(imageId: string, newVisibility: 'private' | 'public') {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token
      
      if (!token) return
      
      const res = await fetch(`/api/images/${imageId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ visibility: newVisibility })
      })
      
      if (!res.ok) {
        throw new Error('Failed to update visibility')
      }
      
      // Reload images
      await loadImages()
    } catch (err: any) {
      alert(err.message || 'Failed to update visibility')
    }
  }

  async function deleteImage(imageId: string) {
    if (!confirm('Are you sure you want to delete this image?')) {
      return
    }
    
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token
      
      if (!token) return
      
      const res = await fetch(`/api/images/${imageId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!res.ok) {
        throw new Error('Failed to delete image')
      }
      
      // Reload images
      await loadImages()
    } catch (err: any) {
      alert(err.message || 'Failed to delete image')
    }
  }

  if (authLoading || loading) {
    return (
      <main className="space-y-6">
        <h1 className="text-xl font-semibold">My Library</h1>
        <div className="text-sm text-gray-500">Loading...</div>
      </main>
    )
  }

  if (!user) {
    return (
      <main className="space-y-6">
        <h1 className="text-xl font-semibold">My Library</h1>
        <div className="rounded-md bg-yellow-50 p-4">
          <p className="text-sm text-yellow-800">
            Please <Link href="/login" className="underline">log in</Link> to view your library.
          </p>
        </div>
      </main>
    )
  }

  return (
    <main className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">My Library</h1>
        <Link
          href="/upload"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
        >
          Upload Image
        </Link>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-gray-700">Filter:</span>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 text-sm rounded-md ${
              filter === 'all'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('private')}
            className={`px-3 py-1 text-sm rounded-md ${
              filter === 'private'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Private
          </button>
          <button
            onClick={() => setFilter('public')}
            className={`px-3 py-1 text-sm rounded-md ${
              filter === 'public'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Public
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {images.length === 0 ? (
        <div className="rounded-md border border-gray-200 p-8 text-center">
          <p className="text-sm text-gray-600">
            No images found. <Link href="/upload" className="text-blue-600 hover:underline">Upload your first image</Link>
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {images.map((image) => (
            <div key={image.id} className="rounded-md border border-gray-200 overflow-hidden">
              <Link href={`/image/${image.id}`}>
                {image.thumbnail_url ? (
                  <img
                    src={image.thumbnail_url}
                    alt={image.caption}
                    className="w-full h-48 object-cover hover:opacity-90 transition-opacity"
                  />
                ) : (
                  <div className="w-full h-48 bg-gray-100 flex items-center justify-center">
                    <span className="text-gray-400 text-sm">No preview</span>
                  </div>
                )}
              </Link>
              <div className="p-3 space-y-2">
                <p className="text-sm text-gray-700 line-clamp-2">{image.caption}</p>
                <div className="flex items-center gap-2">
                  {image.visibility === 'private' ? (
                    <span className="flex items-center gap-1 text-xs text-gray-600">
                      <Lock className="w-3 h-3" />
                      Private
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-gray-600">
                      <Globe className="w-3 h-3" />
                      Public
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <button
                    onClick={() => updateVisibility(
                      image.id,
                      image.visibility === 'private' ? 'public' : 'private'
                    )}
                    className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                    title={image.visibility === 'private' ? 'Make public' : 'Make private'}
                  >
                    {image.visibility === 'private' ? (
                      <>
                        <Eye className="w-3 h-3" />
                        Make Public
                      </>
                    ) : (
                      <>
                        <EyeOff className="w-3 h-3" />
                        Make Private
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => deleteImage(image.id)}
                    className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700"
                    title="Delete image"
                  >
                    <Trash2 className="w-3 h-3" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
