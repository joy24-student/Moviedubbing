"""Standalone Web UI for interactive AI Movie Dubbing Studio testing."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_web_app():
    """Build Gradio or HTTP Web UI interface for interactive movie dubbing."""
    try:
        import gradio as gr  # type: ignore[import-not-found]
    except ImportError:
        logger.warning("Gradio not installed — installing standard Gradio app fallback")
        return None

    def run_dubbing(
        input_video: str,
        target_language: str,
        keep_music: bool,
        provider_name: str,
        api_key: str,
        custom_base_url: str,
    ) -> tuple[str | None, str | None, str]:
        if not input_video:
            return None, None, "Error: Please upload a movie/video file first."

        import os
        if api_key:
            if provider_name == "OpenRouter":
                os.environ["OPENROUTER_API_KEY"] = api_key
            elif provider_name == "Gemini":
                os.environ["GEMINI_API_KEY"] = api_key
            elif provider_name == "OpenAI":
                os.environ["OPENAI_API_KEY"] = api_key
            elif provider_name == "DeepSeek":
                os.environ["DEEPSEEK_API_KEY"] = api_key
            elif provider_name == "Custom URL":
                os.environ["UNOFFICIAL_1_URL"] = custom_base_url
                os.environ["UNOFFICIAL_1_KEY"] = api_key

        from aidub.pipeline.config import PipelineConfig
        from aidub.pipeline.engine import DubbingEngine

        in_p = Path(input_video)
        out_p = in_p.parent / f"{in_p.stem}_dubbed_{target_language}.mp4"

        cfg = PipelineConfig(
            input=in_p,
            output=out_p,
            tgt_lang=target_language,
            keep_music=keep_music,
        )

        try:
            engine = DubbingEngine(cfg)
            outputs = engine.run()
            status_msg = f"SUCCESS: Dubbing finished!\nOutput video: {outputs.dubbed_video}\nSRT: {outputs.bilingual_srt}"
            return outputs.dubbed_video, outputs.bilingual_srt, status_msg
        except Exception as exc:
            return None, None, f"Error running dubbing pipeline: {exc}"

    with gr.Blocks(title="AI Movie Dubbing Studio", theme=gr.themes.Soft()) as app:
        gr.Markdown("# AI Movie Dubbing Studio - Web UI")
        gr.Markdown("Upload movie clips, choose target language (Bengali `bn`), set AI API keys, and run the pipeline interactively.")

        with gr.Row():
            with gr.Column():
                input_video = gr.Video(label="Input Movie File (.mp4, .mkv, .mov)")
                target_lang = gr.Textbox(value="bn", label="Target Language Code (e.g. bn for Bengali, es, fr, ru)")
                keep_music = gr.Checkbox(value=True, label="Keep Background Music Track (Demucs Separation)")
                
                provider_select = gr.Dropdown(
                    choices=["OpenRouter", "Gemini", "OpenAI", "DeepSeek", "Custom URL"],
                    value="OpenRouter",
                    label="AI Provider Router",
                )
                api_key_input = gr.Textbox(type="password", label="API Key (Optional / Pre-filled from .env)")
                custom_url_input = gr.Textbox(value="https://api.openai.com/v1", label="Custom Base URL (For Custom URL Provider)")
                
                dub_btn = gr.Button("Start AI Movie Dubbing Pipeline", variant="primary")

            with gr.Column():
                output_video = gr.Video(label="Dubbed Output Video")
                output_srt = gr.File(label="Generated Bilingual Subtitles (.srt)")
                status_box = gr.Textbox(label="Execution Status Log", lines=6)

        dub_btn.click(
            fn=run_dubbing,
            inputs=[input_video, target_lang, keep_music, provider_select, api_key_input, custom_url_input],
            outputs=[output_video, output_srt, status_box],
        )

    return app


def launch_web_ui(port: int = 7860, share: bool = False) -> None:
    """Launch interactive Web UI server."""
    app = create_web_app()
    if app is None:
        from aidub.ui.html_server import run_html_studio_server
        run_html_studio_server(port=port)
    else:
        app.launch(server_name="0.0.0.0", server_port=port, share=share)


__all__ = ["create_web_app", "launch_web_ui"]
