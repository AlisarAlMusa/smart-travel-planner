// Shows the full trace of what the agent did for the latest planner response.

import { Activity, CheckCircle2 } from "lucide-react";

import type { NormalizedAgentRun, ToolCall } from "../types/agent";
import { ToolCallCard } from "./ToolCallCard";

type ToolTracePanelProps = {
  result: NormalizedAgentRun | null;
  isLoading: boolean;
};

const expectedTools = ["classify_travel_style", "retrieve_destinations", "get_live_conditions"];

function hasTool(toolCalls: ToolCall[], toolName: string) {
  return toolCalls.some((toolCall) => toolCall.tool_name === toolName);
}

export function ToolTracePanel({ result, isLoading }: ToolTracePanelProps) {
  const toolCalls = result?.toolCalls ?? [];

  return (
    <aside className="tool-panel">
      <div className="panel-heading">
        <Activity size={20} />
        <div>
          <h2>Agent Trace</h2>
          <p>Tools fired, inputs, outputs, status, and latency.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="trace-empty">
          <CheckCircle2 size={20} />
          <p>The agent is classifying, retrieving destinations, and checking live conditions.</p>
        </div>
      ) : null}

      {!isLoading && !result ? (
        <div className="trace-empty">
          <p>Run a trip request to see exactly what the agent did.</p>
        </div>
      ) : null}

      {result ? (
        <div className="trace-summary">
          {result.predictedStyle ? <span>Style: {result.predictedStyle}</span> : null}
          {typeof result.totalTokens === "number" ? <span>{result.totalTokens} tokens</span> : null}
          {typeof result.estimatedCost === "number" ? (
            <span>${result.estimatedCost.toFixed(6)}</span>
          ) : null}
        </div>
      ) : null}

      <div className="tool-list">
        {toolCalls.map((toolCall, index) => (
          <ToolCallCard key={`${toolCall.tool_name}-${index}`} toolCall={toolCall} />
        ))}
      </div>

      {result ? (
        <div className="expected-tools">
          <h3>Required Tools</h3>
          {expectedTools.map((toolName) => (
            <span key={toolName} className={hasTool(toolCalls, toolName) ? "seen" : "missing"}>
              {toolName.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      ) : null}
    </aside>
  );
}
