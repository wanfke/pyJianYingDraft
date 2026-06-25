import json
from pathlib import Path

import pyJianYingDraft as draft
import pytest

from pyJianYingDraft.exceptions import DraftContentLoadFailed


def _create_template_draft(tmp_path: Path, draft_name: str) -> Path:
    folder = draft.DraftFolder(str(tmp_path))
    script = folder.create_draft(draft_name, 1920, 1080)
    script.save()
    return tmp_path / draft_name / "draft_content.json"


def test_load_template_raises_stable_error_for_non_plain_content_without_fallback_loader(tmp_path):
    draft_content_path = _create_template_draft(tmp_path, "custom_format_template")
    draft_content_path.write_bytes(b"\x80not-json")

    folder = draft.DraftFolder(str(tmp_path))

    with pytest.raises(DraftContentLoadFailed):
        folder.load_template("custom_format_template")


def test_load_template_uses_fallback_loader_for_non_plain_content(tmp_path):
    draft_content_path = _create_template_draft(tmp_path, "custom_format_template")
    plain_content = draft_content_path.read_text(encoding="utf-8")
    raw_payload = b"custom payload"
    draft_content_path.write_bytes(raw_payload)

    seen = {}

    def fallback_loader(raw_data: bytes) -> str:
        seen["raw_data"] = raw_data
        return plain_content

    folder = draft.DraftFolder(str(tmp_path), fallback_loader=fallback_loader)
    script = folder.load_template("custom_format_template")

    assert seen["raw_data"] == raw_payload
    assert script.width == 1920
    assert script.height == 1080
    assert script.save_path == str(draft_content_path)


def test_load_template_accepts_dict_from_fallback_loader(tmp_path):
    draft_content_path = _create_template_draft(tmp_path, "custom_format_template")
    plain_content = draft_content_path.read_text(encoding="utf-8")
    draft_content_path.write_bytes(b"custom payload")

    folder = draft.DraftFolder(
        str(tmp_path),
        fallback_loader=lambda _: json.loads(plain_content),
    )
    script = folder.load_template("custom_format_template")

    assert script.width == 1920
    assert script.height == 1080


def test_duplicate_as_template_reuses_fallback_loader(tmp_path):
    draft_content_path = _create_template_draft(tmp_path, "custom_format_template")
    plain_content = draft_content_path.read_text(encoding="utf-8")
    draft_content_path.write_bytes(b"custom payload")

    folder = draft.DraftFolder(str(tmp_path), fallback_loader=lambda _: plain_content)
    script = folder.duplicate_as_template("custom_format_template", "copied_template")

    assert script.save_path.endswith("copied_template\\draft_content.json")
    assert (tmp_path / "copied_template" / "draft_content.json").exists()
