"""XS5 manual chapter freeze: explicit request only; no schedule, no invented automation ID.

All literary evaluations are supplied in an authored evidence file; this runner only
binds them to immutable source hashes and uses the existing V4.3 validators.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import novel_state as ns
import narrative_quality as nq
import serial_release as sr
import online_state as oi

ROOT = Path("book")
BOOK = "5afdc2a3-0b3a-4e45-bbd0-f458aff8f3c3"
REQUEST = Path(".automation/manual_chapter_request.json")

def need(ok, message):
    if not ok:
        raise ValueError(message)

def bound(value, current, number):
    if isinstance(value, list):
        return [bound(x, current, number) for x in value]
    if isinstance(value, dict):
        v = {k: bound(x, current, number) for k, x in value.items()}
        if v.get("chapter") == number and v.get("sha256") == "CURRENT" and isinstance(v.get("quote"), str):
            v["sha256"] = current
        return v
    return value

def main():
    req = ns.read_json(REQUEST)
    need(req.get("schema_version") == 1 and req.get("book_id") == BOOK, "Wrong manual request or book.")
    chapter = req.get("chapter")
    need(type(chapter) is int and 1 <= chapter <= 100, "Invalid chapter.")
    number = f"CH{chapter:03d}"
    draft = Path(f"drafts/{number}_未审全文.txt")
    data_path = Path(f"drafts/{number}_审读数据.json")
    need(draft.is_file() and data_path.is_file(), "Missing chapter text or real editorial data.")
    need(req.get("author_instruction") in ("下一章", "继续下一章", "开始第一章", "写下一章"),
         "No explicit author command.")
    need(subprocess.check_output(["git", "hash-object", str(draft)], text=True).strip() ==
         req.get("draft_blob_sha"), "Full manuscript differs from authorized Git blob.")
    state = ns.load_state(ROOT)
    ns.verify_files(ROOT, state)
    need(state["book_id"] == BOOK and state["revision"] == req.get("expected_revision"),
         "State was changed since the author requested this chapter.")
    need(chapter == len(state["chapters"]) + 1 and str(chapter) not in state["serialization"]["frozen"]
         and str(chapter) not in state["tasks"], "Not the unique next unwritten chapter.")
    need(ns.read_json(".automation/config.json").get("automation_id") is None,
         "This project is not eligible for manual owner while an automation is bound.")
    wf = oi.load_workflow(".")
    need(wf["book_id"] == BOOK and wf["chapter"] == chapter and wf["phase"] in ("WAITING_NEXT", "PLANNING"),
         "Workflow does not await this chapter.")
    body = draft.read_text(encoding="utf-8")
    need(8000 <= ns.han_count(body) <= 10000, "Manuscript fails the chapter length gate.")
    need(not nq.surface_scan(body), "Manuscript includes unreviewed production markers.")
    editorial = ns.read_json(data_path)
    need(editorial["schema_version"] == 1 and editorial["book_id"] == BOOK and
         editorial["chapter"] == chapter and editorial["expected_han"] == ns.han_count(body),
         "Editorial material does not belong to full current manuscript.")
    sha = ns.digest(body)
    api = ns.serial_api()
    brief = nq.brief_skeleton(state, api)
    brief.update(editorial["brief"])
    brief_path = Path(f"drafts/{number}_写作任务书.json")
    ns.atomic_json(brief_path, brief)
    nq.check_brief(ROOT, brief_path, api)
    Path(f"drafts/{number}_writer_context.txt").write_text(
         ns.context(ROOT, profile="writer"), encoding="utf-8")
    ns.candidate(ROOT, chapter, draft)
    Path(f"drafts/{number}_reader_context.txt").write_text(
         ns.context(ROOT, profile="reader", text_path=draft), encoding="utf-8")
    record = bound(editorial["record"], sha, chapter)
    record.update(base_revision=state["revision"],
                  canon_sha256=state["inputs"]["canon"]["sha256"], text_sha256=sha)
    record_path = Path(f"drafts/{number}_章后事实记录.json")
    ns.atomic_json(record_path, record)
    ns.validate_record(ROOT, ns.load_state(ROOT), body, record)

    report = sr.skeleton(ROOT, ns.load_state(ROOT), body, record, api)
    evidence = bound(editorial["report"], sha, chapter)
    for key in ("decision", "read_full_text", "blocking_issues", "reader_reason_to_continue",
                "consequence", "ending_runway", "checks", "comparison", "future_window",
                "promise_reviews"):
        need(key in evidence, f"Missing independently authored editorial item: {key}")
        report[key] = evidence[key]
    nar = report["narrative_review"]
    authored = evidence["narrative_review"]
    for key in ("actual_scenes", "plan_comparison", "character_causality",
                "reader_updates", "reader_update_note"):
        need(key in authored, "Missing narrative judgment: " + key)
        nar[key] = authored[key]
    nar["reader"].update(authored["reader"])
    nar["history"].update(authored["history"])
    need(not nar["surface_findings"], "Review must address all production-scan findings.")
    report_path = Path(f"drafts/{number}_发布前实审报告.json")
    ns.atomic_json(report_path, report)
    sr.check(ROOT, draft, record_path, report_path, api)
    ns.adopt(ROOT, draft, record_path)

    wf = oi.load_workflow(".")
    need(wf["book_id"] == BOOK and wf["chapter"] == chapter, "Workflow changed during review.")
    wf["chapter"] = chapter + 1
    oi.write_workflow(".", wf, phase="WAITING_NEXT" if chapter < 100 else "CHECKPOINT",
        detail=f"{number}通过原V4.3八项与叙事release-check，已真实adopt冻结；咪咕发布未登记。",
        next_action=f"等待作者指令，继续CH{chapter+1:03d}；先读取全部已冻结正文与事实账。")
    oi.build_index(".")
    oi.validate_index(".")
    result = ns.load_state(ROOT)
    item = result["chapters"][str(chapter)]
    gate = result["serialization"]["gates"][str(chapter)]
    need(gate["used"] and result["serialization"]["frozen"][str(chapter)]["text_sha256"] ==
         item["text_sha256"] and item["text_sha256"] == sha, "Frozen proof mismatch.")
    need(str(chapter) not in result["serialization"]["published"], "No platform publication proof.")
    print(json.dumps({"status":"LOCKED","chapter":chapter,"han":item["han_count"],
                      "text_path":item["text_path"],"record_path":item["record_path"],
                      "gate_path":gate["path"],"text_sha256":sha},
                      ensure_ascii=False))

if __name__ == "__main__":
    main()
