"""
Simulate 3 live chat scenarios as required by README Step 5.
Saves transcript to transcripts/ directory.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, write_transcript

load_lab_env(ROOT)

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

SCENARIOS = [
    # Scenario 1: Normal research request
    [
        "Tìm tin tức nổi bật về AI hôm nay"
    ],
    # Scenario 2: Missing info → user provides it next turn
    [
        "Tóm tắt bài viết này hộ tôi",
        "https://openai.com/research/",
        "Chỉ đọc đúng link đó thôi nhé"
    ],
    # Scenario 3: Send to Telegram — observe confirm behavior
    [
        "Đăng bản tin AI hôm nay lên Telegram giúp tôi",
        "Có, xác nhận gửi đi nhé"
    ],
]


def run_scenario(
    provider,
    system_prompt: str,
    openai_tools: list,
    turns: list[str],
    scenario_idx: int,
) -> list[dict]:
    history = []
    records = []
    print(f"\n{'='*60}")
    print(f"Scenario {scenario_idx + 1}")
    print('='*60)

    for turn_text in turns:
        print(f"\n>> User: {turn_text}")
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": turn_text},
        ]
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=None,
            max_tool_rounds=4,
        )
        assistant_text = result["assistant_text"] or ""
        tool_events = result.get("tool_events", [])
        rounds = result.get("rounds", [])

        all_calls = []
        for r in rounds:
            all_calls.extend(r.get("tool_calls", []))

        if all_calls:
            print(f"   [tools] {[c['name'] for c in all_calls]}")
        print(f"<< Agent: {assistant_text[:200]}{'...' if len(assistant_text) > 200 else ''}")

        history.append({"role": "user", "content": turn_text})
        history.append({"role": "assistant", "content": assistant_text})

        records.append({
            "user": turn_text,
            "status": result.get("status"),
            "assistant_text": assistant_text,
            "tool_calls": all_calls,
            "tool_events": tool_events,
            "rounds": rounds,
        })

    return records


def main():
    provider_name = "openrouter"
    version_label = "v3"
    prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"

    system_prompt = prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(provider_name)
    artifact_version = build_artifact_version(version_label, prompt_path, tools_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = f"live_{version_label}_{provider_name}_{timestamp}"
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    all_turns = []
    turn_index = 0
    for i, scenario_turns in enumerate(SCENARIOS):
        records = run_scenario(provider, system_prompt, openai_tools, scenario_turns, i)
        for rec in records:
            turn_index += 1
            all_turns.append({
                "turn_index": turn_index,
                "scenario": i + 1,
                **rec,
            })

    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "source": "scripted_live_simulation",
        "scenarios": len(SCENARIOS),
        "turns": all_turns,
    }
    write_transcript(transcript_path, transcript)
    print(f"\n\nTranscript saved: {transcript_path}")
    return str(transcript_path)


if __name__ == "__main__":
    main()
