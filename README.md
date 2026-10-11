# Quantic MSSE Grade Calculator

This script calculates the final grade of the Quantic Master of Science in Software Engineering (MSSE), reading the exam, SMARTCASE and project scores from a JSON file and applying the weights published by Quantic.

The final grade is not just a simple average of all the grades due to Quantic's rules, specifically that a project or presentation that passes counts as 100 whatever its rubric score, so a 3 and a 5 are the same. Separately, only the best two specialization exams count, whereas every SMARTCASE taken in a specialization counts, even if the full specialization is not finished.

When a grade is missing, the script stops and provides info to the user, so the average always covers every course.

| Part of the grade | Weight | What counts |
|---|---|---|
| Exams | 60% | Each concentration exam, plus the best two specialization exams |
| SMARTCASEs | 10% | The first attempt at each SMARTCASE in the core courses and in every started specialization |
| Projects and presentations | 30% | A score at or above the pass mark counts as 100, and a score below it counts as 0 |

## 1. Build and Run

    cp grades.example.json grades.json      # then enter the scores
    python3 grade.py
    python3 grade.py other.json             # a different grades file

The script needs Python 3.11 or later and only the standard library, and it has been tested on every version from 3.11 to 3.14.

## 2. Directory Tree

    grade.py                 the calculator
    curriculum.json          the program rules: weights, courses, SMARTCASE titles and pass marks
    grades.example.json      example of the JSON that needs to be completed with all grades
    grades.json              the student's scores, excluded by .gitignore once .example is edited

## 3. Concepts

### 3.1 Specializations

The program requires two specializations and allows more. A specialization counts as complete once it has an exam score and as in progress otherwise, and that state decides what a SMARTCASE scored `null` means. In a specialization still in progress, the script leaves it out of the average. In a complete one, where every SMARTCASE should already have a score, it stops and informs the users about the missing grade/s.

### 3.2 SMARTCASEs Before the Start Date

SMARTCASEs in the Foundations playlist open before the program starts and do not count, so with `exclude_smartcases_before_start` set to true the script drops each one completed before `start_date`. A SMARTCASE without a `completed` date always counts.

## 4. Rules

Each rule below comes from Quantic's website, from the artificial intelligence (AI) advisor on the platform or from Quantic support, and the website rules are set out on two support pages: [How are MSSE grades calculated?](https://support.quantic.edu/article/1541-how-are-msse-grades-calculated) and [How are project scores calculated?](https://support.quantic.edu/article/475-how-are-mba-project-scores-calculated-july-2019-and-later).

| Rule | Confirmed by |
|---|---|
| Exams weigh 60%, SMARTCASEs 10%, and projects and presentations 30% | Website |
| Final grade of 80% or more to graduate | Website |
| All eight concentration exams count | Website |
| Two specializations required, and more can be taken | Website |
| With more than two specializations complete, only the best two exams count, while the SMARTCASEs of every one count | Support |
| SMARTCASEs taken in an extra specialization count even before its exam is taken | AI advisor |
| Only the first attempt at each SMARTCASE counts | Website |
| SMARTCASEs in the Foundations playlist before the start date do not count | Website |
| Projects and presentations that pass count as 100, and those that fail count as 0, so a 3 and a 5 count the same | Website, AI advisor |
| Course projects and presentations pass at 2 out of 5 | Website |
| Written capstone project passes at 3 out of 5 | Website, Support |
| Capstone presentation passes at 2 out of 5 | Support, AI advisor |

## 5. Usage Notes

**Check `curriculum.json` against the Quantic dashboard.** It describes the Class of October 2026, and another cohort may have different courses or SMARTCASE titles, which the script will report as errors.

**Enter `null` for a grade that is still to come.** The script then names it as missing, whereas a 0 counts as a real score and lowers the grade without a warning.

## 6. Outputs

For a complete JSON that holds all grades, the script prints the weighted components, the final grade and the items it counted. The run below used invented scores of 90 for each exam and SMARTCASE, and 4 for each project:

    Exams               90.00%  x 0.6 = 54.00
    SMARTCASEs          90.00%  x 0.1 =  9.00
    Projects           100.00%  x 0.3 = 30.00
    Final               93.00%

    Specialization exams counted: Specialization 1 (90.00), Specialization 2 (90.00)
    SMARTCASEs counted: 38
    Projects and presentations: 7

When a grade is missing, the script lists each one by course and exits with status 1:

    Grades missing for: Microservices Architectures, Capstone

      Microservices Architectures
        - exam

      Capstone
        - presentation

A project below its pass mark counts as 0 and is named as a block on graduation, and a final grade under the 80% needed to graduate also shows a warning.