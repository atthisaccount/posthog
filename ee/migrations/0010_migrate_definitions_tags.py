# Generated by Django 3.2.5 on 2022-01-28 19:21
from django.db import migrations
from django.db.models import Q

from posthog.models.tag import tagify


def forwards(apps, schema_editor):
    Tag = apps.get_model("posthog", "Tag")
    TaggedItem = apps.get_model("posthog", "TaggedItem")
    tagged_items_to_create = []

    # Create new event definition tags
    EnterpriseEventDefinition = apps.get_model("ee", "EnterpriseEventDefinition")
    for instance in EnterpriseEventDefinition.objects.exclude(deprecated_tags__isnull=True, deprecated_tags=[]):
        if instance.deprecated_tags:
            unique_tags = set([tagify(t) for t in instance.deprecated_tags])
            for tag in unique_tags:
                new_tag, _ = Tag.objects.get_or_create(name=tag, team_id=instance.team_id)
                tagged_items_to_create.append(
                    TaggedItem(event_definition_id=instance.eventdefinition_ptr_id, tag_id=new_tag.id)
                )

    # Create new property definition tags
    EnterprisePropertyDefinition = apps.get_model("ee", "EnterprisePropertyDefinition")
    for instance in EnterprisePropertyDefinition.objects.exclude(deprecated_tags__isnull=True, deprecated_tags=[]):
        if instance.deprecated_tags:
            unique_tags = set([tagify(t) for t in instance.deprecated_tags])
            for tag in unique_tags:
                new_tag, _ = Tag.objects.get_or_create(name=tag, team_id=instance.team_id)
                tagged_items_to_create.append(
                    TaggedItem(property_definition_id=instance.propertydefinition_ptr_id, tag_id=new_tag.id)
                )

    TaggedItem.objects.bulk_create(tagged_items_to_create)


def reverse(apps, schema_editor):
    EnterpriseTaggedItem = apps.get_model("posthog", "TaggedItem")
    EnterpriseTaggedItem.objects.filter(
        Q(event_definition_id__isnull=False) | Q(property_definition_id__isnull=False)
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("ee", "0009_deprecated_old_tags"), ("posthog", "0213_deprecated_old_tags")]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]