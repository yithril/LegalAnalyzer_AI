"use client"

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { theme, cn } from '@/lib/theme'
import { documentsApi } from '@/lib/api/documents'
import { 
  type Document, 
  DocumentStatus, 
  getStatusLabel, 
  getStatusColor 
} from '@/types/document'

interface DocumentQueueProps {
  caseId: number
  refreshTrigger?: number
}

export default function DocumentQueue({ caseId, refreshTrigger }: DocumentQueueProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  
  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const statusFilter = filterStatus === 'all' ? undefined : filterStatus
      const response = await documentsApi.list(caseId, statusFilter)
      setDocuments(response.documents)
    } catch (err: any) {
      setError(err.message || 'Failed to load documents')
      console.error('Error loading documents:', err)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadDocuments()
  }, [caseId, filterStatus, refreshTrigger])
  
  // Auto-refresh every 5 seconds if there are processing documents
  useEffect(() => {
    const hasProcessing = documents.some(doc => 
      doc.status !== DocumentStatus.COMPLETED && 
      doc.status !== DocumentStatus.FAILED &&
      doc.status !== DocumentStatus.FILTERED_OUT
    )
    
    if (!hasProcessing) return
    
    const interval = setInterval(() => {
      loadDocuments()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [documents])
  
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', { 
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  return (
    <div className="space-y-6">
      {/* Header with Filter */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Document Queue</h3>
          <p className="text-sm text-gray-600 mt-1">
            {documents.length} document{documents.length !== 1 ? 's' : ''}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
            Filter:
          </label>
          <select
            id="status-filter"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
          >
            <option value="all">All Documents</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="incomplete">Incomplete</option>
          </select>
          
          <button
            onClick={loadDocuments}
            className={cn(
              'px-3 py-2 rounded-lg transition-colors',
              theme.components.button.ghost
            )}
            title="Refresh"
          >
            <svg 
              className="w-5 h-5" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
              />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Loading State */}
      {isLoading && documents.length === 0 && (
        <div className="flex justify-center items-center py-16">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading documents...</p>
          </div>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-red-50 border border-red-200 rounded-lg p-6 text-center"
        >
          <p className="text-red-700 font-medium mb-2">Failed to load documents</p>
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <button
            onClick={loadDocuments}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium',
              theme.components.button.primary
            )}
          >
            Try Again
          </button>
        </motion.div>
      )}
      
      {/* Empty State */}
      {!isLoading && !error && documents.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border border-gray-200 p-12 text-center"
        >
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg 
              className="w-8 h-8 text-slate-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" 
              />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No documents yet</h3>
          <p className="text-gray-600">Upload documents to see them here</p>
        </motion.div>
      )}
      
      {/* Documents List */}
      {!isLoading && !error && documents.length > 0 && (
        <div className="space-y-3">
          {documents.map((doc, index) => {
            const statusColor = getStatusColor(doc.status as DocumentStatus)
            
            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  {/* Left: File Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      {/* File Icon */}
                      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <svg 
                          className="w-6 h-6 text-primary-600" 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            strokeWidth={2} 
                            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" 
                          />
                        </svg>
                      </div>
                      
                      {/* Filename */}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">
                          {doc.filename}
                        </h4>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(doc.file_size)} • {doc.file_type.toUpperCase()}
                        </p>
                      </div>
                    </div>
                    
                    {/* Classification & Category */}
                    {(doc.classification || doc.content_category) && (
                      <div className="flex items-center gap-2 mb-2">
                        {doc.classification && (
                          <span className={cn(
                            'px-2 py-1 rounded-md text-xs font-medium',
                            theme.components.badge.info
                          )}>
                            {doc.classification}
                          </span>
                        )}
                        {doc.content_category && (
                          <span className={cn(
                            'px-2 py-1 rounded-md text-xs font-medium',
                            theme.components.badge.neutral
                          )}>
                            {doc.content_category}
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* Error Message */}
                    {doc.processing_error && (
                      <div className="mt-2 text-sm text-red-600 bg-red-50 rounded px-3 py-2">
                        <span className="font-medium">Error:</span> {doc.processing_error}
                      </div>
                    )}
                    
                    {/* Filter Reasoning */}
                    {doc.filter_reasoning && doc.status === DocumentStatus.FILTERED_OUT && (
                      <div className="mt-2 text-sm text-gray-600 bg-gray-50 rounded px-3 py-2">
                        <span className="font-medium">Filtered:</span> {doc.filter_reasoning}
                      </div>
                    )}
                    
                    <p className="text-xs text-gray-500 mt-2">
                      Uploaded {formatDate(doc.created_at)}
                    </p>
                  </div>
                  
                  {/* Right: Status Badge */}
                  <div className="flex flex-col items-end gap-2">
                    <span className={cn(
                      'px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap',
                      theme.components.badge[statusColor]
                    )}>
                      {getStatusLabel(doc.status as DocumentStatus)}
                    </span>
                    
                    {/* Processing Indicator */}
                    {doc.status !== DocumentStatus.COMPLETED && 
                     doc.status !== DocumentStatus.FAILED &&
                     doc.status !== DocumentStatus.FILTERED_OUT && (
                      <div className="flex items-center gap-1.5 text-xs text-gray-500">
                        <div className="animate-spin rounded-full h-3 w-3 border-2 border-primary-600 border-t-transparent"></div>
                        Processing...
                      </div>
                    )}
                    
                    {/* Summary Indicator */}
                    {doc.has_summary && (
                      <div className="flex items-center gap-1 text-xs text-success-600">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path 
                            fillRule="evenodd" 
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                            clipRule="evenodd" 
                          />
                        </svg>
                        Summary ready
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}

