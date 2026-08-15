"""Dependency-free HTTP Web UI Server for AI Movie Dubbing Studio."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Movie Dubbing Studio</title>
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --text: #f8fafc;
            --muted: #94a3b8;
            --border: #334155;
            --success: #10b981;
        }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
            display: flex;
            justify-content: center;
        }
        .container {
            max-width: 900px;
            width: 100%;
        }
        .header {
            margin-bottom: 32px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.2rem;
            margin: 0 0 8px 0;
            background: linear-gradient(135deg, #a855f7, #6366f1, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p {
            color: var(--muted);
            margin: 0;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .card h2 {
            margin-top: 0;
            font-size: 1.25rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            font-weight: 600;
            font-size: 0.9rem;
            color: #cbd5e1;
        }
        input[type="text"], input[type="password"], select {
            width: 100%;
            padding: 10px 14px;
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 0.95rem;
            box-sizing: border-box;
        }
        input[type="text"]:focus, select:focus {
            border-color: var(--accent);
            outline: none;
        }
        .btn {
            background: linear-gradient(135deg, var(--accent), var(--accent-hover));
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.1s ease;
        }
        .btn:hover {
            transform: translateY(-1px);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        #statusBox {
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px;
            font-family: monospace;
            font-size: 0.85rem;
            min-height: 120px;
            white-space: pre-wrap;
            color: #38bdf8;
            overflow-y: auto;
            max-height: 300px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Movie Dubbing Studio</h1>
            <p>Production Multi-Provider Agent Dubbing Web Interface</p>
        </div>

        <div class="card">
            <h2>Job Configuration</h2>
            <form id="dubForm">
                <div class="form-group">
                    <label for="inputPath">Input Movie File Path (.mp4, .mkv, .mov)</label>
                    <input type="text" id="inputPath" placeholder="D:\movies\sample.mp4" required>
                </div>
                <div class="form-group">
                    <label for="targetLang">Target Language Code</label>
                    <input type="text" id="targetLang" value="bn" placeholder="bn (Bengali), es, fr, ru" required>
                </div>
                <div class="form-group">
                    <label for="provider">AI Provider Router</label>
                    <select id="provider">
                        <option value="OpenRouter">OpenRouter (100+ Models)</option>
                        <option value="Gemini">Google Gemini API</option>
                        <option value="OpenAI">OpenAI / ChatGPT</option>
                        <option value="DeepSeek">DeepSeek (V3 / R1)</option>
                        <option value="Custom URL">Custom Gateway / Proxy URL</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="apiKey">API Key (Optional / Pre-filled from .env)</label>
                    <input type="password" id="apiKey" placeholder="sk-...">
                </div>
                <div class="form-group">
                    <label for="customUrl">Custom Gateway URL (For Custom URL Provider)</label>
                    <input type="text" id="customUrl" value="https://api.openai.com/v1">
                </div>
                <button type="submit" class="btn" id="runBtn">Start AI Movie Dubbing Engine</button>
            </form>
        </div>

        <div class="card">
            <h2>Execution Progress & Output Logs</h2>
            <div id="statusBox">Ready. Configure inputs above and click Start AI Movie Dubbing Engine.</div>
        </div>
    </div>

    <script>
        document.getElementById('dubForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('runBtn');
            const box = document.getElementById('statusBox');
            btn.disabled = true;
            btn.innerText = 'Processing Dubbing Job...';
            box.innerText = 'Initializing DubbingEngine 9-stage pipeline...\\nTarget Language: ' + document.getElementById('targetLang').value;

            try {
                const res = await fetch('/api/dub', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        input: document.getElementById('inputPath').value,
                        target_lang: document.getElementById('targetLang').value,
                        provider: document.getElementById('provider').value,
                        api_key: document.getElementById('apiKey').value,
                        custom_url: document.getElementById('customUrl').value,
                    })
                });
                const data = await res.json();
                if (data.status === 'ok') {
                    box.innerText = 'SUCCESS: Dubbing Finished!\\n\\nOutput Video: ' + data.dubbed_video + '\\nBilingual Subtitles: ' + data.bilingual_srt;
                } else {
                    box.innerText = 'ERROR: ' + data.error;
                }
            } catch (err) {
                box.innerText = 'Network/Execution error: ' + err.message;
            } finally {
                btn.disabled = false;
                btn.innerText = 'Start AI Movie Dubbing Engine';
            }
        });
    </script>
</body>
</html>
"""


class StudioWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving Studio Web UI."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self) -> None:
        if self.path == "/api/dub":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            input_path = data.get("input", "")
            target_lang = data.get("target_lang", "bn")
            provider = data.get("provider", "OpenRouter")
            api_key = data.get("api_key", "")
            custom_url = data.get("custom_url", "")

            if api_key:
                if provider == "OpenRouter":
                    os.environ["OPENROUTER_API_KEY"] = api_key
                elif provider == "Gemini":
                    os.environ["GEMINI_API_KEY"] = api_key
                elif provider == "OpenAI":
                    os.environ["OPENAI_API_KEY"] = api_key
                elif provider == "DeepSeek":
                    os.environ["DEEPSEEK_API_KEY"] = api_key
                elif provider == "Custom URL":
                    os.environ["UNOFFICIAL_1_URL"] = custom_url
                    os.environ["UNOFFICIAL_1_KEY"] = api_key

            from aidub.pipeline.config import PipelineConfig
            from aidub.pipeline.engine import DubbingEngine

            in_p = Path(input_path)
            out_p = in_p.parent / f"{in_p.stem}_dubbed_{target_lang}.mp4"

            try:
                cfg = PipelineConfig(input=in_p, output=out_p, tgt_lang=target_lang)
                engine = DubbingEngine(cfg)
                outputs = engine.run()
                response = {
                    "status": "ok",
                    "dubbed_video": str(outputs.dubbed_video),
                    "bilingual_srt": str(outputs.bilingual_srt),
                }
            except Exception as exc:
                response = {"status": "error", "error": str(exc)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


def run_html_studio_server(port: int = 7860) -> None:
    """Run lightweight HTTP server."""
    server = HTTPServer(("0.0.0.0", port), StudioWebHandler)
    print(f"AI Movie Dubbing Studio Web UI server live on http://localhost:{port}")
    server.serve_forever()


__all__ = ["run_html_studio_server"]
