from django.core.management.base import BaseCommand
from django.db import connection, transaction
from accounts.models import User


class Command(BaseCommand):
    help = "Correct Neon user IDs to match the SQLite source database."

    def handle(self, *args, **options):

        self.stdout.write("=" * 60)
        self.stdout.write("SMARTHUB: Fixing User IDs")
        self.stdout.write("=" * 60)

        try:
            with transaction.atomic():

                user_368 = User.objects.get(id=368)
                user_369 = User.objects.get(id=369)

                if user_368.username != "ghsdhhdaha":
                    raise Exception(
                        f"User 368 is {user_368.username}, "
                        "not ghsdhhdaha. Aborting."
                    )

                if user_369.username != "Head_Teacher":
                    raise Exception(
                        f"User 369 is {user_369.username}, "
                        "not Head_Teacher. Aborting."
                    )

                if User.objects.filter(id=370).exists():
                    raise Exception(
                        "User ID 370 already exists. Aborting."
                    )

                if User.objects.filter(id=371).exists():
                    raise Exception(
                        "User ID 371 already exists. Aborting."
                    )

                self.stdout.write(
                    "Changing ghsdhhdaha: 368 → 370"
                )

                self.stdout.write(
                    "Changing Head_Teacher: 369 → 371"
                )

                # Temporarily move IDs to negative values
                # to avoid any primary-key collision.
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE accounts_user
                        SET id = -368
                        WHERE id = 368
                    """)

                    cursor.execute("""
                        UPDATE accounts_user
                        SET id = -369
                        WHERE id = 369
                    """)

                    cursor.execute("""
                        UPDATE accounts_user
                        SET id = 370
                        WHERE id = -368
                    """)

                    cursor.execute("""
                        UPDATE accounts_user
                        SET id = 371
                        WHERE id = -369
                    """)

                self.stdout.write(
                    self.style.SUCCESS(
                        "✓ User IDs corrected successfully."
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"ERROR: {e}"
                )
            )
            raise

        # Reset PostgreSQL sequence so future users get
        # an ID higher than the current maximum.
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(
                    pg_get_serial_sequence(
                        'accounts_user',
                        'id'
                    ),
                    COALESCE(
                        (SELECT MAX(id) FROM accounts_user),
                        1
                    ),
                    true
                )
            """)

        self.stdout.write(
            self.style.SUCCESS(
                "✓ PostgreSQL user ID sequence synchronized."
            )
        )

        self.stdout.write(
            f"Neon users: {User.objects.count()}"
        )

