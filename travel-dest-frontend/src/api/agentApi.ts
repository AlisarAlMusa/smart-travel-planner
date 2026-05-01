// API helpers for running the agent and reading saved history.

import { apiClient } from "./client";
import type {
  AgentRunHistoryItem,
  AgentRunRequest,
  AgentRunResponse,
  NormalizedAgentRun,
  ToolCall,
} from "../types/agent";

function buildFallbackToolCalls(response: AgentRunResponse): ToolCall[] {
  const calls: ToolCall[] = [];

  if (response.trip_style_prediction) {
    calls.push({
      tool_name: "classify_travel_style",
      status: response.trip_style_prediction.status ?? "success",
      output: response.trip_style_prediction,
    });
  }

  if (response.retrieval) {
    calls.push({
      tool_name: "retrieve_destinations",
      status: response.retrieval.status ?? "success",
      output: response.retrieval,
    });
  }

  if (response.live_conditions) {
    calls.push({
      tool_name: "get_live_conditions",
      status: response.live_conditions.status ?? "success",
      output: response.live_conditions,
    });
  }

  return calls;
}

// Normalizes the current backend shape and the assumed frontend contract into one view model.
export function normalizeAgentRun(response: AgentRunResponse): NormalizedAgentRun {
  return {
    answer: response.final_answer ?? response.answer ?? "No answer was returned.",
    predictedStyle:
      response.trip_style_prediction?.prediction?.predicted_style ?? response.predicted_style,
    destinations: response.retrieval?.destinations ?? response.destinations ?? [],
    toolCalls: response.tool_calls?.length ? response.tool_calls : buildFallbackToolCalls(response),
    totalTokens: response.total_tokens,
    estimatedCost: response.estimated_cost,
    raw: response,
  };
}

export async function runAgent(payload: AgentRunRequest) {
  const response = await apiClient.post<AgentRunResponse>("/agent/run", payload, {
    timeout: 120000,
  });
  return normalizeAgentRun(response.data);
}

export async function getHistory() {
  const response = await apiClient.get<AgentRunHistoryItem[]>("/history");
  return response.data;
}
