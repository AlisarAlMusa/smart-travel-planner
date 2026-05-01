// Displays a single user or agent chat bubble.

type ChatMessageProps = {
  role: "user" | "agent";
  content: string;
};

export function ChatMessage({ role, content }: ChatMessageProps) {
  return (
    <article className={`chat-message ${role}`}>
      <div className="message-label">{role === "user" ? "You" : "Planner"}</div>
      <p>{content}</p>
    </article>
  );
}
