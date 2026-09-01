import os
import sys
import tempfile
import pytest

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_brief_agents_core as core


def test_scan_markdown_sections():
    sample = """# Main Title
Intro line.

## Section 1: General Principles
- Maintain clean, readable code.
- Obey existing patterns.

### Subsection 1.1: Git Workflow
Do not commit directly to main.
"""
    sections = core.scan_markdown_sections(sample)
    assert len(sections) == 2
    assert sections[0][0] == "Section 1: General Principles"
    assert "Maintain clean" in sections[0][1]
    assert sections[1][0] == "Subsection 1.1: Git Workflow"
    assert "Do not commit directly" in sections[1][1]


def test_build_and_save_index():
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = os.path.join(tmpdir, "home")
        workspace_dir = os.path.join(tmpdir, "workspace")
        rules_dir = os.path.join(home_dir, ".gemini", "config", "rules")
        os.makedirs(rules_dir, exist_ok=True)
        os.makedirs(workspace_dir, exist_ok=True)

        # Create dummy global rule
        rule_file = os.path.join(rules_dir, "user_global.md")
        with open(rule_file, "w", encoding="utf-8") as f:
            f.write("## Rules\nFollow project conventions.\n")

        # Create dummy workspace GEMINI.md
        ws_file = os.path.join(workspace_dir, "GEMINI.md")
        with open(ws_file, "w", encoding="utf-8") as f:
            f.write("## Workspace Directives\nTest everything thoroughly.\n")

        index_file = os.path.join(home_dir, ".gemini", "agent-briefing-index.md")
        fp_file = os.path.join(home_dir, ".gemini", ".brief-fp")

        os.environ["AGY_HOME_OVERRIDE"] = home_dir
        os.environ["AGY_GLOBAL_RULES_DIR"] = rules_dir
        os.environ["AGY_BRIEFING_INDEX_FILE"] = index_file
        os.environ["AGY_FINGERPRINT_FILE"] = fp_file

        try:
            out_path, rebuilt = core.build_and_save_index(workspace_dir, force=False)
            assert rebuilt is True
            assert os.path.isfile(out_path)

            content = core.read_text(out_path)
            assert "Antigravity Agent Briefing Index" in content
            assert "user_global.md" in content
            assert "Follow project conventions" in content
            assert "GEMINI.md" in content
            assert "Test everything thoroughly" in content

            # Second call without changes should not rebuild
            _, rebuilt2 = core.build_and_save_index(workspace_dir, force=False)
            assert rebuilt2 is False

            # Prompt formatting helper
            prompt = core.format_subagent_prompt("Refactor database adapter", workspace_dir)
            assert "[Context Briefing: Refer to" in prompt
            assert "Refactor database adapter" in prompt
        finally:
            os.environ.pop("AGY_HOME_OVERRIDE", None)
            os.environ.pop("AGY_GLOBAL_RULES_DIR", None)
            os.environ.pop("AGY_BRIEFING_INDEX_FILE", None)
            os.environ.pop("AGY_FINGERPRINT_FILE", None)
