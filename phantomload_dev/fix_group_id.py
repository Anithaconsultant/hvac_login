from accounts.models import CustomUser
from django.db.models import Count
from accounts.utils import generate_short_id

duplicates = CustomUser.objects.values('group_id') \
    .annotate(count=Count('id')) \
    .filter(count__gt=1)

for entry in duplicates:
    gid = entry['group_id']
    users = CustomUser.objects.filter(group_id=gid)

    first = True

    for user in users:
        if first:
            first = False
            continue

        while True:
            new_gid = generate_short_id(10)
            if not CustomUser.objects.filter(group_id=new_gid).exists():
                user.group_id = new_gid
                user.save()
                print("Updated:", user.id, "->", new_gid)
                break