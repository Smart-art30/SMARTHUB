import sqlite3

from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Check SQLite student user IDs against Neon users"

    def handle(self, *args, **options):

        db = sqlite3.connect("db.sqlite3")
        cursor = db.cursor()

        cursor.execute("""
            SELECT DISTINCT user_id
            FROM students_student
            ORDER BY user_id
        """)

        student_user_ids = [
            row[0]
            for row in cursor.fetchall()
        ]

        print()
        print("=" * 70)
        print("SQLite Student User → Neon User Mapping")
        print("=" * 70)

        missing = 0

        for sqlite_id in student_user_ids:

            cursor.execute(
                """
                SELECT username
                FROM accounts_user
                WHERE id = ?
                """,
                (sqlite_id,)
            )

            row = cursor.fetchone()

            if not row:
                print(
                    f"SQLite ID {sqlite_id} → "
                    f"NO SQLITE USER"
                )
                missing += 1
                continue

            username = row[0]

            neon_user = User.objects.filter(
                username=username
            ).first()

            if neon_user:
                print(
                    f"SQLite ID {sqlite_id} → "
                    f"{username} → "
                    f"Neon ID {neon_user.id}"
                )
            else:
                print(
                    f"SQLite ID {sqlite_id} → "
                    f"{username} → "
                    f"MISSING IN NEON"
                )
                missing += 1

        print()
        print("=" * 70)
        print(f"Total SQLite student user IDs: {len(student_user_ids)}")
        print(f"Missing mappings: {missing}")
        print("=" * 70)

        db.close()
