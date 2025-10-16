/**
 * TypeScript types for Document model
 */

export enum DocumentStatus {
  UPLOADED = 'uploaded',
  DETECTING_TYPE = 'detecting_type',
  EXTRACTING_BLOCKS = 'extracting_blocks',
  CLASSIFYING = 'classifying',
  ANALYZING_CONTENT = 'analyzing_content',
  FILTERED_OUT = 'filtered_out',
  CHUNKING = 'chunking',
  SUMMARIZING = 'summarizing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface Document {
  id: number
  case_id: number
  filename: string
  file_type: string
  file_size: number
  minio_bucket: string
  minio_key: string
  status: DocumentStatus
  processing_error: string | null
  classification: string | null
  content_category: string | null
  filter_confidence: number | null
  filter_reasoning: string | null
  has_summary: boolean
  summarized_at: string | null
  created_at: string
  updated_at: string
}

export interface DocumentUploadResponse extends Document {}

export interface DocumentDetailResponse extends Document {}

export interface DocumentListResponse {
  total: number
  documents: DocumentDetailResponse[]
}

// Helper to get user-friendly status labels
export const getStatusLabel = (status: DocumentStatus): string => {
  const labels: Record<DocumentStatus, string> = {
    [DocumentStatus.UPLOADED]: 'Uploaded',
    [DocumentStatus.DETECTING_TYPE]: 'Detecting Type',
    [DocumentStatus.EXTRACTING_BLOCKS]: 'Extracting Content',
    [DocumentStatus.CLASSIFYING]: 'Classifying',
    [DocumentStatus.ANALYZING_CONTENT]: 'Analyzing',
    [DocumentStatus.FILTERED_OUT]: 'Filtered Out',
    [DocumentStatus.CHUNKING]: 'Chunking',
    [DocumentStatus.SUMMARIZING]: 'Summarizing',
    [DocumentStatus.COMPLETED]: 'Completed',
    [DocumentStatus.FAILED]: 'Failed',
  }
  return labels[status] || status
}

// Helper to get status color
export const getStatusColor = (status: DocumentStatus): 'success' | 'warning' | 'error' | 'info' | 'neutral' => {
  if (status === DocumentStatus.COMPLETED) return 'success'
  if (status === DocumentStatus.FAILED) return 'error'
  if (status === DocumentStatus.FILTERED_OUT) return 'neutral'
  if ([
    DocumentStatus.EXTRACTING_BLOCKS,
    DocumentStatus.CLASSIFYING,
    DocumentStatus.ANALYZING_CONTENT,
    DocumentStatus.CHUNKING,
    DocumentStatus.SUMMARIZING
  ].includes(status)) return 'info'
  return 'warning'
}

