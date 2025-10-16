/**
 * API methods for Case operations
 */

import { api } from '../api'
import type { Case, CaseCreateRequest, CaseUpdateRequest, CaseResponse } from '@/types/case'

export const casesApi = {
  /**
   * Get all cases
   */
  async list(): Promise<Case[]> {
    return api.get<Case[]>('/cases/')
  },
  
  /**
   * Get a single case by ID
   */
  async get(caseId: number): Promise<CaseResponse> {
    return api.get<CaseResponse>(`/cases/${caseId}`)
  },
  
  /**
   * Create a new case
   */
  async create(data: CaseCreateRequest): Promise<CaseResponse> {
    return api.post<CaseResponse>('/cases/', data)
  },
  
  /**
   * Update an existing case
   */
  async update(caseId: number, data: CaseUpdateRequest): Promise<CaseResponse> {
    return api.patch<CaseResponse>(`/cases/${caseId}`, data)
  },
  
  /**
   * Delete a case
   */
  async delete(caseId: number): Promise<void> {
    return api.delete(`/cases/${caseId}`)
  },
}

