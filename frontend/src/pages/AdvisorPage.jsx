import React, { useState } from "react";
import { ClipLoader } from "react-spinners";
import API from "../utils/api";

export default function AdvisorPage() {
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

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
      setChat([...updatedChat, { role: "assistant", content: answer }]);
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
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-2xl font-bold">AI Consulting Advisor 💬</h2>
        <button
          type="button"
          onClick={handleClear}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-3 py-1 rounded"
          disabled={loading || chat.length === 0}
        >
          Clear Chat
        </button>
      </div>

      <div
        className="border rounded p-4 overflow-y-auto bg-gray-50"
        style={{ height: 400 }}
      >
        {chat.map((message, index) => (
          <div
            key={`chat-${index}`}
            className={`my-2 p-2 rounded ${
              message.role === "user"
                ? "bg-blue-100 text-right"
                : "bg-green-100 text-left"
            }`}
          >
            <p className="text-sm whitespace-pre-line">{message.content}</p>
          </div>
        ))}
        {loading && (
          <div className="flex justify-end mt-2">
            <ClipLoader size={20} color="#6366f1" loading={loading} />
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 mt-4">
        <input
          type="text"
          placeholder="Ask about markets, strategy, or performance..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          className="flex-grow border p-2 rounded"
        />
        <button
          type="submit"
          className="bg-indigo-600 text-white px-4 py-2 rounded"
          disabled={loading}
        >
          Send
        </button>
      </form>
    </div>
  );
}
