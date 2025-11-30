'use client'
import { useState } from 'react'

import { useAuth } from '@/lib/auth/AuthContext'
import { useJobs } from '@/lib/context/JobContext'
import Link from 'next/link'
import { LogOut, User } from 'lucide-react'

export function UserMenu() {
  const { user, loading, signOut } = useAuth()

  if (loading) {
    return <div className="text-sm text-gray-500">Loading...</div>
  }

  if (!user) {
    return (
      <div className="flex items-center gap-3">
        <Link href="/login" className="text-sm hover:underline">
          Sign in
        </Link>
        <Link
          href="/signup"
          className="text-sm bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700"
        >
          Sign up
        </Link>
      </div>
    )
  }

  const { jobs, clearCompleted } = useJobs()
  const activeJobs = jobs.filter(j => j.status === 'queued' || j.status === 'processing')
  const [showJobs, setShowJobs] = useState(false)

  return (
    <div className="flex items-center gap-3 relative">
      {activeJobs.length > 0 && (
        <button
          onClick={() => setShowJobs(!showJobs)}
          className="flex items-center gap-2 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full border border-blue-200 animate-pulse hover:bg-blue-100 transition-colors"
        >
          <div className="w-2 h-2 bg-blue-500 rounded-full" />
          <span>{activeJobs.length} processing</span>
        </button>
      )}

      {showJobs && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-white rounded-md shadow-lg border border-neutral-200 p-2 z-50">
          <div className="text-xs font-semibold text-neutral-500 mb-2 px-2 flex justify-between items-center">
            <span>Active Jobs</span>
            <button onClick={clearCompleted} className="text-blue-600 hover:underline">Clear done</button>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {jobs.map(job => (
              <div key={job.id} className="flex items-center gap-2 p-2 rounded hover:bg-neutral-50 text-xs">
                {job.thumbnail && (
                  <img src={job.thumbnail} alt="" className="w-8 h-8 object-cover rounded" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="truncate font-medium">{job.filename || 'Image'}</div>
                  <div className={`capitalize ${job.status === 'failed' ? 'text-red-600' : 'text-neutral-500'}`}>
                    {job.status}
                  </div>
                </div>
              </div>
            ))}
            {jobs.length === 0 && <div className="text-center text-neutral-400 py-2">No jobs</div>}
          </div>
        </div>
      )}
      <div className="flex items-center gap-2 text-sm text-gray-700">
        <User className="w-4 h-4" />
        <span>{user.email}</span>
      </div>
      <button
        onClick={signOut}
        className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
        title="Sign out"
      >
        <LogOut className="w-4 h-4" />
        <span>Sign out</span>
      </button>
    </div>
  )
}
