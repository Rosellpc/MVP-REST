from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        permissions = [
            ("access_staff", "Puede acceder a administración interna"),
            ("access_kitchen", "Puede acceder a cocina"),
            ("access_bar", "Puede acceder a barra"),
        ]
