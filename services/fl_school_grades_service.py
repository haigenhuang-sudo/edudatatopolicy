import pandas as pd
import os
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.getenv(
    "FL_SCHOOL_GRADES_PATH",
    os.path.join(BASE_DIR, "data", "fldoe_school_grades.csv")
)

DETAIL_COLS = [
    "SchoolYear", "districtNumber", "districtName",
    "schoolNumber", "schoolName", "schoolgrade",
    "totalPoints", "totalComponents", "totalPercentage",
    "elaGrade03Achievement",
    "elaAchievement", "elaGains", "elaGainsLowest25",
    "mathAchievement", "mathGains", "mathGainsLowest25",
    "scienceAchievement", "socialStudiesAchievement",
    "middleSchoolAcceleration",
    "graduationRate", "highSchoolAcceleration",
]


def get_school_grades_data() -> dict[str, Any]:
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    if "schoolgrade" in df.columns:
        df = df[df["schoolgrade"] != "I"]
    detail_cols = [c for c in DETAIL_COLS if c in df.columns]

    # 1. Distinct years (most-recent first)
    years = sorted(df["SchoolYear"].dropna().unique().tolist(), reverse=True)

    # 2. Distinct districts list (all Florida districts)
    districts_df = (
        df[df["schoolNumber"] == 0][["districtNumber", "districtName"]]
        .drop_duplicates()
        .sort_values("districtName")
    )
    districts = districts_df.where(pd.notnull(districts_df), None).to_dict(orient="records")

    # 3. All schools — all districts, include districtNumber for frontend filtering
    # 3. All schools — exclude district 0
    schools_df = (
        df[(df["schoolNumber"] != 0) & (~df["districtNumber"].astype(str).str.strip().isin(["00", "0", "0.0"]))][
            ["districtNumber", "districtName", "schoolNumber", "schoolName", "schoolType"]]
        .drop_duplicates(subset=["districtNumber", "schoolNumber"])
        .sort_values(["districtName", "schoolName"])
    )
    schools = schools_df.where(pd.notnull(schools_df), None).to_dict(orient="records")

    # 4. Per-school detail rows — all districts
    school_data_df = (
        df[df["schoolNumber"] != 0][detail_cols]
        .sort_values(["SchoolYear", "districtNumber", "schoolName"], ascending=[False, True, True])
    )
    school_data = school_data_df.where(pd.notnull(school_data_df), None).to_dict(orient="records")

    # 5. District-level rows — all districts (schoolNumber = 0)
    dist_detail_cols = [c for c in detail_cols if c != "schoolName"]
    district_data_df = (
        df[df["schoolNumber"] == 0][dist_detail_cols]
        .sort_values(["SchoolYear", "districtNumber"], ascending=[False, True])
    )
    district_data = district_data_df.where(pd.notnull(district_data_df), None).to_dict(orient="records")

    # 6. District ranking — all Florida districts, totalPoints, since 2019
    rank_cols = [c for c in ["SchoolYear", "districtNumber", "districtName", "schoolNumber", "totalPoints"] if c in df.columns]
    district_ranking_df = (
        df[(df["schoolNumber"] == 0) & (df["SchoolYear"] >= 2019)][rank_cols]
        .sort_values(["SchoolYear", "districtNumber"], ascending=[False, True])
    )
    district_ranking = district_ranking_df.where(pd.notnull(district_ranking_df), None).to_dict(orient="records")

    # 7. Grade history — all schools all districts, last 6 years
    top6_years = sorted(df[df["schoolNumber"] != 0]["SchoolYear"].dropna().unique(), reverse=True)[:6]
    hist_cols = [c for c in ["districtNumber", "schoolNumber", "schoolName", "schoolType", "SchoolYear", "schoolgrade"] if c in df.columns]
    all_grades_df = (
        df[(df["schoolNumber"] != 0) & (df["SchoolYear"].isin(top6_years))][hist_cols]
        .sort_values(["districtNumber", "schoolName", "SchoolYear"], ascending=[True, True, False])
    )
    all_schools_grades = all_grades_df.where(pd.notnull(all_grades_df), None).to_dict(orient="records")

    return {
        "years":              years,
        "districts":          districts,
        "schools":            schools,
        "school_data":        school_data,
        "district_data":      district_data,
        "district_ranking":   district_ranking,
        "all_schools_grades": all_schools_grades,
    }