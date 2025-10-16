"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { signOut, useSession } from 'next-auth/react'
import { casesApi } from '@/lib/api/cases'
import { theme, cn } from '@/lib/theme'
import CaseModal from '@/components/cases/CaseModal'
import type { Case, CaseCreateRequest } from '@/types/case'

export default function CasesPage() {
  const router = useRouter()
  const { data: session } = useSession()
  const [cases, setCases] = useState<Case[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCase, setEditingCase] = useState<Case | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [deletingCaseId, setDeletingCaseId] = useState<number | null>(null)
  
  // Load cases
  const loadCases = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await casesApi.list()
      setCases(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load cases')
      console.error('Error loading cases:', err)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    loadCases()
  }, [])
  
  // Handle create case
  const handleCreateCase = async (data: CaseCreateRequest) => {
    try {
      setIsSubmitting(true)
      const newCase = await casesApi.create(data)
      setCases([newCase, ...cases])
      setIsModalOpen(false)
    } catch (err: any) {
      alert(err.message || 'Failed to create case')
      console.error('Error creating case:', err)
    } finally {
      setIsSubmitting(false)
    }
  }
  
  // Handle update case
  const handleUpdateCase = async (data: CaseCreateRequest) => {
    if (!editingCase) return
    
    try {
      setIsSubmitting(true)
      const updatedCase = await casesApi.update(editingCase.id, data)
      setCases(cases.map(c => c.id === updatedCase.id ? updatedCase : c))
      setIsModalOpen(false)
      setEditingCase(null)
    } catch (err: any) {
      alert(err.message || 'Failed to update case')
      console.error('Error updating case:', err)
    } finally {
      setIsSubmitting(false)
    }
  }
  
  // Handle delete case
  const handleDeleteCase = async (caseId: number) => {
    const caseToDelete = cases.find(c => c.id === caseId)
    if (!caseToDelete) return
    
    const confirmed = window.confirm(
      `Are you sure you want to delete "${caseToDelete.name}"? This action cannot be undone.`
    )
    
    if (!confirmed) return
    
    try {
      setDeletingCaseId(caseId)
      await casesApi.delete(caseId)
      setCases(cases.filter(c => c.id !== caseId))
    } catch (err: any) {
      alert(err.message || 'Failed to delete case')
      console.error('Error deleting case:', err)
    } finally {
      setDeletingCaseId(null)
    }
  }
  
  // Open edit modal
  const handleEditClick = (caseItem: Case) => {
    setEditingCase(caseItem)
    setIsModalOpen(true)
  }
  
  // Open create modal
  const handleCreateClick = () => {
    setEditingCase(null)
    setIsModalOpen(true)
  }
  
  // Navigate to case dashboard
  const handleCaseClick = (caseId: number) => {
    router.push(`/cases/${caseId}`)
  }
  
  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">L</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900">LegalDocs AI</h1>
            </div>
            
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
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Cases</h2>
            <p className="text-gray-600">Manage your legal cases and documents</p>
          </motion.div>
        </div>
        
        {/* Create Button */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="mb-6"
        >
          <button
            onClick={handleCreateClick}
            className={cn(
              'px-6 py-3 rounded-lg font-semibold transition-all inline-flex items-center gap-2',
              theme.components.button.primary
            )}
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
                d="M12 4v16m8-8H4" 
              />
            </svg>
            Create New Case
          </button>
        </motion.div>
        
        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center items-center py-16">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading cases...</p>
            </div>
          </div>
        )}
        
        {/* Error State */}
        {error && !isLoading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-red-50 border border-red-200 rounded-lg p-6 text-center"
          >
            <p className="text-red-700 font-medium mb-2">Failed to load cases</p>
            <p className="text-red-600 text-sm mb-4">{error}</p>
            <button
              onClick={loadCases}
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
        {!isLoading && !error && cases.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="bg-white rounded-xl shadow-md border border-gray-200 p-12 text-center"
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
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No cases yet</h3>
            <p className="text-gray-600 mb-6">Get started by creating your first case</p>
            <button
              onClick={handleCreateClick}
              className={cn(
                'px-6 py-3 rounded-lg font-semibold transition-all',
                theme.components.button.primary
              )}
            >
              Create Your First Case
            </button>
          </motion.div>
        )}
        
        {/* Cases Table */}
        {!isLoading && !error && cases.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className={theme.components.table.header}>
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider">
                      Case Name
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((caseItem, index) => (
                    <motion.tr
                      key={caseItem.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                      className={cn(
                        theme.components.table.row,
                        'cursor-pointer'
                      )}
                      onClick={() => handleCaseClick(caseItem.id)}
                    >
                      <td className={theme.components.table.cell}>
                        <div className="font-semibold text-primary-700 hover:text-primary-800">
                          {caseItem.name}
                        </div>
                      </td>
                      <td className={theme.components.table.cell}>
                        <div className="max-w-md truncate text-gray-600">
                          {caseItem.description || (
                            <span className="text-gray-400 italic">No description</span>
                          )}
                        </div>
                      </td>
                      <td className={theme.components.table.cell}>
                        <span className="text-gray-600">
                          {formatDate(caseItem.created_at)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleEditClick(caseItem)}
                            className={cn(
                              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                              theme.components.button.ghost
                            )}
                            title="Edit case"
                          >
                            <svg 
                              className="w-4 h-4" 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path 
                                strokeLinecap="round" 
                                strokeLinejoin="round" 
                                strokeWidth={2} 
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" 
                              />
                            </svg>
                          </button>
                          
                          <button
                            onClick={() => handleDeleteCase(caseItem.id)}
                            disabled={deletingCaseId === caseItem.id}
                            className={cn(
                              'px-3 py-1.5 text-sm font-medium rounded-md transition-colors text-red-600 hover:bg-red-50',
                              'disabled:opacity-50 disabled:cursor-not-allowed'
                            )}
                            title="Delete case"
                          >
                            {deletingCaseId === caseItem.id ? (
                              <svg 
                                className="animate-spin h-4 w-4" 
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
                            ) : (
                              <svg 
                                className="w-4 h-4" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth={2} 
                                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" 
                                />
                              </svg>
                            )}
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </main>
      
      {/* Create/Edit Modal */}
      <CaseModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setEditingCase(null)
        }}
        onSubmit={editingCase ? handleUpdateCase : handleCreateCase}
        editCase={editingCase}
        isSubmitting={isSubmitting}
      />
    </div>
  )
}

