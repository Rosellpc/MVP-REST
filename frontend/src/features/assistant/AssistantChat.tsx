import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { apiFetch } from "../../utils/apiFetch";
import "../../styles/assistant-chat.css";

type Role = "user" | "assistant";

type SourceLabel = "Catálogo de productos" | "Políticas de cancelación y reembolso" | "Documento de apoyo";

type Message = {
  role: Role;
  content: string;
  sources?: SourceLabel[];
};

type ChatResponse = {
  answer?: string;
  sources?: SourceLabel[];
  detail?: string;
};

const WELCOME_MESSAGE =
  "Hola. Puedo ayudarte con la carta y la información disponible del restaurante. Para consultas de alergias, verifica siempre con el personal antes de pedir.";

export default function AssistantChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: WELCOME_MESSAGE },
  ]);
  const logRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    logRef.current?.scrollTo({
      top: logRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [isOpen, isSending, messages]);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentQuestion = question.trim();
    if (!currentQuestion || isSending) return;

    const history = messages
      .slice(1)
      .slice(-8)
      .map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, { role: "user", content: currentQuestion }]);
    setQuestion("");
    setIsSending(true);

    try {
      const response = await apiFetch("/api/v1/assistant/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentQuestion, history }),
      });
      const payload = (await response.json().catch(() => ({}))) as ChatResponse;
      if (!response.ok) {
        throw new Error(payload.detail || "No pudimos responder ahora. Inténtalo de nuevo.");
      }

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: payload.answer || "No encontré información suficiente para responder.",
          sources: payload.sources,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "No pudimos conectar con el asistente. Inténtalo más tarde.",
        },
      ]);
    } finally {
      setIsSending(false);
      inputRef.current?.focus();
    }
  }

  function resetConversation() {
    setMessages([{ role: "assistant", content: WELCOME_MESSAGE }]);
    setQuestion("");
  }

  return (
    <section className="assistant-chat" aria-label="Asistente de la carta">
      {isOpen && (
        <div id="assistant-chat-panel" className="assistant-chat__panel" role="dialog" aria-modal="false" aria-labelledby="assistant-chat-title">
          <header className="assistant-chat__header">
            <div>
              <p className="assistant-chat__eyebrow">REST-OS</p>
              <h2 id="assistant-chat-title">Asistente de la carta</h2>
            </div>
            <div className="assistant-chat__header-actions">
              <button type="button" className="assistant-chat__icon-button" onClick={resetConversation} aria-label="Reiniciar conversación" title="Reiniciar conversación">
                ↺
              </button>
              <button type="button" className="assistant-chat__icon-button" onClick={() => setIsOpen(false)} aria-label="Cerrar chat" title="Cerrar chat">
                ×
              </button>
            </div>
          </header>

          <div className="assistant-chat__messages" ref={logRef} role="log" aria-live="polite" aria-relevant="additions text">
            {messages.map((message, index) => (
              <article className={`assistant-chat__message assistant-chat__message--${message.role}`} key={`${index}-${message.role}`}>
                <p>{message.content}</p>
                {message.sources && message.sources.length > 0 && (
                  <div className="assistant-chat__sources" aria-label="Fuentes consultadas">
                    <span>Fuentes</span>
                    {message.sources.map((source) => (
                      <span className="assistant-chat__source" key={source}>{source}</span>
                    ))}
                  </div>
                )}
              </article>
            ))}
            {isSending && <p className="assistant-chat__typing" role="status">Buscando en la carta…</p>}
          </div>

          <p className="assistant-chat__notice">
            Asistente experimental. La información de alérgenos no está verificada; confirma con el personal antes de pedir.
          </p>

          <form className="assistant-chat__form" onSubmit={handleSubmit}>
            <label className="assistant-chat__sr-only" htmlFor="assistant-chat-question">Escribe tu pregunta</label>
            <input
              ref={inputRef}
              id="assistant-chat-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              maxLength={500}
              placeholder="Pregunta sobre la carta…"
              autoComplete="off"
              disabled={isSending}
            />
            <button type="submit" disabled={isSending || question.trim().length < 2} aria-label="Enviar pregunta">
              {isSending ? "…" : "Enviar"}
            </button>
          </form>
        </div>
      )}

      <button
        className="assistant-chat__launcher"
        type="button"
        aria-expanded={isOpen}
        aria-controls="assistant-chat-panel"
        onClick={() => setIsOpen((open) => !open)}
      >
        <span aria-hidden="true">✦</span>
        {isOpen ? "Cerrar asistente" : "¿Dudas sobre la carta?"}
      </button>
    </section>
  );
}
