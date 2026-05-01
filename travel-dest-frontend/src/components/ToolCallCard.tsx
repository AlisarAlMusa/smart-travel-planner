// Displays one collapsible tool call with input, output, status, and latency.

import { ChevronDown, ChevronRight, Clock, Wrench } from "lucide-react";
import { useState } from "react";

import type { ToolCall } from "../types/agent";

type ToolCallCardProps = {
  toolCall: ToolCall;
};

function formatToolName(name: string) {
  return name.replaceAll("_", " ");
}

function renderJson(value: unknown, emptyText: string) {
  if (value === undefined || value === null) {
    return <p className="muted">{emptyText}</p>;
  }

  return <pre>{JSON.stringify(value, null, 2)}</pre>;
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [isOpen, setIsOpen] = useState(true);
  const output = toolCall.tool_output ?? toolCall.output;
  const status = toolCall.status || "unknown";
  const isFailed = status.toLowerCase().includes("error") || status.toLowerCase().includes("fail");

  return (
    <article className={`tool-card ${isFailed ? "failed" : "success"}`}>
      <button className="tool-card-header" type="button" onClick={() => setIsOpen((value) => !value)}>
        <span className="tool-title">
          <Wrench size={17} />
          <span>{formatToolName(toolCall.tool_name)}</span>
        </span>
        <span className={`status-pill ${isFailed ? "failed" : "success"}`}>{status}</span>
        {typeof toolCall.latency_ms === "number" ? (
          <span className="latency">
            <Clock size={14} />
            {toolCall.latency_ms} ms
          </span>
        ) : null}
        {isOpen ? <ChevronDown size={17} /> : <ChevronRight size={17} />}
      </button>

      {isOpen ? (
        <div className="tool-card-body">
          {toolCall.error_message ? <p className="error-banner">{toolCall.error_message}</p> : null}
          <section>
            <h4>Tool Input</h4>
            {renderJson(toolCall.tool_input, "Tool input was not returned by the backend.")}
          </section>
          <section>
            <h4>Tool Output</h4>
            {renderJson(output, "No tool output was returned.")}
          </section>
        </div>
      ) : null}
    </article>
  );
}
