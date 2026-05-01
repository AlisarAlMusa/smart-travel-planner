// Shows saved agent runs for the authenticated user when the backend supports history.

import { CalendarClock, History } from "lucide-react";
import { useEffect, useState } from "react";

import { getHistory } from "../api/agentApi";
import { getApiErrorMessage } from "../api/client";
import { LoadingDots } from "../components/LoadingDots";
import type { AgentRunHistoryItem } from "../types/agent";

function formatDate(value?: string) {
  if (!value) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function HistoryPage() {
  const [history, setHistory] = useState<AgentRunHistoryItem[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        setIsLoading(true);
        const data = await getHistory();
        setHistory(data);
      } catch (apiError) {
        setError(getApiErrorMessage(apiError));
      } finally {
        setIsLoading(false);
      }
    }

    void loadHistory();
  }, []);

  return (
    <main className="history-page">
      <div className="page-heading">
        <h1>History</h1>
        <p>Review previous planner runs saved by the backend.</p>
      </div>

      {isLoading ? (
        <div className="history-state">
          <LoadingDots />
        </div>
      ) : null}

      {error ? <p className="form-error">{error}</p> : null}

      {!isLoading && !error && history.length === 0 ? (
        <section className="history-state">
          <History size={24} />
          <p>No saved runs yet. Ask the planner something first.</p>
        </section>
      ) : null}

      <section className="history-list">
        {history.map((item) => (
          <article className="history-card" key={item.id}>
            <div className="history-card-top">
              <h2>{item.user_query}</h2>
              <span>
                <CalendarClock size={15} />
                {formatDate(item.created_at)}
              </span>
            </div>
            <p>{item.final_answer ?? "The final answer was not saved for this run."}</p>
            <div className="history-meta">
              {typeof item.total_tokens === "number" ? <span>{item.total_tokens} tokens</span> : null}
              {typeof item.estimated_cost === "number" ? (
                <span>${item.estimated_cost.toFixed(6)}</span>
              ) : null}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
