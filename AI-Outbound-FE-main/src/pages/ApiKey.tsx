import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { userApi } from "../api/api";

const ApiKeyPage: React.FC = () => {
  const { user } = useAuth();
  const [apiKey, setApiKey] = useState(user?.api_key || "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"success" | "error" | "">("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    setMessageType("");
    try {
      if (!user || !user._id) throw new Error("User not found");
      await userApi.updateUser(user._id, { api_key:apiKey });
      setMessage("API key saved successfully!");
      setMessageType("success");
    } catch {
      setMessage("Failed to save API key.");
      setMessageType("error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-full mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          API Key Management
        </h1>
        <p className="text-gray-600 mb-6">
          View, update, or save your API key for integration with external
          services.
        </p>
        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
          {/* <h2 className="text-lg font-semibold text-gray-700 mb-4">API Key</h2> */}
          {message && (
            <div
              className={`mb-4 p-3 rounded-lg border text-sm ${
                messageType === "success"
                  ? "bg-green-50 border-green-200 text-green-700"
                  : "bg-yellow-50 border-yellow-200 text-yellow-700"
              }`}
            >
              {message}
            </div>
          )}
          <form onSubmit={handleSubmit}>
            <label className="block mb-2 font-medium">API Key</label>
            <input
              type="text"
              className="w-full border rounded px-3 py-2 mb-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              required
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors duration-200"
              disabled={saving}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ApiKeyPage;
