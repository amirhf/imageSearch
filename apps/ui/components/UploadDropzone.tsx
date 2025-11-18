"use client"
import { useState, useRef, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { uploadImage } from '@/lib/api'
import { useAuth } from '@/lib/auth/AuthContext'
import { createClient } from '@/lib/supabase/client'

export default function UploadDropzone() {
  const router = useRouter()
  const { user } = useAuth()
  const [url, setUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [visibility, setVisibility] = useState<'private' | 'public'>('private')
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState<number | null>(null) // 0-100 for file uploads
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!url && !file) {
      setError('Provide a URL or select a file')
      return
    }
    try {
      setLoading(true)
      
      // Get auth token
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token
      
      if (!token) {
        setError('You must be logged in to upload images')
        setLoading(false)
        return
      }
      
      // If a file is present, use XHR to track upload progress
      if (file) {
        const form = new FormData()
        form.set('file', file, file.name)
        if (url) form.set('url', url)
        form.set('visibility', visibility)

        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest()
          xhr.open('POST', '/api/images', true)
          xhr.setRequestHeader('Authorization', `Bearer ${token}`)
          xhr.upload.onprogress = (ev) => {
            if (ev.lengthComputable) {
              const pct = Math.round((ev.loaded / ev.total) * 100)
              setProgress(pct)
            }
          }
          xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
              try {
                if (xhr.status >= 200 && xhr.status < 300) {
                  const json = JSON.parse(xhr.responseText)
                  router.push(`/image/${json.id}`)
                  resolve()
                } else if (xhr.status === 401) {
                  reject(new Error('Authentication required. Please log in.'))
                } else if (xhr.status === 403) {
                  reject(new Error('You do not have permission to perform this action'))
                } else {
                  reject(new Error(`Upload failed: ${xhr.status}`))
                }
              } catch (err) {
                reject(err as Error)
              }
            }
          }
          xhr.onerror = () => reject(new Error('Network error during upload'))
          xhr.send(form)
        })
      } else {
        // URL-only: small payload; use fetch and show indeterminate progress UI
        setProgress(-1) // signal indeterminate
        const res = await uploadImage({ url, visibility }, token)
        router.push(`/image/${res.id}`)
      }
    } catch (err: any) {
      setError(err?.message || 'Upload failed')
    } finally {
      setLoading(false)
      setTimeout(() => setProgress(null), 500)
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) setFile(f)
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div
        className={`rounded-md border-2 border-dashed p-6 text-center ${dragOver ? 'border-neutral-600 bg-neutral-50' : 'border-neutral-300'}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
      >
        <div className="space-y-2">
          <div className="text-sm text-neutral-700">Drag & drop an image here</div>
          <div className="text-xs text-neutral-500">or</div>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="rounded-md border px-3 py-2 text-sm hover:bg-neutral-50"
          >
            Choose file
          </button>
          {file && (
            <div className="text-xs text-neutral-600">Selected: {file.name}</div>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          aria-label="File chooser"
        />
      </div>

      <div className="space-y-3">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Or paste image URL (Unsplash/COCO/etc)"
          className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 shadow-sm focus:outline-none"
          aria-label="Image URL"
          disabled={loading}
        />
        
        {/* Visibility Selector */}
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-neutral-700">Visibility:</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="visibility"
                value="private"
                checked={visibility === 'private'}
                onChange={(e) => setVisibility(e.target.value as 'private' | 'public')}
                disabled={loading}
                className="cursor-pointer"
              />
              <span className="text-sm text-neutral-700">Private</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="visibility"
                value="public"
                checked={visibility === 'public'}
                onChange={(e) => setVisibility(e.target.value as 'private' | 'public')}
                disabled={loading}
                className="cursor-pointer"
              />
              <span className="text-sm text-neutral-700">Public</span>
            </label>
          </div>
        </div>
        
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-neutral-900 px-4 py-2 text-white hover:bg-neutral-800 disabled:opacity-60"
        >
          {loading ? 'Uploading…' : 'Upload'}
        </button>
      </div>

      {progress !== null && (
        <div className="space-y-1" aria-live="polite" aria-atomic>
          <div className="h-2 w-full rounded bg-neutral-200">
            {progress >= 0 ? (
              <div
                className="h-2 rounded bg-neutral-900 transition-all"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={progress}
              />
            ) : (
              <div className="h-2 w-1/3 animate-pulse rounded bg-neutral-900" />
            )}
          </div>
          {progress >= 0 && <div className="text-xs text-neutral-600">{progress}%</div>}
        </div>
      )}

      {error && <div className="rounded-md border border-red-200 bg-red-50 p-3 text-red-700 text-sm">{error}</div>}
      <div className="text-xs text-neutral-500">Accepted: common image formats. Upload posts to the API and redirects to the image detail page.</div>
    </form>
  )
}
