import { useMemo, useState } from "react";
import { Button } from "./components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Switch } from "./components/ui/switch";
import { Label } from "./components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import {
  useAnalyzeKeyword,
  useAnalyzeOpenAI,
  type AIResult,
  type KeywordResult,
} from "./api/analyze";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [openaiEnabled, setOpenaiEnabled] = useState<boolean>(false);
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
    kwMutation.mutate(text, {
      onSuccess: (data) => setKw(data),
      onError: (e: any) => setError(e?.message ?? "Keyword analyze failed"),
    });
    if (openaiEnabled) {
      aiMutation.mutate(text, {
        onSuccess: (data) => setAi(data),
        onError: (e: any) => setError(e?.message ?? "OpenAI analyze failed"),
      });
    } else {
      setAi(null);
    }
  }

  const isAnalyzing = kwMutation.isPending || aiMutation.isPending;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
        <header className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight">WhatSafe</h1>
            <Badge variant="outline">Beta</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Analyze WhatsApp <span className="font-mono">.txt</span> exports for
            boycott indicators.
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Upload conversation</CardTitle>
            <CardDescription>
              Files stay on your machine; only parsed text is sent to the
              backend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="chat-file">WhatsApp export (.txt)</Label>
              <input
                id="chat-file"
                type="file"
                accept=".txt"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="block w-full cursor-pointer rounded-lg border border-dashed border-input bg-background/40 px-3 py-2 text-sm transition hover:border-primary focus-visible:outline-none"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-muted/20 p-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium">Also analyze with OpenAI</p>
                  <p className="text-xs text-muted-foreground"></p>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={openaiEnabled}
                  onCheckedChange={(checked) => setOpenaiEnabled(!!checked)}
                />
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" size="icon" className="h-8 w-8">
                      ?
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent align="end">
                    Runs GPT-4o-mini for contextual reasoning and confidence info.
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <Button
              className="w-full md:w-auto"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? "Analyzing…" : "Analyze conversation"}
            </Button>

            {(error || kwMutation.error || aiMutation.error) && (
              <p className="text-sm text-red-400">
                Error:{" "}
                {error ||
                  (kwMutation.error as any)?.message ||
                  (aiMutation.error as any)?.message}
              </p>
            )}
          </CardContent>
        </Card>

        {kw && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Risk label</CardDescription>
                <CardTitle className="text-xl">{kw.label}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 text-sm text-muted-foreground">
                Overall classification based on keyword density and sender
                concentration.
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Risk score</CardDescription>
                <CardTitle className="text-xl">
                  {kw.risk_signals.boycott_risk}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 flex gap-2 text-xs">
                <Badge variant="outline">
                  Total msgs: {kw.risk_signals.total_messages}
                </Badge>
                <Badge variant="outline">
                  Boycott msgs: {kw.risk_signals.boycott_messages}
                </Badge>
              </CardContent>
            </Card>
          </div>
        )}

        {kw && (
          <Card>
            <CardHeader>
              <CardTitle>Per-sender stats</CardTitle>
              <CardDescription>
                Who drives most of the conversation and boycott signals.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {senders.map((s) => {
                const st = kw.per_sender_stats[s];
                return (
                  <div
                    key={s}
                    className="rounded-lg border border-border/60 bg-muted/10 p-3 text-sm"
                  >
                    <p className="font-medium">{s}</p>
                    <p className="text-xs text-muted-foreground">
                      Messages: {st.messages} · Chars: {st.chars} · Boycott:{" "}
                      {st.boycott_msgs}
                    </p>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {ai && (
          <Card className="border-primary/40">
            <CardHeader>
              <CardTitle>AI insight ({ai.model_used})</CardTitle>
              <CardDescription>
                Contextual reasoning produced by OpenAI (beta).
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs text-muted-foreground">
                  Boycott detected
                </p>
                <p className="text-lg font-semibold">
                  {ai.boycott_detected ? "Yes" : "No"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Risk level</p>
                <p className="text-lg font-semibold">
                  {ai.risk_level.toUpperCase()}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Confidence</p>
                <p className="text-lg font-semibold">
                  {ai.confidence.toFixed(2)}
                </p>
              </div>
              {ai.potential_targets?.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground">
                    Potential targets
                  </p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {ai.potential_targets.map((t) => (
                      <Badge key={t} variant="outline">
                        {t}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {ai.reasoning && (
                <div className="md:col-span-2">
                  <p className="text-xs text-muted-foreground">Reasoning</p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">
                    {ai.reasoning}
                  </p>
                </div>
              )}
              {ai.boycott_details && (
                <div className="md:col-span-2">
                  <p className="text-xs text-muted-foreground">
                    Detailed findings
                  </p>
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">
                    {ai.boycott_details}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
    </div>
  );
}

