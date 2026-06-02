from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, write_transcript

load_lab_env(ROOT)

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

PROVIDER_MODELS: dict[str, list[str]] = {
    "openrouter": [
        "openai/gpt-4o-mini",
        "openai/gpt-4o",
        "anthropic/claude-3-5-haiku",
        "anthropic/claude-3-5-sonnet",
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.1-8b-instruct",
    ],
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "anthropic": ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"],
    "gemini": ["gemini-1.5-flash", "gemini-1.5-pro"],
}

SNAPSHOT_DIR = ARTIFACTS_DIR / "snapshots"


def list_versions() -> list[str]:
    versions = ["(current)"]
    if SNAPSHOT_DIR.exists():
        snaps = sorted({p.stem.replace("system_prompt_", "") for p in SNAPSHOT_DIR.glob("system_prompt_*.md")})
        versions += snaps
    return versions


def load_artifacts(version: str) -> tuple[str, Path, Path]:
    if version == "(current)":
        prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
    else:
        prompt_path = SNAPSHOT_DIR / f"system_prompt_{version}.md"
        tools_path = SNAPSHOT_DIR / f"tools_{version}.yaml"
        if not prompt_path.exists():
            prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        if not tools_path.exists():
            tools_path = ARTIFACTS_DIR / "tools.yaml"
    return prompt_path.read_text(encoding="utf-8"), prompt_path, tools_path


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.tool-call-box { background:#1e2a3a; border-left:3px solid #4a9eff; padding:8px 12px; border-radius:4px; margin:4px 0; font-size:0.85rem; }
.tool-result-box { background:#1a2e1a; border-left:3px solid #4ade80; padding:8px 12px; border-radius:4px; margin:4px 0; font-size:0.85rem; }
.status-badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("Provider")
    provider_name = st.selectbox("Provider", list(PROVIDER_MODELS.keys()), index=0)
    model_options = PROVIDER_MODELS[provider_name]
    model_choice = st.selectbox("Model", model_options)
    custom_model = st.text_input("Custom model (override)", placeholder="leave blank to use above")
    final_model = custom_model.strip() or model_choice

    st.divider()
    st.subheader("Artifacts")
    version_label = st.selectbox("Version", list_versions())
    system_prompt_text, prompt_path, tools_path = load_artifacts(version_label)

    with st.expander("📄 System Prompt", expanded=False):
        edited_prompt = st.text_area("System Prompt", value=system_prompt_text, height=300, label_visibility="collapsed")

    st.divider()
    st.subheader("Chat Settings")
    history_window = st.slider("History window (turns)", 1, 10, 5)
    max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)
    max_tokens = st.slider("Max tokens (giảm nếu hết credit)", 512, 8192, 2048, step=256)

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.transcript_turns = []
        st.rerun()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transcript_turns" not in st.session_state:
    st.session_state.transcript_turns = []
if "transcript_id" not in st.session_state:
    st.session_state.transcript_id = datetime.now().strftime("ui_%Y%m%dT%H%M%S%f")

# ── Header ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🔬 Research Agent")
    st.caption(f"Provider: **{provider_name}** · Model: **{final_model}** · Version: **{version_label}**")
with col2:
    tool_declarations = load_tool_declarations(tools_path)
    st.metric("Tools loaded", len(tool_declarations))

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                with st.expander(f"🔧 `{tc['name']}` — tool call", expanded=False):
                    st.code(json.dumps(tc["args"], ensure_ascii=False, indent=2), language="json")
        if msg.get("tool_results"):
            for tr in msg["tool_results"]:
                with st.expander(f"✅ `{tr['tool']}` — result", expanded=False):
                    st.code(json.dumps(tr.get("result", {}), ensure_ascii=False, indent=2), language="json")

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Nhập câu hỏi của bạn...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        _paper_keywords = {"paper", "bài báo", "arxiv", "research", "nghiên cứu", "publication", "journal", "cite"}
        _is_paper_query = any(kw in user_input.lower() for kw in _paper_keywords)
        _spinner_msg = "Đang tìm kiếm paper, có thể mất 20–60 giây..." if _is_paper_query else "Đang xử lý..."
        with st.spinner(_spinner_msg):
            try:
                provider = make_provider(provider_name)
                openai_tools = to_openai_tools(tool_declarations)

                history = []
                for m in st.session_state.messages[:-1]:
                    if m["role"] in ("user", "assistant"):
                        history.append({"role": m["role"], "content": m["content"]})

                window = history[-(history_window * 2):]
                messages = [
                    {"role": "system", "content": edited_prompt},
                    *window,
                    {"role": "user", "content": user_input},
                ]

                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=final_model,
                    max_tool_rounds=max_tool_rounds,
                    max_tokens=max_tokens,
                )

                assistant_text = result["assistant_text"]
                tool_events = result.get("tool_events", [])
                rounds = result.get("rounds", [])

                # Collect all tool calls across rounds
                all_tool_calls = []
                for r in rounds:
                    all_tool_calls.extend(r.get("tool_calls", []))

                st.markdown(assistant_text or "*(agent gọi tool, không có text trả lời)*")

                if all_tool_calls:
                    for tc in all_tool_calls:
                        with st.expander(f"🔧 `{tc['name']}` — tool call", expanded=False):
                            st.code(json.dumps(tc.get("args", {}), ensure_ascii=False, indent=2), language="json")

                if tool_events:
                    for tr in tool_events:
                        with st.expander(f"✅ `{tr['tool']}` — result", expanded=True):
                            st.code(json.dumps(tr.get("result", {}), ensure_ascii=False, indent=2), language="json")

                # Status badge
                status = result.get("status", "")
                if status == "waiting_for_user":
                    st.info("💬 Agent đang chờ thông tin bổ sung từ bạn")

                # Save to session
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text or "",
                    "tool_calls": all_tool_calls,
                    "tool_results": tool_events,
                })

                # Save transcript turn
                turn_record = {
                    "turn_index": len(st.session_state.transcript_turns) + 1,
                    "user": user_input,
                    "status": status,
                    "assistant_text": assistant_text,
                    "rounds": rounds,
                    "tool_events": tool_events,
                }
                st.session_state.transcript_turns.append(turn_record)

                # Write transcript JSON
                artifact_version = build_artifact_version(version_label, prompt_path, tools_path)
                transcript = {
                    "transcript_id": st.session_state.transcript_id,
                    **artifact_version_dict(artifact_version),
                    "provider": provider_name,
                    "model": final_model,
                    "source": "streamlit_ui",
                    "turns": st.session_state.transcript_turns,
                }
                transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"
                write_transcript(transcript_path, transcript)

            except Exception as exc:
                st.error(f"❌ Lỗi: {type(exc).__name__}: {exc}")
