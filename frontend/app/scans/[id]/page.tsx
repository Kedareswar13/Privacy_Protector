"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getItem } from "@/lib/api";

export default function ScanItemPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [item, setItem] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = Number(params.id);
    if (!id) return;
    (async () => {
      try {
        const data = await getItem(id);
        setItem(data);
      } catch (err: any) {
        setError(err.message ?? "Failed to load item");
      } finally {
        setLoading(false);
      }
    })();
  }, [params.id]);

  return (
    <div className="flex flex-col gap-4">
      <Button
        variant="ghost"
        size="sm"
        className="w-fit text-xs text-slate-300"
        onClick={() => router.back()}
      >
         Back to dashboard
      </Button>
      <Card className="border-slate-700/80 bg-slate-950/90">
        <CardHeader>
          <CardTitle>Item details</CardTitle>
          <CardDescription>
            Full context for a single exposure or profile discovered during a scan.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-xs text-slate-500">Loading item...</p>}
          {error && !loading && (
            <p className="text-xs text-red-400 bg-red-950/60 border border-red-900/70 rounded-md px-2 py-1">
              {error}
            </p>
          )}
          {item && !loading && !error && (
            <div className="space-y-2 text-xs text-slate-200">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-200">
                  {item.category}
                </span>
                <span className="rounded-full bg-slate-900/80 px-2 py-0.5 text-[10px] text-slate-400">
                  {item.source}
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
                <p className="max-w-xl text-[11px] text-slate-300/90">{item.snippet}</p>
              )}
              <div>
                <p className="text-[11px] text-slate-400">Raw metadata</p>
                <pre className="mt-1 max-h-64 overflow-auto rounded-md bg-slate-900/80 p-2 text-[10px] text-slate-200">
                  {item.metadata_json}
                </pre>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
