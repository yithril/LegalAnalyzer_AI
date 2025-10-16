/**
 * TypeScript types for Case model
 */

export interface Case {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface CaseCreateRequest {
  name: string
  description?: string | null
}

export interface CaseUpdateRequest {
  name?: string
  description?: string | null
}

export interface CaseResponse extends Case {}

