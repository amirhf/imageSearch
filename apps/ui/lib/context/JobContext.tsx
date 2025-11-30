"use client"
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { getJobStatus } from '@/lib/api'
import { useRouter } from 'next/navigation'

export interface Job {
    id: string
    status: 'queued' | 'processing' | 'completed' | 'failed'
    filename?: string
    thumbnail?: string // Data URL or path
    error?: string
    result?: any
    submittedAt: number
}

interface JobContextType {
    jobs: Job[]
    addJob: (jobId: string, metadata?: { filename?: string, thumbnail?: string }) => void
    removeJob: (jobId: string) => void
    clearCompleted: () => void
}

const JobContext = createContext<JobContextType | undefined>(undefined)

export function JobProvider({ children }: { children: ReactNode }) {
    const [jobs, setJobs] = useState<Job[]>([])
    const router = useRouter()

    // Load jobs from localStorage on mount
    useEffect(() => {
        const saved = localStorage.getItem('image_search_jobs')
        if (saved) {
            try {
                setJobs(JSON.parse(saved))
            } catch (e) {
                console.error("Failed to parse jobs", e)
            }
        }
    }, [])

    // Save jobs to localStorage on change
    useEffect(() => {
        localStorage.setItem('image_search_jobs', JSON.stringify(jobs))
    }, [jobs])

    // Poll for active jobs
    useEffect(() => {
        const activeJobs = jobs.filter(j => j.status === 'queued' || j.status === 'processing')
        if (activeJobs.length === 0) return

        const interval = setInterval(async () => {
            for (const job of activeJobs) {
                try {
                    const status = await getJobStatus(job.id)

                    if (status.status !== job.status) {
                        setJobs(prev => prev.map(j =>
                            j.id === job.id
                                ? { ...j, status: status.status as any, error: status.error, result: status.result }
                                : j
                        ))

                        // If completed, we can trigger a toast or something
                        if (status.status === 'completed') {
                            console.log(`Job ${job.id} completed!`)
                        }
                    }
                } catch (e) {
                    console.error(`Failed to poll job ${job.id}`, e)
                }
            }
        }, 2000) // Poll every 2s

        return () => clearInterval(interval)
    }, [jobs])

    const addJob = (jobId: string, metadata?: { filename?: string, thumbnail?: string }) => {
        setJobs(prev => [...prev, {
            id: jobId,
            status: 'queued',
            submittedAt: Date.now(),
            filename: metadata?.filename,
            thumbnail: metadata?.thumbnail
        }])
    }

    const removeJob = (jobId: string) => {
        setJobs(prev => prev.filter(j => j.id !== jobId))
    }

    const clearCompleted = () => {
        setJobs(prev => prev.filter(j => j.status !== 'completed' && j.status !== 'failed'))
    }

    return (
        <JobContext.Provider value={{ jobs, addJob, removeJob, clearCompleted }}>
            {children}
        </JobContext.Provider>
    )
}

export function useJobs() {
    const context = useContext(JobContext)
    if (context === undefined) {
        throw new Error('useJobs must be used within a JobProvider')
    }
    return context
}
