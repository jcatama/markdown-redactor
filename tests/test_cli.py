from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from markdown_redactor.cli import main


def test_cli_reads_file_writes_stdout(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("email jane@example.com", encoding="utf-8")

    exit_code = main([str(input_file)])

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "[REDACTED]" in out
    assert "jane@example.com" not in out


def test_cli_writes_output_file(tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    output_file = tmp_path / "out.md"
    input_file.write_text("ip 192.168.1.1", encoding="utf-8")

    exit_code = main([str(input_file), "-o", str(output_file)])

    assert exit_code == 0
    text = output_file.read_text(encoding="utf-8")
    assert "192.168.1.1" not in text


def test_cli_inline_code_flag(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("`ghp_ABCDEF1234567890`", encoding="utf-8")

    default_exit = main([str(input_file)])
    default_out = capsys.readouterr().out  # type: ignore[attr-defined]

    flagged_exit = main([str(input_file), "--redact-inline-code"])
    flagged_out = capsys.readouterr().out  # type: ignore[attr-defined]

    assert default_exit == 0
    assert flagged_exit == 0
    assert "ghp_ABCDEF1234567890" in default_out
    assert "ghp_ABCDEF1234567890" not in flagged_out


def test_cli_stdin_input(capsys: object, monkeypatch: object) -> None:
    monkeypatch.setattr("sys.stdin", StringIO("jane@example.com"))  # type: ignore[attr-defined]

    exit_code = main(["-"])

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "jane@example.com" not in out
    assert "[REDACTED]" in out


def test_cli_stats_to_stderr(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("jane@example.com", encoding="utf-8")

    exit_code = main([str(input_file), "--stats"])

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    stats = json.loads(captured.err)
    assert exit_code == 0
    assert isinstance(stats["total_matches"], int)
    assert "rule_matches" in stats
    assert "elapsed_ms" in stats


def test_cli_returns_error_code_for_missing_file(capsys: object) -> None:
    exit_code = main(["does-not-exist.md"])

    err = capsys.readouterr().err  # type: ignore[attr-defined]
    assert exit_code == 2
    assert "markdown-redactor:" in err


def test_cli_replacement_mode_preserve_format(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("Phone +1 (415) 555-2671", encoding="utf-8")

    exit_code = main([str(input_file), "--replacement-mode", "preserve_format"])

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "+X (XXX) XXX-XXXX" in out


def test_cli_allowlist_preserves_exact_value(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("email jane@example.com ip 10.0.0.1", encoding="utf-8")

    exit_code = main([str(input_file), "--allowlist", "jane@example.com"])

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "jane@example.com" in out
    assert "10.0.0.1" not in out


def test_cli_enable_rule_limits_active_rules(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("email jane@example.com ip 10.0.0.1", encoding="utf-8")

    exit_code = main([str(input_file), "--enable-rule", "email"])

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "jane@example.com" not in out
    assert "10.0.0.1" in out


def test_cli_disable_rule_skips_selected_rule(capsys: object, tmp_path: Path) -> None:
    input_file = tmp_path / "in.md"
    input_file.write_text("email jane@example.com ip 10.0.0.1", encoding="utf-8")

    exit_code = main([str(input_file), "--disable-rule", "email"])

    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert exit_code == 0
    assert "jane@example.com" in out
    assert "10.0.0.1" not in out
