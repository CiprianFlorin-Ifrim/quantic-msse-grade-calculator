# grade.py
#
# Quantic MSSE final grade calculator.
#
#   Exams                     60%   every concentration exam plus the best specialization exams
#   SMARTCASEs                10%   first attempt only, core courses plus every specialization started
#   Projects & Presentations  30%   pass/fail: a passing rubric score counts as 100, a fail as 0
#
# The program rules live in curriculum.json and your scores in grades.json, so the script can tell a
# grade you have not entered from one the program does not ask for. Any missing core grade stops the
# run. Specializations are the exception: only the required number must be complete. One without an exam
# score is in progress, so it has no exam to count, but every SMARTCASE already taken in it still counts.
#
# Electives do not count. SMARTCASEs completed before the program start may be Foundations items, which
# do not count either; exclude_smartcases_before_start in grades.json decides how they are treated.
#
# Usage: python3 grade.py [grades.json] [--curriculum curriculum.json]

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRADUATION_MINIMUM = 80.0


class GradeError(Exception):
    """The grades file cannot produce a final score, with every reason listed."""


def mean(values):
    return sum(values) / len(values)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        hint = "\nCopy grades.example.json to grades.json and fill in your scores." if path.name == "grades.json" else ""
        raise GradeError(f"File not found: {path}{hint}")
    except json.JSONDecodeError as e:
        raise GradeError(f"{path.name} is not valid JSON: line {e.lineno}, column {e.colno}: {e.msg}")


def smartcase(entry) -> tuple[float | None, date | None]:
    """A SMARTCASE is either a bare score or {"score": ..., "completed": "YYYY-MM-DD"}."""
    if isinstance(entry, dict):
        completed = entry.get("completed")
        return entry.get("score"), date.fromisoformat(completed) if completed else None
    return entry, None


def check_range(value, top: float, label: str, problems: list[str]) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= top:
        problems.append(f"{label}: {value!r} is not a number between 0 and {top:g}")


# -- validation --------------------------------------------------------------


def validate(curriculum: dict, grades: dict) -> list[str]:
    """Return the completed specializations, or raise listing everything that is missing or wrong."""
    missing: dict[str, list[str]] = {}     # course -> what is absent, kept in curriculum order
    problems: list[str] = []               # values present but unusable, and names the curriculum lacks

    core = grades.get("core_courses") or {}
    for course, rules in curriculum["core_courses"].items():
        entered = core.get(course)
        if entered is None:
            missing[course] = ["every grade"]
            continue
        gaps = missing.setdefault(course, [])
        if entered.get("exam") is None:
            gaps.append("exam")
        else:
            check_range(entered["exam"], 100, f"{course} exam", problems)
        if "project" in rules:
            if entered.get("project") is None:
                gaps.append("project")
            else:
                check_range(entered["project"], 5, f"{course} project", problems)
        cases = entered.get("smartcases") or {}
        for title in rules["smartcases"]:
            score, _ = smartcase(cases.get(title))
            if score is None:
                gaps.append(f"SMARTCASE '{title}'")
            else:
                check_range(score, 100, f"{course} SMARTCASE '{title}'", problems)
        for title in cases:
            if title not in rules["smartcases"]:
                problems.append(f"{course}: SMARTCASE '{title}' is not in the curriculum")
    for course in core:
        if course not in curriculum["core_courses"]:
            problems.append(f"Core course '{course}' is not in the curriculum")

    capstone = grades.get("capstone") or {}
    for item in curriculum["capstone"]:
        if capstone.get(item) is None:
            missing.setdefault("Capstone", []).append(item)
        else:
            check_range(capstone[item], 5, f"Capstone {item}", problems)

    completed = []
    for name, spec in (grades.get("specializations") or {}).items():
        done = spec.get("exam") is not None     # without an exam it is in progress, which is allowed
        if done:
            check_range(spec["exam"], 100, f"{name} exam", problems)
            completed.append(name)
        cases = spec.get("smartcases") or {}
        if done and not cases:
            missing.setdefault(name, []).append("its SMARTCASEs")
        for title, entry in cases.items():
            score, _ = smartcase(entry)
            if score is not None:
                check_range(score, 100, f"{name} SMARTCASE '{title}'", problems)
            elif done:
                missing.setdefault(name, []).append(f"SMARTCASE '{title}'")   # a finished one has them all

    required = curriculum["specializations_required"]
    if len(completed) < required:
        missing.setdefault("Specializations", []).append(
            f"{required} must be complete with an exam score, found {len(completed)}"
        )

    if grades.get("exclude_smartcases_before_start") and not grades.get("start_date"):
        problems.append("exclude_smartcases_before_start is set but start_date is missing")

    missing = {course: gaps for course, gaps in missing.items() if gaps}
    if missing or problems:
        lines = []
        if missing:
            lines.append(f"Grades missing for: {', '.join(missing)}")
            for course, gaps in missing.items():
                lines += ["", f"  {course}"] + [f"    - {gap}" for gap in gaps]    # one gap per line, grouped by course
        if problems:
            lines += [""] if lines else []
            lines.append("Grades that cannot be used:")
            lines += [""] + [f"  - {p}" for p in problems]
        raise GradeError("\n".join(lines))
    return completed


# -- scoring -----------------------------------------------------------------


def exams_score(curriculum, grades, completed):
    core = [grades["core_courses"][c]["exam"] for c in curriculum["core_courses"]]
    ranked = sorted(completed, key=lambda s: grades["specializations"][s]["exam"], reverse=True)
    counted = ranked[: curriculum["specializations_required"]]   # only the best ones count
    return mean(core + [grades["specializations"][s]["exam"] for s in counted]), counted


def smartcase_score(curriculum, grades):
    start = grades.get("start_date")
    cutoff = date.fromisoformat(start) if start and grades.get("exclude_smartcases_before_start") else None
    entries = [grades["core_courses"][c]["smartcases"][t] for c, r in curriculum["core_courses"].items() for t in r["smartcases"]]
    for spec in (grades.get("specializations") or {}).values():
        entries += (spec.get("smartcases") or {}).values()    # finished or not, every SMARTCASE taken counts

    counted, excluded = [], 0
    for entry in entries:
        score, when = smartcase(entry)
        if score is None:
            continue    # not yet taken, in a specialization still in progress
        if cutoff and when and when < cutoff:
            excluded += 1
            continue
        counted.append(score)
    return mean(counted), len(counted), excluded


def projects_score(curriculum, grades):
    items = [(f"{c} project", grades["core_courses"][c]["project"], r["project"]["pass_mark"])
             for c, r in curriculum["core_courses"].items() if "project" in r]
    items += [(f"Capstone {i}", grades["capstone"][i], r["pass_mark"]) for i, r in curriculum["capstone"].items()]
    failed = [name for name, score, pass_mark in items if score < pass_mark]
    return mean([0.0 if name in failed else 100.0 for name, _, _ in items]), len(items), failed


# -- report ------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Quantic MSSE final grade calculator.")
    parser.add_argument("grades", nargs="?", type=Path, default=HERE / "grades.json")
    parser.add_argument("--curriculum", type=Path, default=HERE / "curriculum.json")
    args = parser.parse_args(argv)

    try:
        curriculum, grades = load(args.curriculum), load(args.grades)
        completed = validate(curriculum, grades)
    except GradeError as e:
        print(e, file=sys.stderr)
        return 1

    w = curriculum["weights"]
    exams, best = exams_score(curriculum, grades, completed)
    smartcases, counted, excluded = smartcase_score(curriculum, grades)
    projects, items, failed = projects_score(curriculum, grades)
    final = w["exams"] * exams + w["smartcases"] * smartcases + w["projects"] * projects

    print(f"Exams              {exams:6.2f}%  x {w['exams']} = {w['exams'] * exams:5.2f}")
    print(f"SMARTCASEs         {smartcases:6.2f}%  x {w['smartcases']} = {w['smartcases'] * smartcases:5.2f}")
    print(f"Projects           {projects:6.2f}%  x {w['projects']} = {w['projects'] * projects:5.2f}")
    print(f"Final              {final:6.2f}%")

    exam_of = {s: grades["specializations"][s]["exam"] for s in best}
    print("\nSpecialization exams counted: " + ", ".join(f"{s} ({score:.2f})" for s, score in exam_of.items()))
    note = f", {excluded} completed before the start date left out" if excluded else ""
    print(f"SMARTCASEs counted: {counted}{note}")
    print(f"Projects and presentations: {items}")

    if failed:
        print(f"\nBelow the pass mark, so counted as 0 and blocking graduation: {', '.join(failed)}")
    if final < GRADUATION_MINIMUM:
        print(f"\nBelow the {GRADUATION_MINIMUM:g}% minimum needed to graduate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
