import sqlite3

from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import StudentMark, Subject, Exam
from students.models import Student
from accounts.models import User
from schools.models import SchoolClass


class Command(BaseCommand):
    help = "Migrate StudentMark records from SQLite to Neon"

    def handle(self, *args, **options):

        self.stdout.write("=" * 70)
        self.stdout.write("SMARTHUB: SQLite → Neon Student Marks Migration")
        self.stdout.write("=" * 70)

        # ---------------------------------------------------------
        # CONNECT TO SQLITE
        # ---------------------------------------------------------
        db = sqlite3.connect("db.sqlite3")
        cursor = db.cursor()

        cursor.execute("""
            SELECT
                id,
                student_id,
                subject_id,
                exam_id,
                school_class_id,
                marks,
                facilitator_id
            FROM academics_studentmark
            ORDER BY id
        """)

        rows = cursor.fetchall()

        self.stdout.write(
            f"SQLite student marks found: {len(rows)}"
        )

        # ---------------------------------------------------------
        # EXISTING NEON MARKS
        # ---------------------------------------------------------
        existing_count = StudentMark.objects.count()

        self.stdout.write(
            f"Student marks already in Neon: {existing_count}"
        )

        # ---------------------------------------------------------
        # BUILD SQLITE → NEON STUDENT MAPPING
        #
        # SQLite Student:
        #     student.user_id
        #
        # Neon Student:
        #     Student.user_id
        #
        # We match through username rather than assuming
        # user IDs are identical.
        # ---------------------------------------------------------
        student_map = {}

        cursor.execute("""
            SELECT
                s.id,
                u.username
            FROM students_student s
            JOIN accounts_user u
                ON s.user_id = u.id
        """)

        sqlite_students = cursor.fetchall()

        for sqlite_student_id, username in sqlite_students:

            neon_user = User.objects.filter(
                username=username
            ).first()

            if not neon_user:
                self.stdout.write(
                    self.style.ERROR(
                        f"Missing Neon user: {username}"
                    )
                )
                continue

            neon_student = Student.objects.filter(
                user=neon_user
            ).first()

            if not neon_student:
                self.stdout.write(
                    self.style.ERROR(
                        f"Missing Neon student for user: {username}"
                    )
                )
                continue

            student_map[sqlite_student_id] = neon_student.id

        self.stdout.write(
            f"Student mappings available: {len(student_map)}"
        )

        # ---------------------------------------------------------
        # BUILD SUBJECT MAP
        #
        # Match using school + subject code.
        # ---------------------------------------------------------
        subject_map = {}

        cursor.execute("""
            SELECT id, school_id, code
            FROM academics_subject
        """)

        for sqlite_id, school_id, code in cursor.fetchall():

            neon_subject = Subject.objects.filter(
                school_id=school_id,
                code=code
            ).first()

            if neon_subject:
                subject_map[sqlite_id] = neon_subject.id
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Missing Neon subject: "
                        f"SQLite ID {sqlite_id}, code {code}"
                    )
                )

        self.stdout.write(
            f"Subject mappings available: {len(subject_map)}"
        )

        # ---------------------------------------------------------
        # BUILD EXAM MAP
        #
        # Match using:
        # school
        # term
        # exam_type
        # ---------------------------------------------------------
        exam_map = {}

        cursor.execute("""
            SELECT
                e.id,
                e.school_id,
                e.term_id,
                e.exam_type
            FROM academics_exam e
        """)

        for sqlite_exam_id, school_id, term_id, exam_type in cursor.fetchall():

            cursor.execute("""
                SELECT year, term
                FROM academics_academicterm
                WHERE id = ?
            """, (term_id,))

            term_data = cursor.fetchone()

            if not term_data:
                self.stdout.write(
                    self.style.ERROR(
                        f"Missing SQLite term for exam "
                        f"{sqlite_exam_id}"
                    )
                )
                continue

            year, term_name = term_data

            neon_exam = Exam.objects.filter(
                school_id=school_id,
                term__year=year,
                term__term=term_name,
                exam_type=exam_type
            ).first()

            if neon_exam:
                exam_map[sqlite_exam_id] = neon_exam.id
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Missing Neon exam: SQLite ID "
                        f"{sqlite_exam_id}"
                    )
                )

        self.stdout.write(
            f"Exam mappings available: {len(exam_map)}"
        )

        # ---------------------------------------------------------
        # BUILD SCHOOL CLASS MAP
        #
        # SchoolClass IDs may also differ between databases.
        # Match using school + name.
        # ---------------------------------------------------------
        class_map = {}

        cursor.execute("""
            SELECT id, school_id, name
            FROM schools_schoolclass
        """)

        for sqlite_class_id, school_id, name in cursor.fetchall():

            neon_class = SchoolClass.objects.filter(
                school_id=school_id,
                name=name
            ).first()

            if neon_class:
                class_map[sqlite_class_id] = neon_class.id
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Missing Neon class: "
                        f"{name} (SQLite ID {sqlite_class_id})"
                    )
                )

        self.stdout.write(
            f"School class mappings available: {len(class_map)}"
        )

        # ---------------------------------------------------------
        # BUILD FACILITATOR MAP
        #
        # IMPORTANT:
        # Never assume facilitator IDs are the same.
        # Match SQLite user ID → username → Neon user.
        # ---------------------------------------------------------
        facilitator_map = {}

        cursor.execute("""
            SELECT id, username
            FROM accounts_user
        """)

        for sqlite_user_id, username in cursor.fetchall():

            neon_user = User.objects.filter(
                username=username
            ).first()

            if neon_user:
                facilitator_map[sqlite_user_id] = neon_user.id

        self.stdout.write(
            f"Facilitator mappings available: "
            f"{len(facilitator_map)}"
        )

        # ---------------------------------------------------------
        # MIGRATE MARKS
        # ---------------------------------------------------------
        inserted = 0
        skipped = 0
        errors = 0

        self.stdout.write("")
        self.stdout.write("Starting migration...")
        self.stdout.write("")

        try:

            with transaction.atomic():

                for row in rows:

                    (
                        sqlite_mark_id,
                        sqlite_student_id,
                        sqlite_subject_id,
                        sqlite_exam_id,
                        sqlite_class_id,
                        marks,
                        sqlite_facilitator_id,
                    ) = row

                    # ---------------------------------------------
                    # STUDENT
                    # ---------------------------------------------
                    neon_student_id = student_map.get(
                        sqlite_student_id
                    )

                    if not neon_student_id:
                        self.stdout.write(
                            self.style.ERROR(
                                f"SKIP mark {sqlite_mark_id}: "
                                f"student {sqlite_student_id} "
                                f"not mapped"
                            )
                        )
                        errors += 1
                        continue

                    # ---------------------------------------------
                    # SUBJECT
                    # ---------------------------------------------
                    neon_subject_id = subject_map.get(
                        sqlite_subject_id
                    )

                    if not neon_subject_id:
                        self.stdout.write(
                            self.style.ERROR(
                                f"SKIP mark {sqlite_mark_id}: "
                                f"subject {sqlite_subject_id} "
                                f"not mapped"
                            )
                        )
                        errors += 1
                        continue

                    # ---------------------------------------------
                    # EXAM
                    # ---------------------------------------------
                    neon_exam_id = exam_map.get(
                        sqlite_exam_id
                    )

                    if not neon_exam_id:
                        self.stdout.write(
                            self.style.ERROR(
                                f"SKIP mark {sqlite_mark_id}: "
                                f"exam {sqlite_exam_id} "
                                f"not mapped"
                            )
                        )
                        errors += 1
                        continue

                    # ---------------------------------------------
                    # SCHOOL CLASS
                    # ---------------------------------------------
                    neon_class_id = None

                    if sqlite_class_id:
                        neon_class_id = class_map.get(
                            sqlite_class_id
                        )

                        if not neon_class_id:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"SKIP mark {sqlite_mark_id}: "
                                    f"class {sqlite_class_id} "
                                    f"not mapped"
                                )
                            )
                            errors += 1
                            continue

                    # ---------------------------------------------
                    # FACILITATOR
                    # ---------------------------------------------
                    neon_facilitator_id = None

                    if sqlite_facilitator_id:
                        neon_facilitator_id = facilitator_map.get(
                            sqlite_facilitator_id
                        )

                        if not neon_facilitator_id:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Mark {sqlite_mark_id}: "
                                    f"facilitator "
                                    f"{sqlite_facilitator_id} "
                                    f"not mapped; setting NULL"
                                )
                            )

                    # ---------------------------------------------
                    # CHECK DUPLICATE
                    # ---------------------------------------------
                    exists = StudentMark.objects.filter(
                        student_id=neon_student_id,
                        subject_id=neon_subject_id,
                        exam_id=neon_exam_id
                    ).exists()

                    if exists:
                        skipped += 1
                        continue

                    # ---------------------------------------------
                    # CREATE MARK
                    # ---------------------------------------------
                    StudentMark.objects.create(
                        student_id=neon_student_id,
                        subject_id=neon_subject_id,
                        exam_id=neon_exam_id,
                        school_class_id=neon_class_id,
                        marks=marks,
                        facilitator_id=neon_facilitator_id,
                    )

                    inserted += 1

                    if inserted % 500 == 0:
                        self.stdout.write(
                            f"Inserted {inserted}/{len(rows)} marks"
                        )

        except Exception as e:

            self.stdout.write("")
            self.stdout.write(
                self.style.ERROR(
                    f"MIGRATION FAILED: {e}"
                )
            )

            db.close()
            raise

        db.close()

        # ---------------------------------------------------------
        # FINAL REPORT
        # ---------------------------------------------------------
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write(
            self.style.SUCCESS(
                "STUDENT MARK MIGRATION COMPLETED"
            )
        )
        self.stdout.write("=" * 70)

        self.stdout.write(
            f"SQLite marks:       {len(rows)}"
        )

        self.stdout.write(
            f"Inserted:            {inserted}"
        )

        self.stdout.write(
            f"Skipped duplicates:  {skipped}"
        )

        self.stdout.write(
            f"Errors:              {errors}"
        )

        self.stdout.write(
            f"Neon marks now:      {StudentMark.objects.count()}"
        )

        self.stdout.write("=" * 70)
