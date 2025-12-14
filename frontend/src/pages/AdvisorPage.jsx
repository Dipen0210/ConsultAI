import React, { useMemo, useState } from "react";
import { ClipLoader } from "react-spinners";
import API from "../utils/api";

const exampleQuestions = [
  "What should be our immediate focus for APAC expansion?",
  "Where can we trim operating costs without hurting growth?",
  "How do we position against emerging low-cost competitors?",
];

export default function AdvisorPage() {
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  const lastAssistantMessage = useMemo(
    () => [...chat].reverse().find((message) => message.role === "assistant"),
    [chat]
  );

  const advisorStatus = useMemo(() => {
    if (loading) {
      return { label: "Thinking…", tone: "text-indigo-600 bg-indigo-50" };
    }
    if (!lastAssistantMessage) {
      return { label: "Idle", tone: "text-slate-600 bg-slate-100" };
    }
    if (lastAssistantMessage.source === "huggingface") {
      return {
        label: "Live agent",
        tone: "text-emerald-700 bg-emerald-50",
      };
    }
    return {
      label: "Fallback response",
      tone: "text-amber-700 bg-amber-50",
    };
  }, [lastAssistantMessage, loading]);

  const handleClear = () => {
    setChat([]);
    setQuestion("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }

    const updatedChat = [...chat, { role: "user", content: trimmedQuestion }];
    setChat(updatedChat);
    setLoading(true);

    try {
      const response = await API.post("/advisor", { question: trimmedQuestion });
      const answer =
        response.data?.data?.answer ?? "No response from advisor.";
      const source = response.data?.data?.source ?? "unknown";
      const warning = response.data?.warning;

      setChat([
        ...updatedChat,
        { role: "assistant", content: answer, source, warning },
      ]);
    } catch (error) {
      console.error("Advisor request failed", error);
      setChat([
        ...updatedChat,
        { role: "assistant", content: "Error contacting advisor." },
      ]);
    } finally {
      setQuestion("");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <section className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              AI Consulting Advisor
            </h1>
            <p className="text-sm text-slate-500">
              Ask your question and get a concise, three-bullet answer.
            </p>
          </div>
          <div
            className={`px-3 py-1 rounded-full text-sm font-medium ${advisorStatus.tone}`}
          >
            {advisorStatus.label}
          </div>
        </div>
        {lastAssistantMessage?.warning && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {lastAssistantMessage.warning}
          </div>
        )}
      </section>

      <section className="bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col">
        <header className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Chat</h2>
          <button
            type="button"
            onClick={handleClear}
            className="text-sm text-slate-600 border border-slate-200 rounded-full px-3 py-1 hover:bg-slate-50 disabled:opacity-50"
            disabled={loading || chat.length === 0}
          >
            Clear
          </button>
        </header>
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-3 max-h-[480px]">
          {chat.length === 0 && (
            <p className="text-center text-sm text-slate-400">
              Start the conversation with a question or pick a prompt above.
            </p>
          )}
          {chat.map((message, index) => (
            <div
              key={`chat-${index}`}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-xl rounded-2xl px-4 py-3 text-sm ${
                  message.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 text-slate-900"
                }`}
              >
                <p className="whitespace-pre-line break-words">
                  {message.content}
                </p>
                {message.role === "assistant" && (
                  <div className="text-xs mt-2 text-slate-500 space-y-1">
                    <p>
                      Source:{" "}
                      {message.source === "huggingface"
                        ? "Live agent"
                        : "Fallback response"}
                    </p>
                    {message.warning && (
                      <p className="text-amber-600">{message.warning}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-100 text-slate-900 rounded-2xl px-4 py-3 text-sm flex items-center gap-3">
                <ClipLoader size={18} color="#4c1d95" loading={loading} />
                <span>Advisor drafting response…</span>
              </div>
            </div>
          )}
        </div>
        <form
          onSubmit={handleSubmit}
          className="border-t border-slate-100 px-5 py-4 flex gap-3"
        >
          <input
            type="text"
            placeholder="Ask about markets, strategy, or performance..."
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            className="flex-grow border border-slate-200 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            className="bg-indigo-600 text-white px-5 py-3 rounded-2xl text-sm font-semibold hover:bg-indigo-700 disabled:opacity-60"
            disabled={loading}
          >
            Send
          </button>
        </form>
      </section>

      <section className="bg-white border border-dashed border-slate-200 rounded-2xl shadow-sm p-4 space-y-2">
        <p className="text-xs uppercase tracking-wide text-slate-500">
          Example Questions
        </p>
        <div className="flex flex-wrap gap-2">
          {exampleQuestions.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setQuestion(item)}
              className="text-sm px-3 py-1.5 rounded-full border border-slate-200 text-slate-600 hover:border-indigo-400 hover:text-indigo-600 transition-colors"
            >
              {item}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
