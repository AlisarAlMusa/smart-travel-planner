// Chat-style planner page that runs the AI agent and shows its tool trace.

import { SendHorizontal } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";

import { runAgent } from "../api/agentApi";
import { getApiErrorMessage } from "../api/client";
import { ChatMessage } from "../components/ChatMessage";
import { LoadingDots } from "../components/LoadingDots";
import { ToolTracePanel } from "../components/ToolTracePanel";
import type { NormalizedAgentRun } from "../types/agent";

type ChatEntry = {
  id: string;
  role: "user" | "agent";
  content: string;
};

const examplePrompts = [
  "I want a budget beach trip with warm weather",
  "I want a cultural city with good food",
  "I want an adventure destination with nature",
];

export function ChatPage() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [latestResult, setLatestResult] = useState<NormalizedAgentRun | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const canSubmit = useMemo(() => query.trim().length > 0 && !isLoading, [isLoading, query]);

  async function submitQuery(nextQuery: string) {
    if (isLoading) {
      return;
    }

    const trimmedQuery = nextQuery.trim();

    if (!trimmedQuery) {
      setError("Please enter a trip question first.");
      return;
    }

    setError("");
    setIsLoading(true);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: trimmedQuery },
    ]);
    setQuery("");

    try {
      const result = await runAgent({ query: trimmedQuery });
      setLatestResult(result);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "agent", content: result.answer },
      ]);
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuery(query);
  }

  return (
    <main className="chat-layout">
      <section className="chat-panel">
        <div className="page-heading">
          <h1>Trip Planner</h1>
          <p>Ask for a destination recommendation and inspect every tool the agent used.</p>
        </div>

        <div className="chat-window">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <h2>Where should we go?</h2>
              <p>Start with one of these prompts or write your own.</p>
              <div className="prompt-grid">
                {examplePrompts.map((prompt) => (
                  <button key={prompt} type="button" onClick={() => void submitQuery(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} role={message.role} content={message.content} />
            ))
          )}

          {isLoading ? (
            <article className="chat-message agent">
              <div className="message-label">Planner</div>
              <LoadingDots />
            </article>
          ) : null}
        </div>

        {error ? <p className="form-error">{error}</p> : null}

        <form className="chat-form" onSubmit={handleSubmit}>
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Tell me your budget, travel style, weather preferences, and dates if you have them."
            rows={3}
          />
          <button className="primary-button" type="submit" disabled={!canSubmit}>
            <SendHorizontal size={18} />
            {isLoading ? "Planning..." : "Ask Agent"}
          </button>
        </form>
      </section>

      <ToolTracePanel result={latestResult} isLoading={isLoading} />
    </main>
  );
}
