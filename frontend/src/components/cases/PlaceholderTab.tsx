"use client"

import { motion } from 'framer-motion'
import { theme, cn } from '@/lib/theme'

interface PlaceholderTabProps {
  title: string
  description: string
  icon: React.ReactNode
  features?: string[]
}

export default function PlaceholderTab({ 
  title, 
  description, 
  icon,
  features = []
}: PlaceholderTabProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-center justify-center min-h-[500px]"
    >
      <div className="max-w-2xl w-full bg-white rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
        <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
          {icon}
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-3">{title}</h2>
        <p className="text-gray-600 mb-6">{description}</p>
        
        {features.length > 0 && (
          <div className="bg-slate-50 rounded-lg p-6 text-left">
            <h3 className="font-semibold text-gray-900 mb-4 text-center">
              Planned Features:
            </h3>
            <ul className="space-y-2">
              {features.map((feature, index) => (
                <li key={index} className="flex items-start gap-3 text-gray-700">
                  <svg 
                    className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" 
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
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        <div className={cn(
          'mt-8 px-4 py-3 rounded-lg inline-flex items-center gap-2',
          theme.components.badge.info
        )}>
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path 
              fillRule="evenodd" 
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" 
              clipRule="evenodd" 
            />
          </svg>
          <span className="font-medium">Coming Soon</span>
        </div>
      </div>
    </motion.div>
  )
}

