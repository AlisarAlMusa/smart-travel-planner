// Displays one tool call with a friendly summary and expandable raw details.

import { ChevronDown, ChevronRight, Clock, Wrench } from "lucide-react";
import { useState } from "react";

import type { ToolCall } from "../types/agent";

type ToolCallCardProps = {
  toolCall: ToolCall;
};

type UnknownRecord = Record<string, unknown>;

function formatToolName(name: string) {
  return name.replaceAll("_", " ");
}

function asRecord(value: unknown): UnknownRecord | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as UnknownRecord)
    : null;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asText(value: unknown) {
  return typeof value === "string" && value.trim() ? value : null;
}

function asNumber(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function renderJson(value: unknown, emptyText: string) {
  if (value === undefined || value === null) {
    return <p className="muted">{emptyText}</p>;
  }

  return <pre>{JSON.stringify(value, null, 2)}</pre>;
}

function getOutput(toolCall: ToolCall) {
  return toolCall.tool_output ?? toolCall.output;
}

function getErrorMessage(outputRecord: UnknownRecord | null, fallback?: string | null) {
  const errorRecord = asRecord(outputRecord?.error);
  return fallback ?? asText(errorRecord?.message);
}

function renderClassificationSummary(outputRecord: UnknownRecord | null, errorMessage?: string | null) {
  const prediction = asRecord(outputRecord?.prediction);
  const predictedStyle = asText(prediction?.predicted_style);
  const confidence = asNumber(prediction?.confidence);

  if (!prediction || !predictedStyle) {
    return (
      <p>
        Classification did not return a style.
        {errorMessage ? ` ${errorMessage}` : ""}
      </p>
    );
  }

  return (
    <div className="summary-list">
      <div className="summary-item">
        <span>Predicted style</span>
        <strong>{predictedStyle}</strong>
      </div>
      {confidence !== null ? (
        <div className="summary-item">
          <span>Confidence</span>
          <strong>{Math.round(confidence * 100)}%</strong>
        </div>
      ) : null}
    </div>
  );
}

function renderRetrievalSummary(outputRecord: UnknownRecord | null) {
  const destinations = asArray(outputRecord?.destinations);
  const rewrittenQuery = asText(outputRecord?.rewritten_query);

  if (destinations.length === 0) {
    return (
      <div className="summary-list">
        <div className="summary-item">
          <span>Destinations found</span>
          <strong>0</strong>
        </div>
        <p className="muted">No destination chunks matched this request strongly enough.</p>
      </div>
    );
  }

  return (
    <div className="summary-list">
      <div className="summary-item">
        <span>Destinations found</span>
        <strong>{destinations.length}</strong>
      </div>
      {rewrittenQuery ? (
        <div className="summary-item">
          <span>Search query</span>
          <strong>{rewrittenQuery}</strong>
        </div>
      ) : null}
      <div className="destination-pills">
        {destinations.slice(0, 3).map((destination, index) => {
          const record = asRecord(destination);
          return <span key={`${record?.destination ?? index}`}>{asText(record?.destination) ?? "Unknown"}</span>;
        })}
      </div>
    </div>
  );
}

function renderWeatherSummary(outputRecord: UnknownRecord | null, errorMessage?: string | null) {
  const conditions = asArray(outputRecord?.conditions);

  if (conditions.length === 0) {
    return <p>{errorMessage ?? "Weather was skipped because there were no destinations to check."}</p>;
  }

  return (
    <div className="summary-list">
      {conditions.slice(0, 3).map((condition, index) => {
        const record = asRecord(condition);
        const destination = asText(record?.destination) ?? "Unknown";
        const summary = asText(record?.weather_summary) ?? "No summary";
        const temperature = asNumber(record?.temperature_c);

        return (
          <div className="summary-item" key={`${destination}-${index}`}>
            <span>{destination}</span>
            <strong>{temperature !== null ? `${temperature}C, ` : ""}{summary}</strong>
          </div>
        );
      })}
    </div>
  );
}

function renderFriendlySummary(toolCall: ToolCall, outputRecord: UnknownRecord | null) {
  const errorMessage = getErrorMessage(outputRecord, toolCall.error_message);

  if (toolCall.tool_name === "classify_travel_style") {
    return renderClassificationSummary(outputRecord, errorMessage);
  }

  if (toolCall.tool_name === "retrieve_destinations") {
    return renderRetrievalSummary(outputRecord);
  }

  if (toolCall.tool_name === "get_live_conditions") {
    return renderWeatherSummary(outputRecord, errorMessage);
  }

  return <p>{errorMessage ?? "Tool completed. Open raw details for the full payload."}</p>;
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const output = getOutput(toolCall);
  const outputRecord = asRecord(output);
  const status = toolCall.status || "unknown";
  const normalizedStatus = status.toLowerCase();
  const isFailed = normalizedStatus.includes("error") || normalizedStatus.includes("fail");
  const isPartial = normalizedStatus.includes("partial");

  return (
    <article className={`tool-card ${isFailed ? "failed" : "success"}`}>
      <div className="tool-card-header">
        <span className="tool-title">
          <Wrench size={17} />
          <span>{formatToolName(toolCall.tool_name)}</span>
        </span>
        <span className={`status-pill ${isFailed ? "failed" : isPartial ? "partial" : "success"}`}>
          {status}
        </span>
        {typeof toolCall.latency_ms === "number" ? (
          <span className="latency">
            <Clock size={14} />
            {toolCall.latency_ms} ms
          </span>
        ) : null}
      </div>

      <div className="tool-summary">{renderFriendlySummary(toolCall, outputRecord)}</div>

      <button className="detail-toggle" type="button" onClick={() => setIsOpen((value) => !value)}>
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        {isOpen ? "Hide raw details" : "Show raw details"}
      </button>

      {isOpen ? (
        <div className="tool-card-body">
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
