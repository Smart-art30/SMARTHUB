import sqlite3

from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Copy missing users 370 and 371 from SQLite to Neon."

    def handle(self, *args, **options):
        db = sqlite3.connect("db.sqlite3")
        cursor = db.cursor()

        cursor.execute("""
            SELECT
                id,
                password,
                last_login,
                is_superuser,
                username,
                first_name,
                last_name,
                email,
                is_staff,
                is_active,
                date_joined,
                role,
                school_id,
                phone,
                profile_image,
                must_change_password
            FROM accounts_user
            WHERE id IN (370, 371)
            ORDER BY id
        """)

        rows = cursor.fetchall()
        db.close()

        self.stdout.write(f"SQLite users found: {len(rows)}")

        for row in rows:
            (
                user_id,
                password,
                last_login,
                is_superuser,
                username,
                first_name,
                last_name,
                email,
                is_staff,
                is_active,
                date_joined,
                role,
                school_id,
                phone,
                profile_image,
                must_change_password,
            ) = row

            if User.objects.filter(id=user_id).exists():
                self.stdout.write(
                    f"User {user_id} already exists. Skipping."
                )
                continue

            user = User(
                id=user_id,
                password=password,
                last_login=last_login,
                is_superuser=bool(is_superuser),
                username=username,
                first_name=first_name or "",
                last_name=last_name or "",
                email=email or "",
                is_staff=bool(is_staff),
                is_active=bool(is_active),
                date_joined=date_joined,
                role=role or "",
                school_id=school_id,
                phone=phone,
                profile_image=profile_image or "",
                must_change_password=bool(must_change_password),
            )

            user.save(force_insert=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Inserted user {user_id}: {username}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nNeon users now: {User.objects.count()}"
            )
        )
