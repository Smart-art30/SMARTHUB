import sqlite3

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from students.models import Student
from schools.models import SchoolClass


class Command(BaseCommand):
    help = "Migrate students from SQLite to Neon using username-based user mapping."

    def handle(self, *args, **options):

        print("=" * 70)
        print("SMARTHUB: SQLite → Neon Student Migration")
        print("=" * 70)

        # ---------------------------------------------------------
        # Connect directly to the old SQLite database
        # ---------------------------------------------------------
        sqlite_db = sqlite3.connect("db.sqlite3")
        sqlite_db.row_factory = sqlite3.Row

        cursor = sqlite_db.cursor()

        # ---------------------------------------------------------
        # Get all SQLite students
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                user_id,
                school_id,
                student_class_id,
                admission_number,
                date_of_birth,
                photo,
                gender,
                created_at
            FROM students_student
            ORDER BY id
        """)

        sqlite_students = cursor.fetchall()

        print(f"SQLite students found: {len(sqlite_students)}")

        # ---------------------------------------------------------
        # Existing Neon students
        # ---------------------------------------------------------
        existing_count = Student.objects.count()

        print(f"Students already in Neon: {existing_count}")

        # ---------------------------------------------------------
        # If students already exist, stop rather than creating
        # duplicates.
        # ---------------------------------------------------------
        if existing_count > 0:
            print()
            print("Neon already contains students.")
            print("Migration stopped to prevent duplicate students.")
            sqlite_db.close()
            return

        print(f"Students to insert: {len(sqlite_students)}")
        print()

        inserted = 0
        skipped = 0

        # ---------------------------------------------------------
        # Migrate inside one transaction.
        #
        # If ANY student fails, PostgreSQL rolls back the entire
        # migration instead of leaving half the students inserted.
        # ---------------------------------------------------------
        try:

            with transaction.atomic():

                for sqlite_student in sqlite_students:

                    sqlite_user_id = sqlite_student["user_id"]

                    # -------------------------------------------------
                    # Find the SQLite user using the SQLite database.
                    # -------------------------------------------------
                    cursor.execute("""
                        SELECT
                            id,
                            username
                        FROM accounts_user
                        WHERE id = ?
                    """, (sqlite_user_id,))

                    sqlite_user = cursor.fetchone()

                    if not sqlite_user:
                        print(
                            f"SKIPPING Student {sqlite_student['id']}: "
                            f"SQLite user {sqlite_user_id} does not exist."
                        )
                        skipped += 1
                        continue

                    username = sqlite_user["username"]

                    # -------------------------------------------------
                    # CRITICAL:
                    #
                    # Find the corresponding Neon user by USERNAME,
                    # NOT by SQLite ID.
                    # -------------------------------------------------
                    try:
                        neon_user = User.objects.get(username=username)
                    except User.DoesNotExist:

                        print(
                            f"ERROR: SQLite user {sqlite_user_id} "
                            f"({username}) does not exist in Neon."
                        )

                        raise Exception(
                            f"Missing Neon user for username: {username}"
                        )

                    # -------------------------------------------------
                    # Make sure this Neon user does not already have
                    # a Student profile.
                    # -------------------------------------------------
                    if Student.objects.filter(user=neon_user).exists():

                        print(
                            f"SKIPPING Student {sqlite_student['id']}: "
                            f"Neon user {neon_user.id} ({username}) "
                            f"already has a Student profile."
                        )

                        skipped += 1
                        continue

                    # -------------------------------------------------
                    # Get the SchoolClass from Neon.
                    #
                    # The fixture already loaded the school classes.
                    # We use the same primary key here.
                    # -------------------------------------------------
                    student_class_id = sqlite_student["student_class_id"]

                    try:
                        neon_class = SchoolClass.objects.get(
                            id=student_class_id
                        )
                    except SchoolClass.DoesNotExist:

                        print(
                            f"ERROR: SchoolClass {student_class_id} "
                            f"does not exist in Neon."
                        )

                        raise Exception(
                            f"Missing Neon SchoolClass: "
                            f"{student_class_id}"
                        )

                    # -------------------------------------------------
                    # Create the Student.
                    #
                    # IMPORTANT:
                    # user=neon_user
                    #
                    # NOT:
                    # user_id=sqlite_user_id
                    # -------------------------------------------------
                    student = Student(
                        user=neon_user,
                        school_id=sqlite_student["school_id"],
                        student_class=neon_class,
                        admission_number=sqlite_student["admission_number"],
                        date_of_birth=sqlite_student["date_of_birth"],
                        photo=sqlite_student["photo"] or "",
                        gender=sqlite_student["gender"] or "",
                    )

                    # Preserve created_at if your model allows it.
                    if sqlite_student["created_at"]:
                        student.created_at = sqlite_student["created_at"]

                    student.save()

                    inserted += 1

                    if inserted % 50 == 0 or inserted == len(sqlite_students):
                        print(
                            f"Inserted {inserted}/{len(sqlite_students)} students"
                        )

            # ---------------------------------------------------------
            # Transaction succeeded
            # ---------------------------------------------------------
            print()
            print("=" * 70)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 70)
            print(f"Inserted: {inserted}")
            print(f"Skipped:  {skipped}")
            print(f"Neon students now: {Student.objects.count()}")
            print("=" * 70)

        except Exception as e:

            print()
            print("=" * 70)
            print("MIGRATION FAILED")
            print("=" * 70)
            print(f"Reason: {e}")
            print()
            print("The transaction was rolled back.")
            print("No partially migrated students should remain.")
            print("=" * 70)

        finally:
            sqlite_db.close()
