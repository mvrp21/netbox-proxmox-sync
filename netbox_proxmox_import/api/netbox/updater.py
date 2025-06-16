from django.core.serializers import serialize
from extras.models import Tag

class NetBoxUpdater:
    def __init__(self):
        pass

    def update_tags(self, parsed_tags):
        tags = Tag.objects.bulk_create(
            [Tag(
                name=tag_data['name'],
                slug=tag_data['slug'],
                color=tag_data['color'],
            ) for tag_data in parsed_tags],
            update_conflicts=True,
            unique_fields=['slug'],
            update_fields=['name', 'color'],
        )
        return serialize('json', tags)
        # TODO: remove the missing ones??
        # How to know which tags the plugin is managing?
