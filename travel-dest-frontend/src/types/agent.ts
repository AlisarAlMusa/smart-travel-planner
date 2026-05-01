// TypeScript types for agent requests, responses, history, and tool traces.

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type ToolCall = {
  tool_name: string;
  status: string;
  latency_ms?: number;
  tool_input?: JsonValue | Record<string, unknown> | null;
  tool_output?: JsonValue | Record<string, unknown> | null;
  output?: JsonValue | Record<string, unknown> | null;
  error_message?: string | null;
};

export type RetrievedDestination = {
  destination?: string;
  title?: string | null;
  url?: string | null;
  chunk_index?: number;
  chunk_text?: string;
  similarity_score?: number;
};

export type AgentRunRequest = {
  query: string;
};

export type AgentRunResponse = {
  agent_run_id?: string;
  answer?: string;
  final_answer?: string;
  predicted_style?: string;
  destinations?: RetrievedDestination[];
  retrieval?: {
    status?: string;
    destinations?: RetrievedDestination[];
    [key: string]: unknown;
  };
  trip_style_prediction?: {
    status?: string;
    prediction?: {
      predicted_style?: string;
      confidence?: number;
      extracted_features?: Record<string, unknown>;
      [key: string]: unknown;
    } | null;
    [key: string]: unknown;
  };
  live_conditions?: {
    status?: string;
    conditions?: Array<Record<string, unknown>>;
    [key: string]: unknown;
  };
  tool_calls?: ToolCall[];
  total_tokens?: number;
  estimated_cost?: number;
};

export type NormalizedAgentRun = {
  answer: string;
  predictedStyle?: string;
  destinations: RetrievedDestination[];
  toolCalls: ToolCall[];
  totalTokens?: number;
  estimatedCost?: number;
  raw: AgentRunResponse;
};

export type AgentRunHistoryItem = {
  id: string;
  user_query: string;
  final_answer?: string | null;
  total_tokens?: number;
  estimated_cost?: number;
  created_at?: string;
};
