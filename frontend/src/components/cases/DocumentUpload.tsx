"use client"

import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { theme, cn } from '@/lib/theme'
import { documentsApi } from '@/lib/api/documents'

interface DocumentUploadProps {
  caseId: number
  onUploadComplete?: () => void
}

export default function DocumentUpload({ caseId, onUploadComplete }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }
  
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      await handleFileUpload(files[0])
    }
  }
  
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      await handleFileUpload(files[0])
    }
    // Reset input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }
  
  const handleFileUpload = async (file: File) => {
    setError(null)
    setSuccess(null)
    setIsUploading(true)
    setUploadProgress(0)
    
    // Simulate progress (since we don't have real progress tracking)
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => Math.min(prev + 10, 90))
    }, 200)
    
    try {
      await documentsApi.upload(caseId, file)
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      setSuccess(`${file.name} uploaded successfully!`)
      
      // Call callback after a brief delay
      setTimeout(() => {
        onUploadComplete?.()
        setSuccess(null)
        setUploadProgress(0)
      }, 2000)
    } catch (err: any) {
      clearInterval(progressInterval)
      setError(err.message || 'Failed to upload document')
      console.error('Upload error:', err)
    } finally {
      setIsUploading(false)
    }
  }
  
  const handleBrowseClick = () => {
    fileInputRef.current?.click()
  }
  
  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'border-2 border-dashed rounded-xl p-12 text-center transition-all',
          isDragging 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 bg-white hover:border-primary-400 hover:bg-gray-50',
          isUploading && 'pointer-events-none opacity-60'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc,.txt"
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        
        {isUploading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto">
              <svg 
                className="animate-spin h-8 w-8 text-primary-600" 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24"
              >
                <circle 
                  className="opacity-25" 
                  cx="12" 
                  cy="12" 
                  r="10" 
                  stroke="currentColor" 
                  strokeWidth="4"
                />
                <path 
                  className="opacity-75" 
                  fill="currentColor" 
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-900 mb-2">Uploading...</p>
              <div className="max-w-xs mx-auto bg-gray-200 rounded-full h-2 overflow-hidden">
                <motion.div 
                  className="bg-primary-600 h-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${uploadProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">{uploadProgress}%</p>
            </div>
          </div>
        ) : (
          <>
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg 
                className="w-8 h-8 text-primary-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
                />
              </svg>
            </div>
            
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Drop your document here
            </h3>
            <p className="text-gray-600 mb-6">
              or click to browse your files
            </p>
            
            <button
              onClick={handleBrowseClick}
              className={cn(
                'px-6 py-3 rounded-lg font-semibold transition-all',
                theme.components.button.primary
              )}
            >
              Browse Files
            </button>
            
            <p className="text-sm text-gray-500 mt-4">
              Supported formats: PDF, DOCX, DOC, TXT
            </p>
          </>
        )}
      </motion.div>
      
      {/* Success Message */}
      {success && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-success-50 border border-success-200 rounded-lg p-4 flex items-center gap-3"
        >
          <svg 
            className="w-5 h-5 text-success-600 flex-shrink-0" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
          <p className="text-success-700 font-medium">{success}</p>
        </motion.div>
      )}
      
      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-error-50 border border-error-200 rounded-lg p-4 flex items-start gap-3"
        >
          <svg 
            className="w-5 h-5 text-error-600 flex-shrink-0 mt-0.5" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
          <div className="flex-1">
            <p className="text-error-700 font-medium mb-1">Upload Failed</p>
            <p className="text-error-600 text-sm">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-error-600 hover:text-error-700"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path 
                fillRule="evenodd" 
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" 
                clipRule="evenodd" 
              />
            </svg>
          </button>
        </motion.div>
      )}
      
      {/* Instructions */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <svg 
            className="w-5 h-5 text-slate-600" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
          What happens after upload?
        </h4>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">1.</span>
            <span>Document is uploaded to secure storage</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">2.</span>
            <span>AI processes and extracts content</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">3.</span>
            <span>Document is classified and analyzed</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">4.</span>
            <span>Summary and insights are generated</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-600 font-bold">5.</span>
            <span>You can view results in the Document Queue tab</span>
          </li>
        </ul>
      </div>
    </div>
  )
}

