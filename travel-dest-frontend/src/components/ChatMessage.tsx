// Displays a single user or agent chat bubble.

import type { ReactNode } from "react";

type ChatMessageProps = {
  role: "user" | "agent";
  content: string;
};

function renderInlineMarkdown(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }

    return part;
  });
}

function renderAgentContent(content: string) {
  const blocks: ReactNode[] = [];
  const lines = content.split("\n");
  let bulletItems: string[] = [];

  function flushBullets() {
    if (bulletItems.length === 0) {
      return;
    }

    blocks.push(
      <ul key={`list-${blocks.length}`}>
        {bulletItems.map((item, index) => (
          <li key={`${item}-${index}`}>{renderInlineMarkdown(item)}</li>
        ))}
      </ul>,
    );
    bulletItems = [];
  }

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();

    if (!trimmedLine) {
      flushBullets();
      return;
    }

    const headingMatch = trimmedLine.match(/^(#{1,3})\s+(.+)$/);
    if (headingMatch) {
      flushBullets();
      const HeadingTag = headingMatch[1].length === 1 ? "h2" : "h3";
      blocks.push(
        <HeadingTag key={`heading-${index}`}>{renderInlineMarkdown(headingMatch[2])}</HeadingTag>,
      );
      return;
    }

    const bulletMatch = trimmedLine.match(/^[-*]\s+(.+)$/);
    if (bulletMatch) {
      bulletItems.push(bulletMatch[1]);
      return;
    }

    flushBullets();
    blocks.push(<p key={`paragraph-${index}`}>{renderInlineMarkdown(trimmedLine)}</p>);
  });

  flushBullets();
  return <div className="message-content markdown-content">{blocks}</div>;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <article className={`chat-message ${role}`}>
      <div className="message-label">{role === "user" ? "You" : "Planner"}</div>
      {role === "agent" ? (
        renderAgentContent(content)
      ) : (
        <p className="message-content">{content}</p>
      )}
    </article>
  );
}
