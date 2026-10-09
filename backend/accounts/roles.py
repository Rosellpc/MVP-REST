ROLE_PERMISSIONS = {
    "ADMIN": {"access_staff", "access_kitchen", "access_bar"},
    "KITCHEN": {"access_kitchen"},
    "CHEF": {"access_kitchen"},
    "BAR": {"access_bar"},
}


def user_payload(user):
    return {
        "id": user.pk,
        "is_superuser": user.is_superuser,
        "username": user.username,
        "display_name": user.get_full_name() or user.username,
        "roles": list(user.groups.filter(name__in=ROLE_PERMISSIONS).values_list("name", flat=True)),
        "permissions": sorted(user.get_all_permissions()),
    }
