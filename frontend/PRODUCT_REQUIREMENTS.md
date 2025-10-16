# LegalDocs AI - Frontend Product Requirements

## MVP User Flow

### 1. Authentication
- **Login Page** (`/login`)
  - Redirect here if not authenticated
  - Email + password form
  - Test accounts available

### 2. Cases List View (`/cases`)
- **After login, user lands here**
- **Layout**: Top-down table view
  - Columns: Case Name, Description (collapsible), Actions
  - Each row has Edit and Delete buttons
  - Sortable/filterable table
  
- **Actions**:
  - "Create New Case" button → Opens modal
  - Click on case row → Navigate to Case Dashboard (`/cases/{case_id}`)

- **Create Case Modal**:
  - Case Name (required)
  - Description (optional)
  - Create button

### 3. Case Dashboard (`/cases/{case_id}`)
- **Layout**:
  - **Top**: Navigation bar
    - Left: App branding / Case name
    - Right: User info + Logout button
  
  - **Left**: Sidebar with tabs (vertical navigation)
  - **Right**: Main content area (changes based on selected tab)

#### Sidebar Tabs:
1. **Upload Documents**
   - Upload interface for documents
   - Drag & drop or file browser
   - Show upload progress
   
2. **Document Queue**
   - List of documents in the case
   - Status indicators (Processing, Completed, Failed, etc.)
   - Filter by status dropdown
   - View processing status in real-time
   
3. **Timeline of Events**
   - Chronological timeline extracted from documents
   - Events with dates, descriptions, sources
   - Visual timeline component
   
4. **Personages**
   - People/entities extracted from documents
   - Names, roles, relationships
   - Clickable to see related documents/events
   
5. **Ask AI**
   - Chat interface to ask questions about the case
   - Context-aware responses based on case documents
   - Chat history
   
6. **Keyword Search**
   - Search through all documents in the case
   - Full-text search
   - Results with document references and highlights
   - Filter results by document type/date

## UI/UX Notes

### Design Goals
- Clean, professional legal/enterprise aesthetic
- Fast navigation between features
- Real-time updates for document processing
- Responsive design (desktop-first)

### Navigation Bar
- Fixed at top
- User avatar/name with dropdown menu
- Logout option
- Breadcrumb navigation (Cases → Case Name → Tab)

### Sidebar
- Fixed on left side
- Icon + text labels
- Active tab highlighted
- Collapsible on mobile

### Main Content Area
- Full width (minus sidebar)
- Scrollable content
- Consistent padding/margins
- Loading states for async operations

## Technical Stack
- **Framework**: Next.js 14 (App Router)
- **Auth**: NextAuth.js
- **Forms**: React Hook Form + Zod
- **Animations**: Framer Motion
- **Styling**: Tailwind CSS
- **State Management**: React hooks (Context API if needed later)

## Data Flow
1. User selects case → Fetch case data
2. Tab selection → Load tab-specific data
3. Document upload → Background processing, poll for status
4. Real-time updates → WebSocket or polling for document processing status

## Future Enhancements (Post-MVP)
- User roles & permissions
- Case sharing/collaboration
- Export reports
- Advanced analytics
- Document comparison
- Bulk operations
- Activity logs
- Notifications

## Pages Structure
```
/login                    - Login page
/cases                    - Cases list view
/cases/[caseId]          - Case dashboard (with tabs)
/dashboard               - (Currently just for testing, will remove)
```

## Components to Build
- [ ] CasesTable
- [ ] CreateCaseModal
- [ ] CaseDashboardLayout (nav + sidebar + content)
- [ ] DocumentUpload
- [ ] DocumentQueue
- [ ] Timeline
- [ ] PersonagesList
- [ ] AIChatInterface
- [ ] KeywordSearch
- [ ] Navbar
- [ ] Sidebar
- [ ] LoadingStates
- [ ] ErrorStates

