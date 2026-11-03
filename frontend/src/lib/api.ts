/**
 * Nexora AI - Centralized Typed API Client
 * Seamlessly interfaces with the hardened FastAPI backend endpoints.
 */

export const getApiUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

// Storage helper for auth token
export const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('nexora_token');
};

export const setToken = (token: string): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('nexora_token', token);
};

export const clearToken = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('nexora_token');
  localStorage.removeItem('nexora_user');
  try {
    localStorage.clear();
  } catch (e) {
    // ignore
  }
};

export const getUser = (): any | null => {
  if (typeof window === 'undefined') return null;
  const user = localStorage.getItem('nexora_user');
  return user ? JSON.parse(user) : null;
};

export const setUser = (user: any): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem('nexora_user', JSON.stringify(user));
};

// Generic fetch wrapper with Bearer token and error handling
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiUrl();
  const token = getToken();

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  // Only set Content-Type to json if body is not FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle Rate Limiting
  if (response.status === 429) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Rate limit exceeded. Please wait a moment and try again.');
  }

  // Handle Unauthorized
  if (response.status === 401) {
    clearToken();
    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
      window.location.href = '/login?expired=true';
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Session expired. Please log in again.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Auth API Endpoints
// ============================================================================

export interface UserProfile {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
  tenant?: {
    id: string;
    name: string;
    slug: string;
    created_at: string;
  };
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export const authApi = {
  register: (payload: { company_name: string; email: string; password: string; full_name: string; role?: string }) =>
    apiFetch<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: { email: string; password: string }) =>
    apiFetch<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMe: () => apiFetch<UserProfile>('/api/v1/auth/me'),
};

// ============================================================================
// Query & Multi-Agent Intelligence Endpoints
// ============================================================================

export interface ExecutiveQueryResponse {
  query_id: string;
  prompt: string;
  intent: string;
  selected_departments: string[];
  execution_time_ms: number;
  confidence_score: number;
  executive_summary: string;
  department_outputs: Record<string, any>;
  visual_config?: {
    chart_type?: string;
    title?: string;
    data?: any[];
    x_axis?: string;
    series?: { key: string; name: string; color: string }[];
  };
  evidence_queries: Array<{
    department: string;
    sql: string;
    source: string;
  }>;
  strategic_recommendations: Array<{
    id?: string;
    title: string;
    target_department: string;
    action_item: string;
    expected_impact: string;
    confidence_score?: number;
    impact_urgency?: string;
    supporting_evidence: string[];
  }>;
}

export interface GovernanceStats {
  total_decisions: number;
  accepted_count: number;
  rejected_count: number;
  modified_count: number;
  acceptance_rate_pct: number;
  department_breakdown: Record<string, Record<string, number>>;
  recent_decisions: any[];
}

export const queryApi = {
  executeQuery: (prompt: string) =>
    apiFetch<ExecutiveQueryResponse>('/api/v1/query/execute', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    }),

  checkOllamaStatus: () =>
    apiFetch<{ status: string; local_models?: string[]; active_llm: string; info?: string }>(
      '/api/v1/query/ollama-status'
    ),

  getCacheStats: () =>
    apiFetch<{ status: string; hits: number; misses: number; keys_cached: number }>(
      '/api/v1/query/cache-stats'
    ),

  clearCache: () =>
    apiFetch<{ status: string; tenant_id: string; message: string }>('/api/v1/query/cache-clear', {
      method: 'POST',
    }),

  logRecommendationDecision: (payload: {
    recommendation_id: string;
    recommendation_title: string;
    department: string;
    action_type: 'ACCEPTED' | 'REJECTED' | 'MODIFIED';
    action_plan: string;
    feedback_notes?: string;
    confidence_score?: number;
    impact_urgency?: string;
  }) =>
    apiFetch<any>('/api/v1/query/recommendations/decisions', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listDecisions: (limit = 50, department?: string, action_type?: string) => {
    let url = `/api/v1/query/recommendations/decisions?limit=${limit}`;
    if (department) url += `&department=${encodeURIComponent(department)}`;
    if (action_type) url += `&action_type=${encodeURIComponent(action_type)}`;
    return apiFetch<any[]>(url);
  },

  getGovernanceStats: () =>
    apiFetch<GovernanceStats>('/api/v1/query/recommendations/stats'),
};

// ============================================================================
// Ingestion & Enterprise Memory Endpoints
// ============================================================================

export interface DatasetItem {
  id: string;
  name: string;
  department: string;
  row_count: number;
  schema_info?: {
    total_columns?: number;
    detected_types?: Record<string, string>;
    kpis_extracted?: Record<string, any>;
    canonical_mappings?: Record<string, string>;
  };
  created_at: string;
}

export interface IngestionJob {
  id: string;
  tenant_id: string;
  department: string;
  filename: string;
  status: 'PENDING' | 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  stage: string;
  progress: number;
  row_count?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface SchemaAnalysisResult {
  department: string;
  filename: string;
  temp_file_id: string;
  total_columns: number;
  proposed_mappings: Array<{
    user_column: string;
    proposed_canonical: string;
    confidence: number;
    sample_values: string[];
    available_options: string[];
  }>;
  canonical_fields_available: string[];
}

export const ingestApi = {
  analyzeSchema: (file: File, department: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('department', department);
    return apiFetch<SchemaAnalysisResult>('/api/v1/ingest/analyze-schema', {
      method: 'POST',
      body: formData,
    });
  },

  confirmAndIngest: (tempFileId: string, department: string, confirmedMapping: Record<string, string>) =>
    apiFetch<IngestionJob>('/api/v1/ingest/confirm-and-ingest', {
      method: 'POST',
      body: JSON.stringify({
        temp_file_id: tempFileId,
        department,
        confirmed_mapping: confirmedMapping,
      }),
    }),

  uploadDirect: (file: File, department: string, sync = false) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('department', department);
    return apiFetch<IngestionJob>(`/api/v1/ingest/upload?sync=${sync}`, {
      method: 'POST',
      body: formData,
    });
  },

  getJobStatus: (jobId: string) =>
    apiFetch<IngestionJob>(`/api/v1/ingest/jobs/${jobId}`),

  getDatasets: () =>
    apiFetch<DatasetItem[]>('/api/v1/ingest/datasets'),

  getDatasetDetail: (datasetId: string) =>
    apiFetch<any>(`/api/v1/ingest/datasets/${datasetId}`),
};

// ============================================================================
// Sentinel AI Anomaly Monitoring Endpoints
// ============================================================================

export interface SentinelAlertItem {
  id: string;
  title: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  metric_name: string;
  current_value: number;
  historical_mean: number;
  deviation_score: number;
  root_cause: string;
  target_role: string;
  acknowledged: boolean;
  created_at: string;
}

export const sentinelApi = {
  getAlerts: (severity?: string, acknowledged?: boolean) => {
    let url = '/api/v1/sentinel/alerts';
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (acknowledged !== undefined) params.append('acknowledged', String(acknowledged));
    const qs = params.toString();
    if (qs) url += `?${qs}`;
    return apiFetch<SentinelAlertItem[]>(url);
  },

  triggerScan: () =>
    apiFetch<SentinelAlertItem[]>('/api/v1/sentinel/trigger', {
      method: 'POST',
    }),

  acknowledgeAlert: (alertId: string) =>
    apiFetch<SentinelAlertItem>(`/api/v1/sentinel/alerts/${alertId}/acknowledge`, {
      method: 'PATCH',
    }),
};

// ============================================================================
// Health & Telemetry Endpoints
// ============================================================================

export const healthApi = {
  getHealth: () =>
    apiFetch<{
      status: string;
      subsystems: Record<string, any>;
      system_resources: Record<string, any>;
      uptime_seconds: number;
    }>('/health'),
};
