"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { login, register } from "@/lib/api";

export default function HomePage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (isLogin) {
        const res = await login(email, password);
        if (typeof window !== "undefined") {
          localStorage.setItem("pp_token", res.access_token);
        }
        window.location.href = "/dashboard";
      } else {
        await register(email, password);
        const res = await login(email, password);
        if (typeof window !== "undefined") {
          localStorage.setItem("pp_token", res.access_token);
        }
        window.location.href = "/dashboard";
      }
    } catch (err: any) {
      setError(err.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="grid w-full gap-8 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] items-center">
        <div className="space-y-4 text-slate-100">
          <p className="inline-flex items-center rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400 shadow-soft">
            <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-emerald-400" />
            AI agent for your own privacy
          </p>
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">
            See where your <span className="text-cyan-400">identity</span> and
            <span className="text-emerald-400"> photos</span> are exposed online.
          </h2>
          <p className="max-w-xl text-sm text-slate-300/90">
            PrivacyProtector runs safe OSINT searches, breach checks, and reverse image search
            to show you where your email, usernames, and photos appear on the public internet —
            then drafts polite takedown requests for you.
          </p>
          <ul className="mt-4 grid gap-2 text-xs text-slate-300 md:grid-cols-2">
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
              No face recognition, only image-level matching
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Breach checks + risk scores for each item
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-fuchsia-400" />
              One-click remediation drafts for websites
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
              All actions auditable and consent-driven
            </li>
          </ul>
        </div>

        <Card className="max-w-md ml-auto mr-auto md:mr-0 border-slate-700/80 bg-slate-950/90">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{isLogin ? "Sign in" : "Create an account"}</CardTitle>
                <CardDescription>
                  {isLogin
                    ? "Use the same account across all your scans."
                    : "We only use your email for auth — scanning is consent-based."}
                </CardDescription>
              </div>
              <div className="flex gap-1 rounded-full bg-slate-900/80 px-1 py-1 text-[11px] font-medium text-slate-300">
                <button
                  className={`px-2 py-1 rounded-full ${
                    isLogin ? "bg-slate-800 text-slate-50" : "text-slate-400"
                  }`}
                  type="button"
                  onClick={() => setIsLogin(true)}
                >
                  Login
                </button>
                <button
                  className={`px-2 py-1 rounded-full ${
                    !isLogin ? "bg-slate-800 text-slate-50" : "text-slate-400"
                  }`}
                  type="button"
                  onClick={() => setIsLogin(false)}
                >
                  Register
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              {error && (
                <p className="text-xs text-red-400 bg-red-950/60 border border-red-900/70 rounded-md px-2 py-1">
                  {error}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading
                  ? isLogin
                    ? "Signing in..."
                    : "Creating account..."
                  : isLogin
                  ? "Sign in to dashboard"
                  : "Create account & continue"}
              </Button>
              <p className="text-[10px] text-slate-500 leading-relaxed">
                By continuing you agree that PrivacyProtector will search only public data sources
                and will never perform facial recognition. Reverse image search is used solely to
                locate copies of the images you upload.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
