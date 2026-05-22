import urllib.parse
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Any
import os

db_user     = os.getenv("DB_USER",     "svc-dwftp")
db_password = os.getenv("DB_PASSWORD", "13wwu1rM")


def get_engine():
    conn_str = (
        "Driver={SQL Server};"
        f"Server=ag-darts\\darts;"
        "Database=Imports;"
        f"UID={db_user};"
        f"PWD={db_password};"
        "Trusted_Connection=yes;"
    )
    params = urllib.parse.quote_plus(conn_str)
    return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


def get_school_grades_data() -> dict[str, Any]:
    engine = get_engine()

    with engine.connect() as conn:

        # 1. Distinct years (most-recent first)
        years_df = pd.read_sql(text("""
            SELECT DISTINCT SchoolYear
            FROM   [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
            ORDER  BY SchoolYear DESC
        """), conn)
        years = years_df["SchoolYear"].tolist()

        # 2. Schools list: Collier County (dist 11), exclude district aggregate
        schools_df = pd.read_sql(text("""
            SELECT DISTINCT schoolNumber, schoolName, schoolType
            FROM   [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
            WHERE  districtNumber = 11
              AND  schoolNumber  <> 0
            ORDER  BY schoolName
        """), conn)
        schools = schools_df.to_dict(orient="records")

        # 3. Per-school detail rows (Collier, non-aggregate)
        school_data_df = pd.read_sql(text("""
            SELECT
                SchoolYear,
                districtNumber, districtName,
                schoolNumber,   schoolName,
                schoolgrade,
                totalPoints,        totalComponents,    totalPercentage,
                elaGrade03Achievement,
                elaAchievement,     elaGains,           elaGainsLowest25,
                mathAchievement,    mathGains,          mathGainsLowest25,
                scienceAchievement, socialStudiesAchievement,
                middleSchoolAcceleration,
                graduationRate,     highSchoolAcceleration
            FROM [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
            WHERE districtNumber = 11
              AND schoolNumber  <> 0
            ORDER BY SchoolYear DESC, schoolName
        """), conn)
        school_data = school_data_df.where(pd.notnull(school_data_df), None).to_dict(orient="records")

        # 4. District-level detail rows for Collier (schoolNumber = 0) — full columns
        collier_district_df = pd.read_sql(text("""
            SELECT
                SchoolYear,
                districtNumber, districtName,
                schoolNumber,
                schoolgrade,
                totalPoints,        totalComponents,    totalPercentage,
                elaGrade03Achievement,
                elaAchievement,     elaGains,           elaGainsLowest25,
                mathAchievement,    mathGains,          mathGainsLowest25,
                scienceAchievement, socialStudiesAchievement,
                middleSchoolAcceleration,
                graduationRate,     highSchoolAcceleration
            FROM [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
            WHERE districtNumber = 11
              AND schoolNumber = 0
            ORDER BY SchoolYear DESC
        """), conn)
        collier_district_data = collier_district_df.where(pd.notnull(collier_district_df), None).to_dict(orient="records")

        # 5. District-level rows for comparison chart (all comparison districts, totalPoints only)
        district_df = pd.read_sql(text("""
            SELECT
                SchoolYear,
                districtNumber, districtName,
                schoolNumber,
                totalPoints
            FROM [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
            WHERE districtNumber IN (10,11,17,35,41,42,46,55,56,58,64)
              AND schoolNumber = 0
            ORDER BY SchoolYear DESC, districtNumber
        """), conn)
        district_comparison = district_df.where(pd.notnull(district_df), None).to_dict(orient="records")

        # 6. Grade history table: all Collier schools, last 6 years — include schoolType
        all_grades_df = pd.read_sql(text("""
            SELECT schoolNumber, schoolName, schoolType, SchoolYear, schoolgrade
            FROM   [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
            WHERE  districtNumber = 11
              AND  schoolNumber  <> 0
              AND  SchoolYear IN (
                    SELECT TOP 6 SchoolYear
                    FROM   [Imports].[dbo].[FLDOE_SchoolAccountability_SchoolGrades_RAW]
                    WHERE  districtNumber = 11
                      AND  schoolNumber  <> 0
                    GROUP  BY SchoolYear
                    ORDER  BY SchoolYear DESC
              )
            ORDER  BY schoolName, SchoolYear DESC
        """), conn)
        all_schools_grades = all_grades_df.where(pd.notnull(all_grades_df), None).to_dict(orient="records")

    return {
        "years":                 years,
        "schools":               schools,
        "school_data":           school_data,
        "collier_district_data": collier_district_data,
        "district_comparison":   district_comparison,
        "all_schools_grades":    all_schools_grades,
    }