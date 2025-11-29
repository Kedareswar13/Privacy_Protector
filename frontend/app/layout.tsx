import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "PrivacyProtector",
  description: "AI-powered privacy exposure scanning and remediation dashboard",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="gradient-bg">
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-border/60 backdrop-blur bg-black/40">
            <div className="container flex items-center justify-between py-3">
              <div className="flex items-center gap-2">
                <div className="h-9 w-9 rounded-xl bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300 font-bold text-lg shadow-soft">
                  PP
                </div>
                <div>
                  <h1 className="text-sm font-semibold tracking-tight text-slate-100">
                    PrivacyProtector
                  </h1>
                  <p className="text-xs text-slate-400">
                    Safe OSINT + reverse image privacy scanner
                  </p>
                </div>
              </div>
            </div>
          </header>
          <main className="flex-1 flex">
            <div className="container py-10 flex-1 flex flex-col max-w-5xl">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
