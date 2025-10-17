/**
 * Centralized theme configuration for LegalDocs AI
 * 
 * Professional legal/enterprise aesthetic with consistent colors, 
 * typography, and component styles.
 */

export const theme = {
  colors: {
    // Primary brand colors
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    
    // Accent colors for actions
    accent: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
    },
    
    // Success states
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
    },
    
    // Warning states
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },
    
    // Error states
    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },
    
    // Neutral grays
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
      950: '#030712',
    },
    
    // Slate for professional UI
    slate: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
      950: '#020617',
    },
  },
  
  // Spacing scale (consistent with Tailwind defaults)
  spacing: {
    xs: '0.5rem',    // 8px
    sm: '0.75rem',   // 12px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
    '3xl': '4rem',   // 64px
  },
  
  // Typography
  typography: {
    fonts: {
      sans: 'Inter, system-ui, -apple-system, sans-serif',
      mono: 'ui-monospace, Menlo, Monaco, monospace',
    },
    
    sizes: {
      xs: '0.75rem',     // 12px
      sm: '0.875rem',    // 14px
      base: '1rem',      // 16px
      lg: '1.125rem',    // 18px
      xl: '1.25rem',     // 20px
      '2xl': '1.5rem',   // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem',  // 36px
      '5xl': '3rem',     // 48px
    },
    
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  
  // Border radius
  radius: {
    none: '0',
    sm: '0.25rem',    // 4px
    md: '0.375rem',   // 6px
    lg: '0.5rem',     // 8px
    xl: '0.75rem',    // 12px
    '2xl': '1rem',    // 16px
    full: '9999px',
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  },
  
  // Component-specific styles
  components: {
    button: {
      primary: 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium shadow-md hover:shadow-lg transition-all',
      secondary: 'bg-blue-100 hover:bg-blue-200 active:bg-blue-300 text-blue-900 font-medium border border-blue-200 transition-all',
      outline: 'border-2 border-blue-600 text-blue-700 hover:bg-blue-50 active:bg-blue-100 font-medium transition-all',
      ghost: 'bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 font-medium transition-all',
      danger: 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-medium shadow-md hover:shadow-lg transition-all',
    },
    
    input: {
      base: 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all outline-none',
      error: 'border-error-500 focus:ring-error-500',
    },
    
    card: {
      base: 'bg-white rounded-xl shadow-md border border-gray-200',
      hover: 'hover:shadow-lg transition-shadow duration-200',
    },
    
    table: {
      header: 'bg-slate-50 text-slate-700 font-semibold',
      row: 'hover:bg-slate-50 border-b border-gray-200',
      cell: 'px-6 py-4 text-sm text-gray-900',
    },
    
    modal: {
      overlay: 'fixed inset-0 bg-black/50 backdrop-blur-sm',
      container: 'fixed inset-0 flex items-center justify-center p-4 z-50',
      content: 'bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden',
    },
    
    badge: {
      success: 'bg-success-100 text-success-700 border border-success-200',
      warning: 'bg-warning-100 text-warning-700 border border-warning-200',
      error: 'bg-error-100 text-error-700 border border-error-200',
      info: 'bg-primary-100 text-primary-700 border border-primary-200',
      neutral: 'bg-slate-100 text-slate-700 border border-slate-200',
    },
  },
  
  // Animation durations
  animation: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
  },
  
  // Z-index layers
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
} as const

// Helper function to get theme values
export const getThemeColor = (path: string) => {
  const keys = path.split('.')
  let value: any = theme.colors
  
  for (const key of keys) {
    value = value?.[key]
  }
  
  return value as string
}

// CSS class builder for common patterns
export const cn = (...classes: (string | boolean | undefined | null)[]) => {
  return classes.filter(Boolean).join(' ')
}

