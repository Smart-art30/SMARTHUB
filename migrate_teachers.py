import sqlite3

from django.db import transaction
from accounts.models import User
from schools.models import School
from teachers.models import Teacher


SQLITE_DB = "db_backup.sqlite3"


teacher_fields = [
    "employee_id",
    "phone",
    "date_joined",
    "date_of_birth",
    "gender",
    "designation",
    "qualification",
    "specialization",
    "is_class_teacher",
    "is_approved",
]


print("=" * 70)
print("SMARTHUB: SQLite → Neon Teacher Migration")
print("=" * 70)

conn = sqlite3.connect(SQLITE_DB)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT
        id,
        user_id,
        school_id,
        employee_id,
        phone,
        date_joined,
        date_of_birth,
        gender,
        designation,
        qualification,
        specialization,
        is_class_teacher,
        profile_picture,
        is_approved
    FROM teachers_teacher
    ORDER BY id
""")

teachers = cursor.fetchall()

print(f"\nSQLite teachers found: {len(teachers)}")

created = 0
updated = 0

with transaction.atomic():

    for row in teachers:

        teacher_id = row["id"]
        user_id = row["user_id"]
        school_id = row["school_id"]

        # --------------------------------------------------
        # Find the existing Neon user
        # --------------------------------------------------
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            print(
                f"SKIPPED Teacher {teacher_id}: "
                f"Neon user {user_id} does not exist."
            )
            continue

        # --------------------------------------------------
        # Find the existing Neon school
        # --------------------------------------------------
        try:
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            print(
                f"SKIPPED Teacher {teacher_id}: "
                f"Neon school {school_id} does not exist."
            )
            continue

        # --------------------------------------------------
        # Build teacher data
        # --------------------------------------------------
        data = {
            "user": user,
            "school": school,
            "employee_id": row["employee_id"] or "",
            "phone": row["phone"] or "",
            "date_joined": row["date_joined"],
            "date_of_birth": row["date_of_birth"],
            "gender": row["gender"] or "",
            "designation": row["designation"] or "",
            "qualification": row["qualification"] or "",
            "specialization": row["specialization"] or "",
            "is_class_teacher": bool(row["is_class_teacher"]),
            "is_approved": bool(row["is_approved"]),
        }

        # --------------------------------------------------
        # Restore profile picture path if it exists
        # --------------------------------------------------
        if row["profile_picture"]:
            data["profile_picture"] = row["profile_picture"]

        # --------------------------------------------------
        # Create or update using the existing Teacher ID
        # --------------------------------------------------
        teacher, was_created = Teacher.objects.update_or_create(
            id=teacher_id,
            defaults=data,
        )

        if was_created:
            created += 1
            print(
                f"CREATED | Teacher ID={teacher.id} | "
                f"User={user.username} | "
                f"School={school.name} | "
                f"Approved={teacher.is_approved}"
            )
        else:
            updated += 1
            print(
                f"UPDATED | Teacher ID={teacher.id} | "
                f"User={user.username} | "
                f"School={school.name} | "
                f"Approved={teacher.is_approved}"
            )


conn.close()

print("\n" + "=" * 70)
print("MIGRATION COMPLETE")
print("=" * 70)
print(f"Created: {created}")
print(f"Updated: {updated}")
print(f"Total teachers now in Neon: {Teacher.objects.count()}")

