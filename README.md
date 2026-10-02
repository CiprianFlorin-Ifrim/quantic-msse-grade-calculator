# Quantic MSSE Grade Calculator

This script calculates the final grade of the Quantic Master of Science in Software Engineering (MSSE). It reads the exam, SMARTCASE and project scores from one JavaScript Object Notation (JSON) file, and it applies the weights that Quantic publishes.

A plain average of the scores on the dashboard gives the wrong figure, because the final grade follows two rules from Quantic's support pages. A project or presentation that passes counts as 100 whatever its rubric score, so a 3 and a 5 carry the same weight. Only the best two specialization exams count, while every SMARTCASE taken in a specialization counts, finished or not.

The script stops and names each absent grade, so the average always includes every course.

| Part of the grade | Weight | What counts |
|---|---|---|
| Exams | 60% | Each concentration exam, plus the best two specialization exams |
| SMARTCASEs | 10% | The first attempt at each SMARTCASE in the core courses and in every specialization started |
| Projects and presentations | 30% | Pass or fail: a score at or above the pass mark counts as 100, and a score below it counts as 0 |

## 1. Build and Run

    cp grades.example.json grades.json      # then enter the scores
    python3 grade.py
    python3 grade.py other.json             # a different grades file

The script needs Python 3.11 or later, and it was run on 3.11, 3.12, 3.13 and 3.14. Every dependency is in the standard library.

## 2. Directory Tree

    grade.py                 the calculator
    curriculum.json          the program rules: weights, courses, SMARTCASE titles and pass marks
    grades.example.json      each grade that the program requires, set to null
    grades.json              the student's scores, excluded by .gitignore

## 3. Concepts

### 3.1 Curriculum and Grades

`curriculum.json` lists each grade that the program requires. `grades.json` holds the student's scores. The script compares the two files, so it can tell an absent grade from a grade that the program does not require.

### 3.2 Specializations

The program requires two specializations, and a student can take more. A specialization with an exam score is complete, and one without an exam score is in progress.

Only the best two exams from the complete specializations count. Every SMARTCASE taken in a specialization counts, complete or in progress.

A SMARTCASE that is not taken yet has the score `null` in `grades.json`. The effect of `null` depends on the specialization:

- **In progress:** the script excludes that SMARTCASE from the average, and the SMARTCASEs with a score still count.
- **Complete:** the script stops and names that SMARTCASE, because a complete specialization has a score for each of its SMARTCASEs.

### 3.3 Pass Marks

Each project and presentation passes at 2 out of 5, except the written capstone project, which passes at 3.

### 3.4 SMARTCASEs Before the Start Date

SMARTCASEs in the Foundations playlist open before the program starts, and they do not count. When `exclude_smartcases_before_start` is true, the script excludes each SMARTCASE completed before `start_date`. The `completed` date is optional, and a SMARTCASE without one always counts.

## 4. Rules

Each rule below comes from Quantic's website, from the AI advisor on the Quantic platform, or from Quantic support. The website rules are on two support pages: [How are MSSE grades calculated?](https://support.quantic.edu/article/1541-how-are-msse-grades-calculated) and [How are project scores calculated?](https://support.quantic.edu/article/475-how-are-mba-project-scores-calculated-july-2019-and-later).

| Rule | Confirmed by |
|---|---|
| Exams weigh 60%, SMARTCASEs 10%, and projects and presentations 30% | Website |
| Final grade of 80% or more to graduate | Website |
| All eight concentration exams count | Website |
| Two specializations required, and more can be taken | Website |
| With more than two specializations complete, only the best two exams count, while the SMARTCASEs of every one count | Support |
| SMARTCASEs taken in an extra specialization count even without the exam completion | AI advisor |
| Only the first attempt at each SMARTCASE counts | Website |
| SMARTCASEs in the Foundations playlist before the start date do not count | Website |
| Projects and presentations that pass count as 100, and fails count as 0, so a 3 and a 5 count the same | Website, AI advisor |
| Course projects and presentations pass at 2 out of 5 | Website |
| Written capstone project passes at 3 out of 5 | Website, support |
| Capstone presentation passes at 2 out of 5 | Support, AI advisor |

## 5. Usage Notes

**Check `curriculum.json` against the Quantic dashboard.** It describes the Class of October 2026, and another cohort can have different courses or SMARTCASE titles. The script reports a title that does not match as an error.

**Enter `null` for a grade that is still to come.** The script then names it as absent. A score of 0 counts as a real score, and it lowers the grade without a warning.

## 6. Outputs

For a complete file, the script prints the weighted parts, the final grade and the items that it counted. This run used made-up scores of 90 for each exam and SMARTCASE, and 4 for each project:

    Exams               90.00%  x 0.6 = 54.00
    SMARTCASEs          90.00%  x 0.1 =  9.00
    Projects           100.00%  x 0.3 = 30.00
    Final               93.00%

    Specialization exams counted: Specialization 1 (90.00), Specialization 2 (90.00)
    SMARTCASEs counted: 38
    Projects and presentations: 7

When a grade is absent, the script lists each absent grade by course and exits with status 1:

    Grades missing for: Microservices Architectures, Capstone

      Microservices Architectures
        - exam

      Capstone
        - presentation

A project below its pass mark counts as 0, and the script names it as a block on graduation. The script also warns about a final grade below 80%, which is the minimum to graduate.
