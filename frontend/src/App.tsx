import { useMemo, useState } from "react";
import { Button, Card, Pill } from "./components/ui";
import { useAnalyzeKeyword, useAnalyzeOpenAI } from "./api/analyze";

type KeywordResult = {
  label: string;
  risk_signals: {
    boycott_risk: number;
    keyword_ratio: number;
    sender_concentration: number;
    total_messages: number;
    boycott_messages: number;
  };
  per_sender_stats: Record<
    string,
    { messages: number; chars: number; boycott_msgs: number }
  >;
  potential_target: string | null;
  target_mentions: [string, number][];
};

type AIResult = {
  source: string;
  boycott_detected: boolean;
  confidence: number;
  risk_level: "none" | "low" | "medium" | "high";
  reasoning: string;
  boycott_details: string;
  potential_targets: string[];
  model_used: string;
  label: string;
};

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [openaiEnabled, setOpenaiEnabled] = useState<boolean>(false);
  const [showAiHelp, setShowAiHelp] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [kw, setKw] = useState<KeywordResult | null>(null);
  const [ai, setAi] = useState<AIResult | null>(null);
  const kwMutation = useAnalyzeKeyword();
  const aiMutation = useAnalyzeOpenAI();

  const senders = useMemo(
    () => (kw ? Object.keys(kw.per_sender_stats) : []),
    [kw]
  );

  async function handleAnalyze() {
    setError(null);
    setKw(null);
    setAi(null);
    if (!file) {
      setError("Please choose a WhatsApp .txt file first.");
      return;
    }

    const text = await file.text();
    setLoading(true);
    kwMutation.mutate(text, {
      onSuccess: (data) => setKw(data),
      onError: (e: any) => setError(e?.message ?? "Keyword analyze failed"),
      onSettled: () => setLoading(false),
    });
    if (openaiEnabled) {
      aiMutation.mutate(text, {
        onSuccess: (data) => setAi(data),
        onError: (e: any) => setError(e?.message ?? "OpenAI analyze failed"),
      });
    }
  }

  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="text-2xl font-semibold tracking-tight">WhatSafe</h1>
      <p className="mt-1 text-sm text-slate-400">
        Analyze a WhatsApp <span className="font-mono">.txt</span> export for potential boycott signals.
      </p>

      <Card className="mt-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <input
            type="file"
            accept=".txt"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full cursor-pointer rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm transition hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-300 select-none">
              <input
                type="checkbox"
                checked={openaiEnabled}
                onChange={(e) => setOpenaiEnabled(e.target.checked)}
              />
              Also analyze with OpenAI
            </label>
            <button
              type="button"
              aria-label="What is this?"
              onClick={() => setShowAiHelp((s) => !s)}
              className="h-6 w-6 rounded-full border border-slate-700 bg-slate-900 text-xs font-semibold text-slate-200 hover:bg-slate-800"
              title="What is this?"
            >
              ?
            </button>
          </div>
          {showAiHelp && (
            <div className="text-xs text-slate-400 md:ml-2">
              Choose optional AI backend for deeper insights.
            </div>
          )}
          <Button onClick={handleAnalyze} disabled={loading || kwMutation.isPending || aiMutation.isPending}>
            {loading || kwMutation.isPending || aiMutation.isPending ? "Analyzing…" : "Analyze"}
          </Button>
        </div>
        {(error || kwMutation.error || aiMutation.error) && (
          <p className="mt-3 text-sm text-red-400">
            Error: {error || (kwMutation.error as any)?.message || (aiMutation.error as any)?.message}
          </p>
        )}
      </Card>

      {kw && (
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <Card>
            <h2 className="text-sm text-slate-300">Risk label</h2>
            <div className="mt-1 text-lg">{kw.label}</div>
          </Card>
          <Card>
            <h2 className="text-sm text-slate-300">Risk score</h2>
            <div className="mt-1 text-lg">{kw.risk_signals.boycott_risk}</div>
          </Card>
          <Card>
            <h2 className="text-sm text-slate-300">Totals</h2>
            <div className="mt-2 flex gap-2 text-sm">
              <Pill>Total msgs: {kw.risk_signals.total_messages}</Pill>
              <Pill>Boycott msgs: {kw.risk_signals.boycott_messages}</Pill>
            </div>
          </Card>
          <Card>
            <h2 className="text-sm text-slate-300">Potential target</h2>
            <div className="mt-1 text-lg">
              {kw.potential_target ?? "—"}
            </div>
          </Card>
        </div>
      )}

      {kw && (
        <Card className="mt-6">
          <h2 className="text-sm text-slate-300">Per-sender stats</h2>
          <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
            {senders.map((s) => {
              const st = kw.per_sender_stats[s];
              return (
                <div
                  key={s}
                  className="rounded-md border border-slate-800 bg-slate-900 p-3"
                >
                  <div className="text-sm font-medium">{s}</div>
                  <div className="mt-1 text-xs text-slate-400">
                    Messages: {st.messages} · Chars: {st.chars} · Boycott:{" "}
                    {st.boycott_msgs}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {ai && (
        <Card className="mt-6">
          <h2 className="text-sm text-blue-300">AI details ({ai.model_used})</h2>
          <div className="mt-2 grid gap-3 md:grid-cols-2">
            <div>
              <div className="text-xs text-slate-400">Boycott detected</div>
              <div className="text-base">
                {ai.boycott_detected ? "Yes" : "No"}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Risk level</div>
              <div className="text-base">{ai.risk_level.toUpperCase()}</div>
            </div>
            <div>
              <div className="text-xs text-slate-400">Confidence</div>
              <div className="text-base">{ai.confidence.toFixed(2)}</div>
            </div>
          </div>
          {ai.reasoning && (
            <div className="mt-4">
              <div className="text-xs text-slate-400">Reasoning</div>
              <p className="mt-1 whitespace-pre-wrap text-sm">{ai.reasoning}</p>
            </div>
          )}
          {ai.potential_targets?.length > 0 && (
            <div className="mt-4">
              <div className="text-xs text-slate-400">Potential targets</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {ai.potential_targets.map((t) => (
                  <Pill key={t}>{t}</Pill>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

