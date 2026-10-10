from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Lentech Nexus user.

    Extends Django's ``AbstractUser`` (username + password hashing + staff
    flags) so we keep battle-tested authentication while adding a unique email
    and a lightweight role used for UI decisions.

    Roles are NOT used as a security boundary on their own: object-level
    permissions and Django's ``is_staff``/``is_superuser`` flags remain
    authoritative. The role field simply describes the user's intent.
    """

    class Role(models.TextChoices):
        DEVELOPER = 'developer', 'Developer'
        CLIENT = 'client', 'Client'
        PROJECT_OWNER = 'project_owner', 'Project Owner'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.DEVELOPER,
    )
    email_verified = models.BooleanField(default=False)

    # Email is required and unique; username remains the login identifier.
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username
