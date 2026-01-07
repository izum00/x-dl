// This is a minimal Next.js (App Router) example for Vercel
// It provides:
// 1) /api/download endpoint that optionally replaces x.com -> twitter.com (default ON)
// 2) A simple UI to paste URL, toggle the option, and get a downloadable link
//
// File structure (for reference):
// app/page.tsx
// app/api/download/route.ts
// package.json
//
// ---------------------------
// app/page.tsx
// ---------------------------
"use client";
import { useState } from "react";

export default function Page() {
  const [url, setUrl] = useState("");
  const [replace, setReplace] = useState(true); // default ON
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, replaceX: replace }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Unknown error");
      setResult(data.downloadUrl || data.message);
    } catch (e: any) {
      setError(e.message || "Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">X(Twitter) Video Downloader (yt-dlp)</h1>
      <p className="mb-4 text-sm text-gray-600">Vercel上で動くAPI + UI。デフォルトで x.com → twitter.com 置換がONです。</p>

      <div className="space-y-4">
        <input
          type="url"
          placeholder="https://x.com/... or https://twitter.com/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full border rounded px-3 py-2"
        />

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={replace}
            onChange={(e) => setReplace(e.target.checked)}
          />
          変換時に x.com を twitter.com に置き換える（推奨）
        </label>

        <button
          onClick={handleSubmit}
          disabled={loading || !url}
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
        >
          {loading ? "処理中..." : "ダウンロードURLを取得"}
        </button>

        {error && <div className="text-red-600 text-sm">{error}</div>}
        {result && (
          <div className="mt-4 p-3 border rounded">
            <p className="text-sm mb-2">結果:</p>
            {result.startsWith("http") ? (
              <a href={result} className="text-blue-600 underline" target="_blank">{result}</a>
            ) : (
              <pre className="text-xs whitespace-pre-wrap">{result}</pre>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

// ---------------------------
// app/api/download/route.ts
// ---------------------------
import { NextResponse } from "next/server";
import { execFile } from "child_process";
import path from "path";
import fs from "fs";
import os from "os";

export async function POST(req: Request) {
  try {
    const { url, replaceX } = await req.json();
    if (!url || typeof url !== "string") {
      return NextResponse.json({ error: "URL is required" }, { status: 400 });
    }

    let targetUrl = url.trim();
    if (replaceX !== false) {
      // default ON
      targetUrl = targetUrl.replace(/^https?:\/\/x\.com\//i, "https://twitter.com/");
    }

    // NOTE:
    // VercelのServerless環境では yt-dlp バイナリが無いので、
    // 事前にビルド時にバイナリを含める or Edge Functions + 外部API などの対応が必要です。
    // ここでは "yt-dlp" が実行可能パスにある前提のサンプルです。

    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "ytdlp-"));
    const outputTemplate = path.join(tmpDir, "%(title).200s.%(ext)s");

    const args = [
      targetUrl,
      "-f",
      "bv*+ba/b",
      "-o",
      outputTemplate,
      "--no-playlist",
    ];

    const run = () =>
      new Promise<string>((resolve, reject) => {
        execFile("yt-dlp", args, { maxBuffer: 1024 * 1024 * 10 }, (err, stdout, stderr) => {
          if (err) return reject(stderr || err.message);
          resolve(stdout);
        });
      });

    const output = await run();

    // 実際のファイル名を取得
    const files = fs.readdirSync(tmpDir);
    if (!files.length) {
      return NextResponse.json({ error: "Download failed" }, { status: 500 });
    }

    const filePath = path.join(tmpDir, files[0]);
    const fileBuffer = fs.readFileSync(filePath);

    // そのままレスポンスで返す（小さいファイル想定）
    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": `attachment; filename="${encodeURIComponent(files[0])}"`,
      },
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || "Internal error" }, { status: 500 });
  }
}

// ---------------------------
// package.json (参考)
// ---------------------------
// {
//   "name": "x-twitter-downloader",
//   "private": true,
//   "scripts": {
//     "dev": "next dev",
//     "build": "next build",
//     "start": "next start"
//   },
//   "dependencies": {
//     "next": "14.0.0",
//     "react": "^18.2.0",
//     "react-dom": "^18.2.0"
//   }
// }
