import pandas as pd
import os
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.getenv(
    "EWI_STUDENTS_PATH",
    os.path.join(BASE_DIR, "data", "ewi_students.csv")
)

# ── Risk functions ────────────────────────────────────────────────────────
def att_risk(v):
    return "high" if v < 85 else "mod" if v < 90 else "low"

def beh_risk(r, s):
    return "high" if (r >= 3 or s >= 1) else "mod" if r == 2 else "low"

def crs_risk(g, f):
    return "high" if (g < 2.0 or f >= 2) else "mod" if (g < 2.5 or f >= 1) else "low"

def ach_risk(ela, math, sci, wri, et, mt):
    flags = []
    if ela:
        flags.append("high" if ela < 285 else "mod" if ela < 297 else "low")
    if math:
        flags.append("high" if math < 285 else "mod" if math < 297 else "low")
    if sci and sci != "":
        try:
            s = float(sci)
            flags.append("high" if s < 130 else "mod" if s < 150 else "low")
        except: pass
    if wri and wri != "":
        try:
            w = float(wri)
            flags.append("high" if w < 2.0 else "mod" if w < 3.0 else "low")
        except: pass
    if et is not None:
        flags.append("high" if et <= -10 else "mod" if et <= -5 else "low")
    if mt is not None:
        flags.append("high" if mt <= -10 else "mod" if mt <= -5 else "low")
    return "high" if "high" in flags else "mod" if "mod" in flags else "low"

def domain_score(r):
    return 20 if r == "high" else 55 if r == "mod" else 90

def overall_risk(ar, br, cr, acr):
    risks = [ar, br, cr, acr]
    high_n = risks.count("high")
    mod_n  = risks.count("mod")
    return "high" if (high_n >= 1 or mod_n >= 2) else "mod" if mod_n >= 1 else "low"

def composite_score(ar, br, cr, acr):
    return round(0.30 * domain_score(ar) + 0.20 * domain_score(br) +
                 0.25 * domain_score(cr) + 0.25 * domain_score(acr))


def _safe_float(v, default=None):
    try: return float(v) if v != "" else default
    except: return default

def _safe_int(v, default=None):
    try: return int(v) if v != "" else default
    except: return default


def get_ewi_data() -> dict[str, Any]:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df = df.where(pd.notnull(df), None)

    students = []
    summary = {"high": 0, "mod": 0, "low": 0}

    for _, row in df.iterrows():
        att   = _safe_float(row.get("attendance_pct"), 90)
        refs  = _safe_int(row.get("referrals"), 0)
        sus   = _safe_int(row.get("suspensions"), 0)
        gpa   = _safe_float(row.get("gpa"), 2.5)
        fails = _safe_int(row.get("failing_subjects"), 0)
        ela   = _safe_int(row.get("ela_score"))
        ela_p = _safe_int(row.get("ela_prior"))
        math  = _safe_int(row.get("math_score"))
        math_p= _safe_int(row.get("math_prior"))
        sci   = _safe_float(row.get("sci_score"))
        wri   = _safe_float(row.get("writing_score"))

        et = (ela - ela_p) if ela and ela_p else None
        mt = (math - math_p) if math and math_p else None

        ar  = att_risk(att)
        br  = beh_risk(refs, sus)
        cr  = crs_risk(gpa, fails)
        acr = ach_risk(ela, math, sci, wri, et, mt)
        ov  = overall_risk(ar, br, cr, acr)
        cs  = composite_score(ar, br, cr, acr)

        summary[ov] += 1

        hist_labels = str(row.get("hist_labels") or "").split("|") if row.get("hist_labels") else []
        hist_ela    = [_safe_int(x) for x in str(row.get("hist_ela") or "").split("|")] if row.get("hist_ela") else []
        hist_math   = [_safe_int(x) for x in str(row.get("hist_math") or "").split("|")] if row.get("hist_math") else []

        students.append({
            "student_id":   int(row.get("student_id", 0)),
            "name":         str(row.get("name", "")),
            "grade":        _safe_int(row.get("grade")),
            "school":       str(row.get("school", "")),
            "school_level": str(row.get("school_level", "")),
            "school_year":  str(row.get("school_year", "")),
            "counselor":    str(row.get("counselor", "")),
            "overall":      ov,
            "score":        cs,
            "ewi": {
                "attendance_pct":   att,
                "referrals":        refs,
                "suspensions":      sus,
                "gpa":              gpa,
                "failing_subjects": fails,
                "test_scores": {
                    "ela":     {"score": ela,  "prior_year": ela_p},
                    "math":    {"score": math, "prior_year": math_p},
                    "science": {"score": sci},
                    "writing": {"score": wri},
                },
                "score_history": {
                    "labels": hist_labels,
                    "ela":    hist_ela,
                    "math":   hist_math,
                },
            },
            "risks": {"att": ar, "beh": br, "crs": cr, "ach": acr},
        })

    # Sort: high first, then mod, then low, then by score asc within group
    order = {"high": 0, "mod": 1, "low": 2}
    students.sort(key=lambda s: (order[s["overall"]], s["score"]))

    return {"students": students, "summary": summary}


def get_student_by_id(student_id: int) -> dict | None:
    data = get_ewi_data()
    return next((s for s in data["students"] if s["student_id"] == student_id), None)
