'use client'

import { useAuth } from '@/lib/auth/AuthContext'
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

  return (
    <div className="flex items-center gap-3">
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
