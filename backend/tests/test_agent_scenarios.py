"""End-to-end co-pilot scenarios on the demo data (demo SOPs, stock lots and fixes).

Covered elsewhere: number mismatch, prompt injection, LLM failure, tool timeout and budget
(test_agent_guardrails.py); path traversal (test_agent_tools.py, test_agent_api.py);
cross-organisation access (test_agent_tools.py, test_agent_api.py).
"""
from __future__ import annotations

import json
import re

import pytest

from app import create_app
from app.agents.orchestrator import PLAN_SCHEMA, AgentLimits, Orchestrator
from app.agents.tools import ToolEnv
from app.config import TestConfig
from tests.conftest import FakeLLM

UNCERTAIN = "Insufficient evidence in the uploaded SOPs. Consult lab supervisor."


@pytest.fixture()
def demo_app(tmp_path):
    return create_app(TestConfig, DATA_DIR=tmp_path, DATABASE_PATH=tmp_path / "demo.db", UPLOAD_DIR=tmp_path / "uploads",
                      INDEX_DIR=tmp_path / "index", SEED_AGENT_DEMO=True)


def ask(app, question, llm=None, **kw):
    llm = llm or FakeLLM(fail=True)  # offline: rules-based plan, verbatim SOP sentences
    return Orchestrator(ToolEnv.from_app(app), llm, AgentLimits()).run(question, **kw)


def passages(content) -> dict[str, str]:
    text = content[0]["text"]
    return dict(re.findall(r'<untrusted_sop_passage chunk_id="([^"]+)"[^>]*>\n(.*?)\n</untrusted_sop_passage>', text, re.S))


def calcs(content) -> list[dict]:
    text = content[0]["text"]
    return [json.loads(b) for b in re.findall(r'<tool_output name="calculate_preparation">\n(.*?)\n</tool_output>', text, re.S)]


def grounded_llm(plan: dict, extra_step: str | None = None, mass_override: str | None = None) -> FakeLLM:
    """An LLM that plans as given and writes only steps copied from the passages and the calculator."""
    def respond(system, content, schema):
        if schema is PLAN_SCHEMA:
            return plan
        chunks = passages(content)
        first = next(iter(chunks))
        steps = [{"action": f"Weigh {mass_override or c['mass']} of {c['compound']}.", "safety_note": "",
                  "chunk_ids": [first], "required": True} for c in calcs(content)]
        if extra_step:
            cid = next(cid for cid, t in chunks.items() if extra_step in " ".join(t.split()))
            steps.append({"action": extra_step, "safety_note": "Hydrochloric acid is corrosive: add it slowly, in a "
                          "fume hood, and never add water to concentrated acid.", "chunk_ids": [cid], "required": True})
        return {"summary": "Checklist assembled from the uploaded SOP and the calculation.",
                "insufficient_evidence": False, "missing": "", "checklist": steps}
    return FakeLLM(json_result=respond)


def prep_plan(components, volume, unit, reagents=None):
    return {"intent": "preparation", "search_query": "buffer preparation " + " ".join(c[0] for c in components),
            "components": [{"compound": n, "target_concentration": v, "concentration_unit": u} for n, v, u in components],
            "volume": volume, "volume_unit": unit, "reagents": reagents or [c[0] for c in components], "error_code": ""}


TNE = "Prepare 1 L of TNE buffer: 50 mM Tris base, 150 mM NaCl and 1 mM EDTA disodium salt dihydrate"
TNE_PLAN = prep_plan([("Tris base", 50, "mM"), ("NaCl", 150, "mM"), ("EDTA disodium salt dihydrate", 1, "mM")], 1, "L")
PH_STEP = "Adjust the pH to 8.0 by adding hydrochloric acid dropwise while stirring."


def test_fully_supported_run(demo_app):
    r = ask(demo_app, TNE, grounded_llm(TNE_PLAN, extra_step=PH_STEP))
    assert r["status"] == "supported", (r["blockers"], r["cautions"])
    assert r["confidence"] >= 0.7 and not r["uncertainty_flag"] and r["uncertainty_message"] == ""
    assert [s["unsupported"] for s in r["checklist"]] == [False] * 4
    assert r["checklist"][0]["action"] == "Weigh 6.057 g of Tris base."
    assert {i["reagent"] for i in r["inventory_status"]} == {"Tris base", "Sodium chloride", "EDTA disodium salt dihydrate"}
    assert all(i["available"] and i["sufficient"] for i in r["inventory_status"])
    assert {p["result"] for p in r["compatibility"]} == {"no_known_issue"}
    assert r["compatibility_label"] == "Limited demo matrix, not expert-reviewed."
    cited = {c["chunk_id"] for c in r["citations"]}
    assert all(set(s["chunk_ids"]) <= cited for s in r["checklist"])
    assert r["response"].startswith("**Supported by uploaded SOP**")
    assert "verified" not in r["response"].lower()
    steps = [t["step"] for t in r["agent_trace"]]
    for stage in ("Plan", "Retrieve", "Calculate", "Stock check", "Compatibility check", "Synthesize", "Verify"):
        assert stage in steps
    assert steps.index("Retrieve") < steps.index("Calculate") < steps.index("Stock check") \
        < steps.index("Compatibility check") < steps.index("Synthesize") < steps.index("Verify")


def test_offline_run_is_caution_with_verbatim_steps(demo_app):
    r = ask(demo_app, TNE)
    assert r["status"] == "caution" and all(not s["unsupported"] for s in r["checklist"])
    assert any("language model" in c for c in r["cautions"])
    assert r["calculations"][0]["mass"] == "6.057 g"


@pytest.mark.parametrize("question, blocker", [
    ("Prepare 500 mL of 10 mM magnesium chloride hexahydrate", "missing"),
    ("Prepare 1 L of 20 mM Tris-HCl", "expired"),
    ("Prepare 1 L of 1 M KCl", "Insufficient stock"),
    ("Prepare 500 mL of 1% w/v sodium hypochlorite in 70% ethanol", "Incompatible pair"),
    ("Prepare 1 L of 1 M PBS", "Molecular weight"),
    ("Prepare 100 mL of 1 M Tris", "more than one compound"),
])
def test_blocking_scenarios_are_refused_with_the_exact_blocker(demo_app, question, blocker):
    r = ask(demo_app, question)
    assert r["status"] == "refused"
    assert any(blocker in b for b in r["blockers"]), r["blockers"]
    assert r["checklist"] == []  # nothing to follow
    assert "Blocked by" in r["response"]


def test_incompatible_pair_reports_the_pair(demo_app):
    r = ask(demo_app, "Prepare 500 mL of 1% w/v sodium hypochlorite in 70% ethanol")
    pair = r["compatibility"][0]
    assert pair["result"] == "incompatible" and set(pair["pair"]) == {"Sodium hypochlorite", "Ethanol"}


def test_missing_molecular_weight_never_guesses_a_mass(demo_app):
    r = ask(demo_app, "Prepare 1 L of 1 M PBS")
    assert r["uncertainty_flag"] and r["uncertainty_message"] == UNCERTAIN
    assert r["calculations"] == [] and " g " not in r["response"]


def test_unknown_pair_is_caution_not_safe(demo_app):
    q = "Prepare 1 L of 50 mM Tris base with 10% acetonitrile"
    plan = prep_plan([("Tris base", 50, "mM")], 1, "L", reagents=["Tris base", "acetonitrile"])
    r = ask(demo_app, q, grounded_llm(plan))
    assert r["status"] == "caution", r["blockers"]
    assert r["compatibility"][0]["result"] == "unknown"
    assert any("unknown does not mean safe" in c for c in r["cautions"])


def test_expiring_and_low_stock_are_non_blocking_cautions(demo_app):
    q = "Prepare 1 L of running buffer with 25 mM Tris base, 192 mM glycine and 0.1% w/v SDS"
    plan = prep_plan([("Tris base", 25, "mM"), ("glycine", 192, "mM"), ("SDS", 0.1, "% w/v")], 1, "L")
    r = ask(demo_app, q, grounded_llm(plan))
    assert r["status"] == "caution"
    assert any("expires soon" in c for c in r["cautions"]) and any("reorder threshold" in c for c in r["cautions"])


def test_mass_mismatch_from_the_model_is_flagged(demo_app):
    r = ask(demo_app, TNE, grounded_llm(TNE_PLAN, mass_override="6.5 g"))
    assert r["status"] == "refused" and r["uncertainty_flag"]
    assert all(s["unsupported"] for s in r["checklist"]) and r["checklist_label"].startswith("Do not follow")


def test_unanswerable_question_is_refused(demo_app):
    r = ask(demo_app, "What is the IC50 of compound XJ-9921 against kinase ABL?")
    assert r["status"] == "refused" and r["uncertainty_message"] == UNCERTAIN
    assert r["checklist"] == [] and r["citations"] == []
    assert "nM" not in r["response"]


def test_demo_troubleshooting_entry_with_ppe(demo_app):
    r = ask(demo_app, "How do I fix CAL-02 on the pH meter?")
    assert r["diagnosis"]["machine_model"].startswith("PHM-200")
    assert "safety glasses" in r["diagnosis"]["ppe_warnings"][0]
    assert all(not s["unsupported"] for s in r["checklist"])


def test_inventory_lookup(demo_app):
    r = ask(demo_app, "Do we have SDS in stock?")
    assert r["intent"] == "inventory" and r["inventory_status"][0]["expiring_soon"]
    assert r["status"] == "caution"
