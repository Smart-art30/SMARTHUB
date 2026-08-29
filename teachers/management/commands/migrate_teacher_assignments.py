import sqlite3

from django.core.management.base import BaseCommand
from django.db import transaction

from teachers.models import Teacher, TeacherSubjectAssignment
from schools.models import SchoolClass
from academics.models import Subject


class Command(BaseCommand):
    help = "Migrate teacher class/subject assignments from SQLite to Neon"

    def handle(self, *args, **options):

        print("=" * 70)
        print("SMARTHUB: SQLite → Neon Teacher Assignment Migration")
        print("=" * 70)

        # ---------------------------------------------------------
        # Connect directly to the old SQLite database
        # ---------------------------------------------------------
        db = sqlite3.connect("db.sqlite3")
        cursor = db.cursor()

        cursor.execute("""
            SELECT
                id,
                school_class_id,
                subject_id,
                teacher_id
            FROM teachers_teachersubjectassignment
            ORDER BY id
        """)

        rows = cursor.fetchall()

        print(f"SQLite teacher assignments found: {len(rows)}")
        print(
            "Teacher assignments already in Neon:",
            TeacherSubjectAssignment.objects.count()
        )

        if not rows:
            print("No teacher assignments found in SQLite.")
            db.close()
            return

        # ---------------------------------------------------------
        # Build mappings
        #
        # SQLite teacher IDs are linked to Teacher records.
        # Teacher.user_id points to the actual Django user.
        # ---------------------------------------------------------

        sqlite_teachers = {}

        for teacher in Teacher.objects.select_related("user").all():
            sqlite_teachers[teacher.user_id] = teacher

        sqlite_classes = {}

        for school_class in SchoolClass.objects.all():
            # Match using school + name + stream + section.
            key = (
                school_class.school_id,
                school_class.name,
                school_class.stream,
                school_class.section,
            )
            sqlite_classes[key] = school_class

        sqlite_subjects = {}

        for subject in Subject.objects.all():
            key = (
                subject.school_id,
                subject.code,
            )
            sqlite_subjects[key] = subject

        print("Teacher mappings available:", len(sqlite_teachers))
        print("School class mappings available:", len(sqlite_classes))
        print("Subject mappings available:", len(sqlite_subjects))

        # ---------------------------------------------------------
        # We need SQLite information to correctly match classes
        # and subjects.
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                stream,
                section,
                school_id
            FROM schools_schoolclass
        """)

        class_rows = cursor.fetchall()

        sqlite_class_data = {
            row[0]: {
                "name": row[1],
                "stream": row[2],
                "section": row[3],
                "school_id": row[4],
            }
            for row in class_rows
        }

        cursor.execute("""
            SELECT
                id,
                school_id,
                name,
                code
            FROM academics_subject
        """)

        subject_rows = cursor.fetchall()

        sqlite_subject_data = {
            row[0]: {
                "school_id": row[1],
                "name": row[2],
                "code": row[3],
            }
            for row in subject_rows
        }

        # ---------------------------------------------------------
        # Migrate
        # ---------------------------------------------------------

        inserted = 0
        skipped = 0
        errors = 0

        print()
        print("Starting migration...")
        print()

        with transaction.atomic():

            for index, (
                sqlite_assignment_id,
                sqlite_class_id,
                sqlite_subject_id,
                sqlite_teacher_id,
            ) in enumerate(rows, start=1):

                try:

                    # ---------------------------------------------
                    # Find SQLite teacher
                    # ---------------------------------------------

                    teacher = Teacher.objects.filter(
                        id=sqlite_teacher_id
                    ).select_related("user").first()

                    if not teacher:
                        print(
                            f"WARNING: SQLite teacher "
                            f"{sqlite_teacher_id} not found in Neon"
                        )
                        errors += 1
                        continue

                    # ---------------------------------------------
                    # Find SQLite class information
                    # ---------------------------------------------

                    class_data = sqlite_class_data.get(sqlite_class_id)

                    if not class_data:
                        print(
                            f"WARNING: SQLite class "
                            f"{sqlite_class_id} not found"
                        )
                        errors += 1
                        continue

                    school_class = SchoolClass.objects.filter(
                        school_id=class_data["school_id"],
                        name=class_data["name"],
                        stream=class_data["stream"],
                        section=class_data["section"],
                    ).first()

                    if not school_class:
                        print(
                            f"WARNING: Could not match class "
                            f"{class_data['name']} "
                            f"{class_data['stream']}"
                        )
                        errors += 1
                        continue

                    # ---------------------------------------------
                    # Find SQLite subject information
                    # ---------------------------------------------

                    subject_data = sqlite_subject_data.get(
                        sqlite_subject_id
                    )

                    if not subject_data:
                        print(
                            f"WARNING: SQLite subject "
                            f"{sqlite_subject_id} not found"
                        )
                        errors += 1
                        continue

                    subject = Subject.objects.filter(
                        school_id=subject_data["school_id"],
                        code=subject_data["code"],
                    ).first()

                    if not subject:

                        # Fallback to name if code does not match
                        subject = Subject.objects.filter(
                            school_id=subject_data["school_id"],
                            name=subject_data["name"],
                        ).first()

                    if not subject:
                        print(
                            f"WARNING: Could not match subject "
                            f"{subject_data['name']} "
                            f"({subject_data['code']})"
                        )
                        errors += 1
                        continue

                    # ---------------------------------------------
                    # Prevent duplicate assignments
                    # ---------------------------------------------

                    assignment, created = (
                        TeacherSubjectAssignment.objects.get_or_create(
                            teacher=teacher,
                            school_class=school_class,
                            subject=subject,
                        )
                    )

                    if created:
                        inserted += 1
                    else:
                        skipped += 1

                    # ---------------------------------------------
                    # Progress
                    # ---------------------------------------------

                    if index % 10 == 0 or index == len(rows):
                        print(
                            f"Processed {index}/{len(rows)} "
                            f"| Inserted: {inserted} "
                            f"| Skipped: {skipped}"
                        )

                except Exception as e:
                    errors += 1

                    print(
                        f"ERROR migrating SQLite assignment "
                        f"{sqlite_assignment_id}: {e}"
                    )

        db.close()

        print()
        print("=" * 70)
        print("TEACHER ASSIGNMENT MIGRATION COMPLETED")
        print("=" * 70)
        print(f"SQLite assignments:   {len(rows)}")
        print(f"Inserted:              {inserted}")
        print(f"Skipped duplicates:    {skipped}")
        print(f"Errors:                {errors}")
        print(
            "Neon assignments now:",
            TeacherSubjectAssignment.objects.count()
        )
        print("=" * 70)

