"""Safety-first guardrails shared by the RAG and vision pipelines.

Two responsibilities:

* **Query screening** - flag questions asking for things the assistant must not
  answer from retrieved text alone (identifying unknown substances, medical
  advice/dosing for people, disabling safety interlocks).
* **Vision output sanitising** - the vision model may *describe* what is visible
  (colours, turbidity, text on a display, equipment parts) but must never assert
  the identity of a chemical, organism, contaminant or medical condition. Any
  sentence that does is redacted and replaced with a notice, and the response is
  flagged so the UI can show it.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

VISION_DISCLAIMER = (
    "Visual analysis describes observable features only. It does not identify chemicals, "
    "organisms, contaminants or medical conditions - confirm identity with validated analytical "
    "methods (e.g. HPLC, MS, PCR, culture) and your lab's SOPs."
)
REDACTION_NOTICE = "[Redacted: unverified identification - confirm with a validated analytical method.]"

# Substances, organisms and conditions the vision pipeline must never claim to identify.
_IDENTITY_LEXICON = [
    # chemicals / reagents
    r"acetone", r"ethanol", r"methanol", r"isopropanol", r"chloroform", r"benzene", r"toluene", r"xylene",
    r"formaldehyde", r"formalin", r"cyanide", r"arsenic", r"mercury", r"lead", r"acid", r"base", r"bleach",
    r"hypochlorite", r"peroxide", r"ammonia", r"phenol", r"dmso", r"trizol", r"guanidin\w*", r"sodium \w+",
    r"potassium \w+", r"hydrochloric", r"sulfuric", r"nitric", r"opioid\w*", r"fentanyl", r"cocaine",
    r"toxin\w*", r"poison\w*", r"explosive\w*", r"solvent", r"compound \w+",
    # organisms / contaminants
    r"e\.? ?coli", r"escherichia", r"salmonella", r"staphylococc\w*", r"streptococc\w*", r"pseudomonas",
    r"mycoplasma", r"bacteri\w*", r"fung\w*", r"yeast", r"mold", r"mould", r"virus\w*", r"viral",
    r"pathogen\w*", r"contaminat\w*", r"infect\w*", r"aspergillus", r"candida",
    # medical
    r"disease", r"diagnos\w*", r"cancer\w*", r"tumou?r\w*", r"malignan\w*", r"lesion\w*", r"symptom\w*",
    r"overdose", r"lethal", r"toxic\w*",
]
_IDENTITY = r"(?:" + "|".join(_IDENTITY_LEXICON) + r")"

# Assertive identification phrasing followed (within a few words) by an identity term.
_ASSERTION_PATTERNS = [
    rf"\b(?:this|it|the (?:sample|substance|liquid|powder|solid|culture|colony|colonies|growth|residue|precipitate|material|tissue))"
    rf"\s+(?:is|are|appears to be|looks like|seems to be|is likely|is probably|is most likely|contains|shows|indicates)\b[^.]{{0,60}}?\b{_IDENTITY}\b",
    rf"\b(?:identified|identify|identifies|consistent with|indicative of|diagnostic of|positive for|confirms?|confirmed)\b[^.]{{0,60}}?\b{_IDENTITY}\b",
    rf"\b(?:likely|probably|possibly|presumably|definitely|clearly)\s+(?:a |an |the )?{_IDENTITY}\b",
    rf"\b{_IDENTITY}\b[^.]{{0,30}}\b(?:is present|are present|detected|identified)\b",
]
_ASSERTION_RE = [re.compile(p, re.IGNORECASE) for p in _ASSERTION_PATTERNS]
# Sentence boundary: terminal punctuation followed by an upper-case start, so "E. coli" stays intact.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])|\n+")

# Query screening rules: (code, regex, user-facing warning)
_QUERY_RULES = [
    (
        "substance_identification",
        re.compile(r"\b(what|which|identify|tell me)\b.{0,40}\b(chemical|substance|compound|powder|liquid|"
                   r"contaminant|organism|bacteri\w*|microbe)\b.{0,30}\b(is (this|it)|in (this|the|that)( \w+)? "
                   r"(image|photo|picture|vial|tube|flask|bottle|container|sample|beaker))"
                   r"|\bwhat\b.{0,15}\b(is|are) (this|these|that)\b.{0,20}\b(powder|liquid|substance|chemical|"
                   r"crystals|residue|growth|colony|colonies)\b",
                   re.IGNORECASE),
        "SmartLab AI cannot identify unknown substances or organisms. Use validated analytical methods "
        "and treat unlabelled materials as hazardous per your chemical hygiene plan.",
    ),
    (
        "medical_advice",
        re.compile(r"\b(dose|dosage|dosing|mg/kg|administer|inject|ingest|swallow\w*|treat(ment)?|diagnos\w*)\b"
                   r".{0,40}\b(human|patient|person|people|me|myself|child|someone)\b|\b(i|someone|colleague) "
                   r"(was|got|have been|has been) (exposed|splashed|cut|burned|burnt)\b", re.IGNORECASE),
        "SmartLab AI does not give medical or dosing advice for people. For exposures follow your SDS "
        "first-aid section, use the eyewash/safety shower, and contact occupational health or emergency services.",
    ),
    (
        "safety_bypass",
        re.compile(r"\b(bypass|disable|override|defeat|turn off|jumper)\b.{0,40}\b(interlock|safety|alarm|"
                   r"sash|lid lock|sensor)\b", re.IGNORECASE),
        "Safety interlocks and alarms must not be bypassed. Contact the equipment owner or EHS.",
    ),
]


@dataclass
class GuardrailReport:
    flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    redactions: int = 0

    @property
    def blocked(self) -> bool:
        return bool(self.flags)

    def to_dict(self) -> dict:
        return {"flags": self.flags, "warnings": self.warnings, "redactions": self.redactions}


def screen_query(text: str) -> GuardrailReport:
    report = GuardrailReport()
    for code, pattern, warning in _QUERY_RULES:
        if pattern.search(text or ""):
            report.flags.append(code)
            report.warnings.append(warning)
    return report


def contains_identification(text: str) -> bool:
    return any(p.search(text or "") for p in _ASSERTION_RE)


def sanitize_vision_text(text: str, report: GuardrailReport | None = None) -> str:
    """Redact sentences that assert the identity of a substance, organism or condition."""
    report = report if report is not None else GuardrailReport()
    if not text:
        return text
    out: list[str] = []
    for sentence in _SENTENCE_SPLIT.split(text):
        if contains_identification(sentence):
            report.redactions += 1
            if out and out[-1] == REDACTION_NOTICE:
                continue
            out.append(REDACTION_NOTICE)
        else:
            stripped = sentence.strip()
            if stripped:
                out.append(stripped)
    if report.redactions and "unverified_identification_redacted" not in report.flags:
        report.flags.append("unverified_identification_redacted")
        report.warnings.append(
            "Part of the visual description was withheld because it attempted an unverified "
            "chemical, biological or medical identification."
        )
    return " ".join(out)


def sanitize_vision_result(result: dict, report: GuardrailReport) -> dict:
    """Apply :func:`sanitize_vision_text` to every free-text field of a vision result."""
    clean = dict(result)
    for key in ("visual_description", "equipment_type", "search_query"):
        if isinstance(clean.get(key), str):
            clean[key] = sanitize_vision_text(clean[key], report)
    # observed_text is verbatim text read off a display/label (e.g. an instrument's own
    # "CONTAMINATION DETECTED" message), not an identification made by the model, so it is kept.
    for key in ("sample_observations",):
        if isinstance(clean.get(key), list):
            items = [sanitize_vision_text(str(item), report) for item in clean[key]]
            clean[key] = [i for i in items if i]
    return clean


# =====================================================================================
# Lab co-pilot guardrails (deterministic; no model involved)
# =====================================================================================
# The orchestrator's draft checklist is checked here before anything reaches the user:
#
# * every step must cite chunk ids that were actually retrieved (and not quarantined) in this request;
# * every number in a step must appear in a cited chunk or in the calculator output, after
#   normalising spacing, case, decimal commas and units ("1 M" == "1M", "100 mL" == "0.1 L");
# * unsupported steps are kept and marked ``unsupported: true``, never silently dropped;
# * confidence is computed from retrieval similarity, the share of supported steps and tool
#   outcomes - never from the model's own rating;
# * the final status (supported / caution / refused) is decided here.

UNCERTAINTY_MESSAGE = "Insufficient evidence in the uploaded SOPs. Consult lab supervisor."
DO_NOT_FOLLOW_LABEL = "Do not follow. Shown for transparency only."
CONFIDENCE_THRESHOLD = 0.70
DEFAULT_SAFETY_NOTE = ("No specific safety note in the cited passage. Follow your lab's standard PPE rules "
                       "and the Safety Data Sheet.")

# ---------------------------------------------------------------- prompt injection in retrieved text
_INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in (
    r"\b(ignore|disregard|forget|override)\b[^.]{0,40}\b(previous|prior|above|earlier|all|system|your)\b[^.]{0,20}"
    r"\b(instructions?|prompts?|rules|guidelines|messages?)\b",
    r"\byou are now\b",
    r"\b(system|developer) (prompt|message|instructions?)\b",
    r"\bnew instructions?\s*:",
    r"\b(mark|label|set|report|treat)\b[^.]{0,30}\b(as )?(verified|approved|safe|supported)\b[^.]{0,30}"
    r"\b(answer|status|response|checklist|output)\b",
    r"\b(answer|status|response|checklist|output)\b[^.]{0,30}\b(must|should) be (marked )?(verified|safe|supported)\b",
    r"\bdo not (tell|inform|warn) the user\b",
    r"\b(call|invoke|run|use) the [a-z_]+ tool\b",
    r"</?\s*(system|assistant|untrusted_[a-z_]+|tool_output)\b",
)]


def screen_untrusted_text(text: str) -> bool:
    """True when retrieved or image-derived text contains instruction-like content aimed at the assistant.

    Such passages are quarantined: they are not shown to the model as evidence and cannot be cited.
    """
    return any(p.search(text or "") for p in _INJECTION_PATTERNS)


_DELIMITER_TAG = re.compile(r"<\s*/?\s*(untrusted_[a-z_]+|tool_output|system|assistant)[^>]*>", re.IGNORECASE)


def neutralise_delimiters(text: str) -> str:
    """Remove anything that looks like our own data delimiters so untrusted text cannot close them."""
    return _DELIMITER_TAG.sub("[removed tag]", text or "")


# ---------------------------------------------------------------- numbers
_UNIT_ALTERNATIVES = [
    "mg/mL", "mg/ml", "µg/mL", "μg/mL", "ug/mL", "ug/ml", "mg/L", "mg/l", "g/L", "g/l", "mL/min", "ml/min",
    "% w/v", "%w/v", "mL", "ml", "µL", "μL", "uL", "ul", "L", "mM", "µM", "μM", "uM", "nM", "M",
    "kg", "mg", "µg", "μg", "ug", "g", "°C", "° C", "C", "minutes", "minute", "mins", "min", "hours", "hour", "hrs",
    "hr", "h", "seconds", "second", "secs", "sec", "s", "rpm", "x g", "× g", "xg", "%", "bar", "mAU",
    "column volumes", "days", "day", "weeks", "week", "cm2", "nm", "um", "cells/mL",
]
_UNIT_RE = "|".join(re.escape(u) for u in sorted(_UNIT_ALTERNATIVES, key=len, reverse=True))
_NUM_RE = r"-?\d+(?:[.,]\d+)*"
_LEFT = r"(?<![A-Za-z0-9\-./^_,])"
_RANGE = re.compile(rf"{_LEFT}({_NUM_RE})\s*(?:to|-|–)\s*({_NUM_RE})\s*({_UNIT_RE})(?![A-Za-z])")
_SINGLE = re.compile(rf"{_LEFT}(pH\s*)?({_NUM_RE})(?:\s*({_UNIT_RE})(?![A-Za-z]))?")
_TIME_SECONDS = {"s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1, "min": 60, "mins": 60, "minute": 60,
                 "minutes": 60, "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
                 "day": 86400, "days": 86400, "week": 604800, "weeks": 604800}


@dataclass(frozen=True)
class Number:
    raw: str
    value: float
    kind: str | None  # dimension or literal unit; None when the number has no unit
    base: float  # value converted to the kind's base unit

    @property
    def sig_figs(self) -> int:
        return max(len(re.sub(r"[^0-9]", "", self.raw).lstrip("0")), 1)


def _parse_value(text: str) -> float | None:
    t = text.strip()
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t):
        t = t.replace(",", "")  # thousands separators
    elif t.count(",") == 1 and "." not in t:
        t = t.replace(",", ".")  # decimal comma
    try:
        return float(t)
    except ValueError:
        return None


def _canonical(value: float, unit: str | None, ph: bool = False) -> tuple[str | None, float]:
    from .agents import units  # local import: the agents package imports this module

    if ph:
        return "ph", value
    if not unit:
        return None, value
    u = unit.strip()
    if u in ("°C", "° C", "C"):
        return "temp_c", value
    low = u.lower()
    if low in _TIME_SECONDS:
        return "time", value * _TIME_SECONDS[low]
    if low.replace(" ", "") in ("xg", "×g"):
        return "rcf", value
    if low == "ml/min":
        return "flow_ml_min", value
    if u in ("nm", "um"):  # lengths (wavelength, pore size); molar units are written nM / uM
        return f"length_{u}", value
    try:
        return units.to_base(value, "%w/v" if low.replace(" ", "") == "%w/v" else u)
    except units.UnitError:
        return low, value


def extract_numbers(text: str) -> list[Number]:
    """All quantities in ``text`` with normalised units. Codes like E-104, T75 or HEK293 are skipped."""
    text = (text or "").replace(" ", " ")
    found: list[Number] = []
    covered: list[tuple[int, int]] = []
    for m in _RANGE.finditer(text):
        for raw in (m.group(1), m.group(2)):
            value = _parse_value(raw)
            if value is not None:
                kind, base = _canonical(value, m.group(3))
                found.append(Number(raw, value, kind, base))
        covered.append(m.span())
    for m in _SINGLE.finditer(text):
        if any(a <= m.start() < b for a, b in covered):
            continue
        value = _parse_value(m.group(2))
        if value is None:
            continue
        kind, base = _canonical(value, m.group(3), bool(m.group(1)))
        found.append(Number(m.group(2), value, kind, base))
    return found


def _round_sig(x: float, sig: int) -> float:
    if x == 0:
        return 0.0
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)


def _same(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def number_supported(n: Number, evidence: list[Number]) -> bool:
    """A step number is supported if the evidence holds the same quantity.

    Units must agree after conversion (100 mL == 0.1 L, but 1 M != 1 mM). A unitless step number
    matches any evidence number with the same value. A step value that is the evidence value rounded
    to at least 3 significant figures (6.06 g for 6.057 g) also counts.
    """
    for e in evidence:
        if n.kind is not None and e.kind != n.kind:
            continue
        a, b = (n.base, e.base) if n.kind is not None else (n.value, e.value)
        if _same(a, b):
            return True
        if n.sig_figs >= 3 and _same(_round_sig(b, n.sig_figs), a):
            return True
    return False


# ---------------------------------------------------------------- checklist verification
def verify_step(step: dict, chunk_texts: dict[str, str], calculator_numbers: list[str]) -> list[str]:
    """Reasons a checklist step is unsupported (empty when it is grounded)."""
    reasons: list[str] = []
    cited = [c for c in step.get("chunk_ids") or [] if isinstance(c, str)]
    if not cited:
        reasons.append("Step cites no SOP passage.")
    unknown = [c for c in cited if c not in chunk_texts]
    if unknown:
        reasons.append(f"Cites passage(s) not retrieved in this request: {', '.join(unknown[:3])}.")
    evidence: list[Number] = []
    for c in cited:
        evidence += extract_numbers(chunk_texts.get(c, ""))
    for text in calculator_numbers:
        evidence += extract_numbers(text)
    for field_name in ("action", "safety_note"):
        for n in extract_numbers(step.get(field_name) or ""):
            if not number_supported(n, evidence):
                reasons.append(f"The value {n.raw} in the {field_name.replace('_', ' ')} is not in the cited "
                               "passage or the calculation.")
    return reasons


def verify_checklist(steps: list[dict], chunk_texts: dict[str, str], calculator_numbers: list[str]) -> list[dict]:
    """Return the steps renumbered, each with ``unsupported`` and ``unsupported_reasons`` set."""
    out = []
    for i, step in enumerate(steps, start=1):
        reasons = verify_step(step, chunk_texts, calculator_numbers)
        out.append({
            "step": i,
            "action": str(step.get("action") or "").strip(),
            "safety_note": str(step.get("safety_note") or "").strip() or DEFAULT_SAFETY_NOTE,
            "chunk_ids": [c for c in step.get("chunk_ids") or [] if isinstance(c, str)],
            "required": bool(step.get("required", True)),
            "unsupported": bool(reasons),
            "unsupported_reasons": reasons,
        })
    return out


# ---------------------------------------------------------------- confidence and status
def retrieval_strength(top_score: float, min_score: float) -> float:
    """0 at the evidence threshold, 1 at 2.3x the threshold (the RAG engine's 'high' level)."""
    if min_score <= 0:
        return 1.0 if top_score > 0 else 0.0
    return max(0.0, min(1.0, (top_score - min_score) / (min_score * 1.3)))


def compute_confidence(*, retrieval: float | None, steps: list[dict] | None, tools_ok: float | None) -> float:
    """Weighted mean of the components that apply (retrieval 0.4, supported steps 0.4, tool outcomes 0.2).

    Never uses a model's self-rating.
    """
    parts: list[tuple[float, float]] = []
    if retrieval is not None:
        parts.append((0.4, retrieval))
    if steps is not None:
        parts.append((0.4, (sum(1 for s in steps if not s["unsupported"]) / len(steps)) if steps else 0.0))
    if tools_ok is not None:
        parts.append((0.2, tools_ok))
    if not parts:
        return 0.0
    return round(sum(w * v for w, v in parts) / sum(w for w, _ in parts), 2)


@dataclass
class Assessment:
    status: str
    confidence: float
    uncertainty_flag: bool
    uncertainty_message: str
    blockers: list[str]
    cautions: list[str]
    checklist_label: str


def assess(*, blockers: list[str], cautions: list[str], steps: list[dict], confidence: float,
           required_tool_failed: bool, procedure: bool) -> Assessment:
    """Final, deterministic status for an agent run.

    refused: any blocker (missing/expired reagent, insufficient stock, incompatible pair, failed
    required tool, unsupported required step, confidence below the threshold for a procedure).
    caution: non-blocking issues only (expiring reagent, unknown pair, low stock, unapproved source...).
    supported: everything grounded and checked.
    """
    blockers = list(dict.fromkeys(blockers))
    cautions = list(dict.fromkeys(cautions))
    required_unsupported = [s["step"] for s in steps if s["unsupported"] and s.get("required", True)]
    optional_unsupported = [s["step"] for s in steps if s["unsupported"] and not s.get("required", True)]
    if required_unsupported:
        blockers.append(f"Required step(s) {', '.join(map(str, required_unsupported))} are not supported by the "
                        "retrieved SOP passages or the calculation.")
    if optional_unsupported:
        cautions.append(f"Optional step(s) {', '.join(map(str, optional_unsupported))} are not supported by the "
                        "retrieved SOP passages.")
    low = procedure and confidence < CONFIDENCE_THRESHOLD
    if low:
        blockers.append(f"Confidence {confidence:.2f} is below {CONFIDENCE_THRESHOLD:.2f}.")
    uncertain = low or bool(required_unsupported) or required_tool_failed
    status = "refused" if blockers else "caution" if cautions else "supported"
    return Assessment(
        status=status,
        confidence=confidence,
        uncertainty_flag=uncertain,
        uncertainty_message=UNCERTAINTY_MESSAGE if uncertain else "",
        blockers=blockers,
        cautions=cautions,
        checklist_label=DO_NOT_FOLLOW_LABEL if status == "refused" and steps else "",
    )
