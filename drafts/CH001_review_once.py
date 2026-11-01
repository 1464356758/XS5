#!/usr/bin/env python3
"""One-shot, author-requested CH001 evidence assembly.
All literary judgments and exact excerpts are authored in the immutable
manual-review JSON. This program only binds those statements to source SHA,
checks their occurrence, and refuses missing or stale evidence. No AI calls.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, "tools")
import novel_state as ns

BODY = Path("drafts/CH001_未审全文.txt")
SPEC = Path("drafts/CH001_人工审读规格.json")
RECORD = Path("drafts/CH001_章后记录.json")
PENDING = Path("drafts/CH001_release_pending.json")
REVIEW = Path("drafts/CH001_发布前审读报告.json")
BOOK_ID = "2b285e23-d842-4102-9f56-c55a1d6357b0"
TEXT_SHA = "2d5552763abb28d8f475b594cbabb767881378836b09aec56b4c60c3fbb433f6"

state = ns.load_state("book")
ns.verify_files("book",state)
spec = ns.read_json(SPEC)
text = BODY.read_text(encoding="utf-8")
assert state["book_id"] == BOOK_ID, "book_id changed"
assert state["revision"] == 3 and not state["chapters"], "already adopted or version changed"
assert set(state["inputs"]) == {"canon","roadmap"}
assert state["tasks"]["1"]["phase"] == "candidate"
assert state["tasks"]["1"]["repairs"] == 0
assert ns.digest(text) == TEXT_SHA == state["tasks"]["1"]["candidate_sha256"]
assert ns.han_count(text) == 9594, "unexpected manuscript revision"
assert spec["record"]["title"] == "印比雨先到" and len(spec["record"]["facts"]) >= 8

def ev(quote):
    assert isinstance(quote,str) and len(quote) > 3 and quote in text, f"quote absent: {quote}"
    return {"chapter":1,"sha256":TEXT_SHA,"quote":quote}

if len(sys.argv) != 2 or sys.argv[1] not in ("record", "review"):
    raise SystemExit("usage: ch001_review_once.py record|review")

if sys.argv[1] == "record":
    record = spec["record"]
    data = {
      "chapter":1,
      "title":record["title"],
      "stage":record["stage"],
      "base_revision":state["revision"],
      "canon_sha256":state["inputs"]["canon"]["sha256"],
      "text_sha256":TEXT_SHA,
      "complete":True,
      "story_time_end":record["story_time_end"],
      "summary":record["summary"],
      "review":{
          "read_full_text":True,
          "decision":"adopt",
          "blocking_issues":[],
          "sources_checked":[],
          "conclusion":record["review_conclusion"] +
            "；same_context_approximation：非独立读者测试。"
      },
      "facts":[],
      "progression":record["progression"],
      "thread_events":[],
      "stage_closing":False,
    }
    for kind,key,value,holder,start,quote in record["facts"]:
        ev(quote)
        data["facts"].append({"kind":kind,"key":key,"value":value,"holder":holder,
                  "valid_from":start,"valid_until":None,"quote":quote})
    for thread in record["threads"]:
        ev(thread["quote"])
        data["thread_events"].append({k:thread[k] for k in ("id","action","description","quote")})
    ns.atomic_json(RECORD,data)
    ns.validate_record("book",state,text,data)
    print("MANUAL_RECORD_EVIDENCE_PASS",len(data["facts"]),len(data["thread_events"]),TEXT_SHA)
else:
    assert RECORD.exists() and PENDING.exists(), "first generate actual pending template"
    record = ns.read_json(RECORD)
    report = ns.read_json(PENDING)
    assert report["text_sha256"] == TEXT_SHA and report["base_revision"] == state["revision"]
    src = spec["release"]
    report.update(decision="release",read_full_text=True,blocking_issues=[],
        reader_reason_to_continue=src["reason_to_continue"],
        consequence=src["consequence"],
        ending_runway=src["ending_runway"])
    expected_checks = tuple(ns.serial_module().CHECKS)
    assert set(src["checks"]) == set(expected_checks)
    for key in expected_checks:
        first,second,judgment = src["checks"][key]
        report["checks"][key]={"decision":"pass","conclusion":judgment,
            "evidence":[ev(first),ev(second)]}
    assert list(map(lambda x:x["chapter"],report["future_window"])) == [2,3,4]
    report["future_window"]=[
        {"chapter":n,"goal":goal,"change":change,"ending_question":question}
        for n,goal,change,question in src["future_window"]]
    for key,quote,why in src["opening"]:
        ev(quote)
        report["opening"][key] = {"quote":quote,"why":why}
    expected_promises = {x["id"]:x for x in spec["record"]["threads"]}
    assert set(expected_promises) == {x["id"] for x in report["promise_reviews"]}
    for review in report["promise_reviews"]:
        promise = expected_promises[review["id"]]
        review.update(action="set",deadline_chapter=promise["deadline"],
            reason=promise["description"] + "；当前仍未完成，不更改历史到期。",
            evidence=ev(promise["quote"]))
    assert not report["incident_actions"] and not report["comparison"]
    n=spec["narrative"]
    nav=report["narrative_review"]
    nav["actual_scenes"]=[
        {"event":event,"choice":choice,"change":change,"evidence":[ev(quote)]}
        for event,choice,change,quote in n["scenes"]]
    nav["plan_comparison"]=n["plan_comparison"]
    reader=n["reader"]
    nav["reader"].update(
        mode=reader["mode"],limitation=reader["limitation"],
        understanding=reader["understanding"],
        information_load=reader["information_load"],
        promise_delivery=reader["promise_delivery"],
        evidence=[ev(q) for q in reader["quotes"]],
        issues=[{"severity":x["severity"],"status":x["status"],
             "reason":x["reason"],"evidence":ev(x["quote"])} for x in reader["issues"]]
    )
    char=n["character"]
    for key in ("opposition","dialogue","aftermath"):
        first,second,conclusion=char[key]
        nav["character_causality"][key]={"status":"reviewed","conclusion":conclusion,
                   "evidence":[ev(first),ev(second)]}
    nav["history"].update(queries=[],comparisons=[],no_match_reason=n["history_reason"])
    nav["reader_updates"]=[
        {"kind":kind,"statement":statement,"evidence":[ev(quote)]}
        for kind,statement,quote in n["updates"]]
    nav["reader_update_note"]=n["reader_update_note"]
    assert nav["surface_findings"] == ns.narrative_module().surface_scan(text) == []
    ns.atomic_json(REVIEW,report)
    print("MANUAL_RELEASE_EVIDENCE_ASSEMBLED",
          "checks",list(report["checks"]),"scenes",len(nav["actual_scenes"]),
          "reader-mode",nav["reader"]["mode"],
          "issues",[(x["severity"],x["status"]) for x in nav["reader"]["issues"]])
