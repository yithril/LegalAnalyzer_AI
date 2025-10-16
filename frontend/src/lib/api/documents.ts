/**
 * API methods for Document operations
 */

import { api } from '../api'
import type { DocumentUploadResponse, DocumentDetailResponse, DocumentListResponse } from '@/types/document'

export const documentsApi = {
  /**
   * Upload a document to a case
   */
  async upload(caseId: number, file: File): Promise<DocumentUploadResponse> {
    // Create form data with case_id as query param
    const endpoint = `/documents/upload?case_id=${caseId}`
    return api.uploadFile<DocumentUploadResponse>(endpoint, file)
  },
  
  /**
   * Get documents for a case
   */
  async list(
    caseId: number,
    status?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<DocumentListResponse> {
    let endpoint = `/documents/?case_id=${caseId}&limit=${limit}&offset=${offset}`
    if (status) {
      endpoint += `&status=${status}`
    }
    return api.get<DocumentListResponse>(endpoint)
  },
  
  /**
   * Get a single document by ID
   */
  async get(documentId: number): Promise<DocumentDetailResponse> {
    return api.get<DocumentDetailResponse>(`/documents/${documentId}`)
  },
}

