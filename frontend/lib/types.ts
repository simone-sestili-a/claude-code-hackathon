// Domain types mirroring the Python Pydantic schemas in src/schemas/document.py

export interface FilledField {
  field_name: string;
  field_value: string;
}

export interface PageExtraction {
  page_number: number;
  header: string;
  summary: string;
  entities: string[];
  filled_fields: FilledField[];
}

export interface ExternalModule {
  module_name: string;
  page_section?: string;
  ercole_related: boolean;
}

export interface Contact {
  // PERSONA FISICA
  name?: string;
  surname?: string;
  fiscal_code?: string;
  data_nascita?: string;
  luogo_nascita?: string;
  provincia_nascita?: string;
  genere?: string;
  // ENTITA GIURIDICA
  ragione_sociale?: string;
  piva?: string;
}

export interface ErcoleRequest {
  request_id: string;
  page_number: number;
  header: string;
  contacts: Contact[];
  notes?: string;
  confidence_score: number;
  external_modules: ExternalModule[];
}

export interface RequestPageAssignment {
  pages: number[];
  reasoning: string;
  confidence_score: number;
}

export interface DocumentProcessingResponse {
  session_id: string;
  total_pages: number;
  page_extractions: PageExtraction[];
  requests: ErcoleRequest[];
  page_assignments: Record<string, RequestPageAssignment>;
  external_modules: string[];
  summary: string;
}

export interface ChatApiResponse {
  session_id?: string;
  flow_type?: string;
  intent: string;
  response: string;
  document_result?: DocumentProcessingResponse | null;
}

export interface FollowUpApiResponse {
  session_id: string;
  answer: string;
}

// UI-layer types

export type MessageRole = "user" | "assistant";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  attachedFileName?: string;
  documentResult?: DocumentProcessingResponse;
  timestamp: Date;
  isLoading?: boolean;
  error?: string;
}

export interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
  backendSessionId?: string;
}
