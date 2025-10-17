"use client"

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { motion, AnimatePresence } from 'framer-motion'
import * as z from 'zod'
import { theme, cn } from '@/lib/theme'
import type { Case, CaseCreateRequest } from '@/types/case'

const caseSchema = z.object({
  name: z.string().min(1, 'Case name is required').max(255, 'Case name is too long'),
  description: z.string().optional(),
})

type CaseFormData = z.infer<typeof caseSchema>

interface CaseModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CaseCreateRequest) => Promise<void>
  editCase?: Case | null
  isSubmitting?: boolean
}

export default function CaseModal({
  isOpen,
  onClose,
  onSubmit,
  editCase,
  isSubmitting = false,
}: CaseModalProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CaseFormData>({
    resolver: zodResolver(caseSchema),
    defaultValues: editCase 
      ? { name: editCase.name, description: editCase.description || '' }
      : { name: '', description: '' },
  })
  
  // Reset form when modal opens/closes or editCase changes
  useEffect(() => {
    if (isOpen) {
      reset(editCase 
        ? { name: editCase.name, description: editCase.description || '' }
        : { name: '', description: '' })
    }
  }, [isOpen, editCase, reset])
  
  const handleFormSubmit = async (data: CaseFormData) => {
    await onSubmit({
      name: data.name,
      description: data.description || null,
    })
  }
  
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={theme.components.modal.overlay}
            onClick={handleBackdropClick}
          />
          
          {/* Modal */}
          <div className={theme.components.modal.container} onClick={handleBackdropClick}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className={theme.components.modal.content}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="px-6 py-5 border-b border-gray-200">
                <h2 className="text-2xl font-bold text-gray-900">
                  {editCase ? 'Edit Case' : 'Create New Case'}
                </h2>
                <p className="mt-1 text-sm text-gray-600">
                  {editCase 
                    ? 'Update the case details below' 
                    : 'Enter the details for your new case'}
                </p>
              </div>
              
              {/* Form */}
              <form onSubmit={handleSubmit(handleFormSubmit)} className="px-6 py-6 space-y-6">
                {/* Case Name */}
                <div>
                  <label 
                    htmlFor="name" 
                    className="block text-sm font-semibold text-gray-700 mb-2"
                  >
                    Case Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    {...register('name')}
                    id="name"
                    type="text"
                    placeholder="e.g., Smith v. Jones"
                    className={cn(
                      theme.components.input.base,
                      errors.name && theme.components.input.error
                    )}
                    autoFocus
                  />
                  {errors.name && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="text-red-500 text-sm mt-1.5"
                    >
                      {errors.name.message}
                    </motion.p>
                  )}
                </div>
                
                {/* Description */}
                <div>
                  <label 
                    htmlFor="description" 
                    className="block text-sm font-semibold text-gray-700 mb-2"
                  >
                    Description <span className="text-gray-400 font-normal">(Optional)</span>
                  </label>
                  <textarea
                    {...register('description')}
                    id="description"
                    rows={4}
                    placeholder="Add notes or context about this case..."
                    className={cn(
                      theme.components.input.base,
                      'resize-none'
                    )}
                  />
                  {errors.description && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="text-red-500 text-sm mt-1.5"
                    >
                      {errors.description.message}
                    </motion.p>
                  )}
                </div>
                
                {/* Actions */}
                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={isSubmitting}
                    className={cn(
                      'px-5 py-2.5 rounded-lg font-medium transition-colors',
                      theme.components.button.ghost,
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    Cancel
                  </button>
                  
                  <motion.button
                    whileHover={{ scale: isSubmitting ? 1 : 1.02 }}
                    whileTap={{ scale: isSubmitting ? 1 : 0.98 }}
                    type="submit"
                    disabled={isSubmitting}
                    className={cn(
                      'px-6 py-2.5 rounded-lg font-semibold transition-all',
                      theme.components.button.primary,
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {isSubmitting ? (
                      <span className="flex items-center gap-2">
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
                        {editCase ? 'Updating...' : 'Creating...'}
                      </span>
                    ) : (
                      editCase ? 'Update Case' : 'Create Case'
                    )}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}

