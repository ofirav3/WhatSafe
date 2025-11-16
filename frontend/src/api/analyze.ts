import { useMutation } from "@tanstack/react-query";

export type KeywordResult = {
  label: string;
  risk_signals: {
    boycott_risk: number;
    keyword_ratio: number;
    sender_concentration: number;
    total_messages: number;
    boycott_messages: number;
  };
  per_sender_stats: Record<string, { messages: number; chars: number; boycott_msgs: number }>;
  potential_target: string | null;
  target_mentions: [string, number][];
};

export type AIResult = {
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

async function analyzeKeyword(content: string): Promise<KeywordResult> {
  const res = await fetch("http://localhost:3000/api/analyze-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(`Keyword analyze failed: ${res.status}`);
  return res.json();
}

async function analyzeOpenAI(content: string): Promise<AIResult> {
  const res = await fetch("http://localhost:3000/api/analyze-text-ai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(`OpenAI analyze failed: ${res.status}`);
  return res.json();
}

export function useAnalyzeKeyword() {
  return useMutation({ mutationFn: analyzeKeyword });
}

export function useAnalyzeOpenAI() {
  return useMutation({ mutationFn: analyzeOpenAI });
}


