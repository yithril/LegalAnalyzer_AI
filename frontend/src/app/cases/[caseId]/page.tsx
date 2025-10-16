"use client"

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { signOut, useSession } from 'next-auth/react'
import { casesApi } from '@/lib/api/cases'
import { theme, cn } from '@/lib/theme'
import type { Case } from '@/types/case'
import DocumentUpload from '@/components/cases/DocumentUpload'
import DocumentQueue from '@/components/cases/DocumentQueue'
import PlaceholderTab from '@/components/cases/PlaceholderTab'

type TabId = 'upload' | 'queue' | 'timeline' | 'personages' | 'ai' | 'search'

interface Tab {
  id: TabId
  label: string
  icon: React.ReactNode
}

const tabs: Tab[] = [
  {
    id: 'upload',
    label: 'Upload Documents',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
  },
  {
    id: 'queue',
    label: 'Document Queue',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    id: 'timeline',
    label: 'Timeline',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 'personages',
    label: 'Personages',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    id: 'ai',
    label: 'Ask AI',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
  },
  {
    id: 'search',
    label: 'Keyword Search',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
]

export default function CaseDashboardPage() {
  const params = useParams()
  const router = useRouter()
  const { data: session } = useSession()
  const caseId = parseInt(params.caseId as string)
  
  const [currentCase, setCurrentCase] = useState<Case | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabId>('upload')
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  
  // Load case details
  useEffect(() => {
    const loadCase = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const caseData = await casesApi.get(caseId)
        setCurrentCase(caseData)
      } catch (err: any) {
        setError(err.message || 'Failed to load case')
        console.error('Error loading case:', err)
      } finally {
        setIsLoading(false)
      }
    }
    
    if (caseId) {
      loadCase()
    }
  }, [caseId])
  
  const handleUploadComplete = () => {
    // Trigger refresh of document queue
    setRefreshTrigger(prev => prev + 1)
    // Switch to queue tab to see the uploaded document
    setActiveTab('queue')
  }
  
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading case...</p>
        </div>
      </div>
    )
  }
  
  if (error || !currentCase) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Case Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'The requested case could not be found.'}</p>
          <button
            onClick={() => router.push('/cases')}
            className={cn(
              'px-6 py-3 rounded-lg font-semibold',
              theme.components.button.primary
            )}
          >
            Back to Cases
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Top Navbar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
        <div className="px-6">
          <div className="flex justify-between items-center h-16">
            {/* Left: Breadcrumb */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/cases')}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <div className="flex items-center gap-2 text-sm">
                <button
                  onClick={() => router.push('/cases')}
                  className="text-gray-500 hover:text-gray-700 transition-colors"
                >
                  Cases
                </button>
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <span className="font-semibold text-gray-900">{currentCase.name}</span>
              </div>
            </div>
            
            {/* Right: User & Logout */}
            <div className="flex items-center gap-4">
              <div className="text-sm text-right">
                <p className="font-medium text-gray-900">{session?.user?.name}</p>
                <p className="text-gray-500">{session?.user?.email}</p>
              </div>
              
              <button
                onClick={() => signOut({ callbackUrl: '/login' })}
                className={cn(
                  'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                  theme.components.button.ghost
                )}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Layout: Sidebar + Content */}
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-4rem)] sticky top-16">
          <div className="p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
              Navigation
            </h2>
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700 shadow-sm'
                      : 'text-gray-700 hover:bg-gray-100'
                  )}
                >
                  <span className={activeTab === tab.id ? 'text-primary-600' : 'text-gray-500'}>
                    {tab.icon}
                  </span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
          
          {/* Case Info */}
          <div className="p-4 border-t border-gray-200 mt-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Case Details
            </h3>
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-sm font-medium text-gray-900 mb-1">{currentCase.name}</p>
              {currentCase.description && (
                <p className="text-xs text-gray-600 line-clamp-3">{currentCase.description}</p>
              )}
            </div>
          </div>
        </aside>
        
        {/* Main Content Area */}
        <main className="flex-1 p-8">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Upload Documents Tab */}
            {activeTab === 'upload' && (
              <DocumentUpload caseId={caseId} onUploadComplete={handleUploadComplete} />
            )}
            
            {/* Document Queue Tab */}
            {activeTab === 'queue' && (
              <DocumentQueue caseId={caseId} refreshTrigger={refreshTrigger} />
            )}
            
            {/* Timeline Tab - Placeholder */}
            {activeTab === 'timeline' && (
              <PlaceholderTab
                title="Timeline of Events"
                description="Chronological view of events extracted from your documents"
                icon={
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
                features={[
                  'Automatic date extraction from documents',
                  'Visual timeline with key events',
                  'Filter by date range and event type',
                  'Link events to source documents',
                  'Export timeline to PDF or Excel',
                ]}
              />
            )}
            
            {/* Personages Tab - Placeholder */}
            {activeTab === 'personages' && (
              <PlaceholderTab
                title="Personages"
                description="People and entities mentioned in your documents"
                icon={
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                }
                features={[
                  'Named Entity Recognition (NER) for people and organizations',
                  'Relationship mapping between entities',
                  'Role identification (plaintiff, defendant, witness, etc.)',
                  'Contact information extraction',
                  'View all documents mentioning each person',
                ]}
              />
            )}
            
            {/* Ask AI Tab - Placeholder */}
            {activeTab === 'ai' && (
              <PlaceholderTab
                title="Ask AI"
                description="Chat with AI about your case documents using RAG (Retrieval Augmented Generation)"
                icon={
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                }
                features={[
                  'Natural language questions about your case',
                  'AI-powered answers with source citations',
                  'Context-aware responses based on your documents',
                  'Chat history and conversation management',
                  'Export Q&A sessions for reports',
                ]}
              />
            )}
            
            {/* Search Tab - Placeholder */}
            {activeTab === 'search' && (
              <PlaceholderTab
                title="Keyword Search"
                description="Full-text search across all documents in this case"
                icon={
                  <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
                features={[
                  'Fast full-text search powered by Elasticsearch',
                  'Highlighted search results with context',
                  'Filter by document type, date, or status',
                  'Boolean operators (AND, OR, NOT)',
                  'Jump directly to highlighted sections in documents',
                ]}
              />
            )}
          </motion.div>
        </main>
      </div>
    </div>
  )
}

