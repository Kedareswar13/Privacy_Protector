"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  createConsent,
  createScan,
  getScan,
  getScanItems,
  runScan,
} from "@/lib/api";

interface ScanSummary {
  id: number;
  status: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [hasConsent, setHasConsent] = useState(false);
  const [loadingConsent, setLoadingConsent] = useState(false);

  const [query, setQuery] = useState("");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageHash, setImageHash] = useState<string | null>(null);
  const [hashingImage, setHashingImage] = useState(false);

  const [runningScan, setRunningScan] = useState(false);
  const [currentScan, setCurrentScan] = useState<ScanSummary | null>(null);
  const [items, setItems] = useState<any[]>([]);
  const [agentLog, setAgentLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("pp_token") : null;
    if (!t) {
      router.replace("/");
      return;
    }
    setToken(t);
  }, [router]);

  async function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setImagePreview(URL.createObjectURL(file));
    setHashingImage(true);
    try {
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
      setImageHash(hashHex);
    } catch (err: any) {
      setError(err?.message ?? "Failed to process image");
      setImageHash(null);
    } finally {
      setHashingImage(false);
    }
  }

  async function handleConsent() {
    if (!token) return;
    setLoadingConsent(true);
    setError(null);
    try {
      await createConsent(token);
      setHasConsent(true);
    } catch (err: any) {
      setError(err.message ?? "Failed to create consent");
    } finally {
      setLoadingConsent(false);
    }
  }

  async function handleRunScan(e: React.FormEvent) {
    e.preventDefault();
    setRunningScan(true);
    setError(null);
    setAgentLog([]);
    setItems([]);
    setCurrentScan(null);

    try {
      const payload: any = {
        seeds: {
          query: query || undefined,
        },
      };
      if (imageHash) {
        payload.seeds.image_hash = imageHash;
      }

      setAgentLog((log) => [
        ...log,
        "Understanding your request and preparing a privacy scan plan.",
      ]);

      const { scan_id } = await createScan(token, payload);
      setCurrentScan({ id: scan_id, status: "pending" });
      setAgentLog((log) => [...log, `Scan ${scan_id} created. Running agent loop...`]);

      const runResult: any = await runScan(scan_id);
      setAgentLog((log) => [
        ...log,
        `Agent executed tools and discovered ${runResult.items_created} relevant results.`,
      ]);

      const s: any = await getScan(scan_id);
      setCurrentScan({ id: scan_id, status: s.status });

      const it: any[] = await getScanItems(scan_id);
      setItems(it);
      setAgentLog((log) => [...log, `Scoring each finding based on category and confidence.`]);
    } catch (err: any) {
      setError(err.message ?? "Failed to run scan");
    } finally {
      setRunningScan(false);
    }
  }

  function riskLabel(score: number): { label: string; color: string } {
    if (score >= 0.5) return { label: "High", color: "bg-red-500/20 text-red-300" };
    if (score >= 0.2) return { label: "Medium", color: "bg-amber-500/20 text-amber-300" };
    return { label: "Low", color: "bg-emerald-500/20 text-emerald-300" };
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center py-8">
      <div className="w-full max-w-3xl space-y-6">
        <div className="flex items-center justify-between text-xs">
          <div className="flex flex-col">
            <span className="text-[11px] uppercase tracking-wide text-slate-500">
              PrivacyProtector
            </span>
            <span className="text-[11px] text-slate-400">
              Ask anything about your digital footprint. The agent will search the web and
              breaches for you.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 ${
                hasConsent
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                  : "border-amber-500/40 bg-amber-500/10 text-amber-200"
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {hasConsent ? "Consent active" : "Consent required"}
            </span>
            {!hasConsent && (
              <Button
                variant="outline"
                size="sm"
                disabled={loadingConsent || !token}
                onClick={handleConsent}
              >
                {loadingConsent ? "Creating consent..." : "Grant consent"}
              </Button>
            )}
          </div>
        </div>

        <div className="space-y-4 text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-50 md:text-3xl">
            What's on your mind today?
          </h2>
          <p className="text-xs text-slate-400 md:text-sm">
            Type anything you want the agent to investigate about your online presence. You can
            also add a profile photo to look for similar images on the web.
          </p>
        </div>

        <Card className="border-slate-700/80 bg-slate-950/90">
          <CardContent className="pt-6">
            <form className="space-y-4" onSubmit={handleRunScan}>
              <div className="flex items-center gap-2 rounded-full border border-slate-700/80 bg-slate-900/80 px-4 py-2 shadow-lg">
                <span className="text-xs text-slate-500">Ask anything</span>
                <Input
                  id="query"
                  className="border-0 bg-transparent px-2 py-1 text-sm text-slate-100 shadow-none focus-visible:ring-0"
                  placeholder="Search the web for my name and image leaks, old profiles, or breaches..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <Label
                  htmlFor="image-upload"
                  className="flex cursor-pointer items-center rounded-full bg-slate-800 px-3 py-1 text-[11px] text-slate-200 hover:bg-slate-700"
                >
                  {hashingImage ? "Processing..." : "Add image"}
                </Label>
                <input
                  id="image-upload"
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleImageChange}
                />
                <Button type="submit" size="sm" disabled={runningScan || !token}>
                  {runningScan ? "Running scan" : "Go"}
                </Button>
              </div>
              {error && (
                <p className="text-xs text-red-400 bg-red-950/60 border border-red-900/70 rounded-md px-2 py-1 text-left">
                  {error}
                </p>
              )}
              {imagePreview && (
                <div className="flex items-center justify-between gap-3 rounded-md border border-slate-800/80 bg-slate-950/80 px-3 py-2 text-xs text-slate-300">
                  <div className="flex items-center gap-3">
                    <img
                      src={imagePreview}
                      alt="Selected for reverse image search"
                      className="h-10 w-10 rounded-md object-cover"
                    />
                    <div className="text-left">
                      <p className="text-[11px] font-medium text-slate-100">
                        Image attached
                      </p>
                      <p className="text-[11px] text-slate-400">
                        The agent will use a privacy-preserving hash of this image to search for
                        lookalikes.
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {currentScan && (
                <p className="text-[11px] text-left text-slate-400">
                  Last scan: <span className="text-slate-100">#{currentScan.id}</span> – status
                  <span className="text-slate-100"> {currentScan.status}</span>
                </p>
              )}
            </form>
          </CardContent>
        </Card>

        <Card className="border-slate-700/80 bg-slate-950/90">
          <CardHeader>
            <CardTitle>Results</CardTitle>
            <CardDescription>
              Websites, breaches, and profiles the agent found that may be linked to your
              request.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {items.length === 0 ? (
              <p className="text-xs text-slate-500">
                Ask something above to see web results, breaches, social posts, and image
                matches.
              </p>
            ) : (
              <div className="space-y-2">
                {items.map((item) => {
                  const risk = riskLabel(item.risk_score ?? 0);
                  return (
                    <div
                      key={item.id}
                      className="flex items-start justify-between gap-3 rounded-md border border-slate-800/80 bg-slate-950/80 px-3 py-2 text-xs"
                    >
                      <div className="space-y-0.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-200">
                            {item.category}
                          </span>
                          <span className="rounded-full bg-slate-900/80 px-2 py-0.5 text-[10px] text-slate-400">
                            {item.source}
                          </span>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${risk.color}`}
                          >
                            Risk: {risk.label}
                          </span>
                        </div>
                        {item.url && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            className="block max-w-xl truncate text-[11px] text-cyan-300 hover:underline"
                          >
                            {item.url}
                          </a>
                        )}
                        {item.snippet && (
                          <p className="max-w-xl text-[11px] text-slate-300/90">
                            {item.snippet}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/scans/${item.id}`)}
                        >
                          View details
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {agentLog.length > 0 && (
          <Card className="border-slate-700/80 bg-slate-950/90">
            <CardHeader>
              <CardTitle>How the agent is thinking</CardTitle>
              <CardDescription>
                A short explanation of the steps the agent took to answer your request.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="space-y-1.5 text-xs text-slate-200">
                {agentLog.map((line, idx) => (
                  <li key={idx} className="flex gap-2">
                    <span className="mt-1 h-1.5 w-1.5 rounded-full bg-cyan-400" />
                    <span>{line}</span>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
