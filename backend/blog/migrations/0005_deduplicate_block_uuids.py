"""
Migration to fix duplicate block UUIDs introduced by migration 0004.

When 0004 added the uuid column to pre-existing rows it evaluated uuid.uuid4
once and used that value as the SQL DEFAULT, so every existing row received
the same UUID. This migration:
  1. Reassigns a fresh uuid4 to every row whose UUID is shared with at least
     one other row in the same table (keeps the first row's UUID intact,
     generates a new one for every duplicate).
  2. Makes uuid non-nullable by filling any remaining NULL values.
  3. Adds a unique constraint so this can never happen again.
"""

import uuid as _uuid

from django.db import migrations, models


def _deduplicate(apps, schema_editor, model_name):
    Model = apps.get_model('blog', model_name)
    seen = set()
    # Order by pk so the earliest created row keeps its original UUID.
    for obj in Model.objects.order_by('pk'):
        if obj.uuid is None or obj.uuid in seen:
            obj.uuid = _uuid.uuid4()
            obj.save(update_fields=['uuid'])
        else:
            seen.add(obj.uuid)


def deduplicate_header_uuids(apps, schema_editor):
    _deduplicate(apps, schema_editor, 'NoteHeader')


def deduplicate_text_content_uuids(apps, schema_editor):
    _deduplicate(apps, schema_editor, 'NoteTextContent')


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_note_blocks_uuid'),
    ]

    operations = [
        # Step 1 – repair existing duplicate / NULL UUIDs via Python
        migrations.RunPython(
            deduplicate_header_uuids,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            deduplicate_text_content_uuids,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2 – make the field non-nullable and unique
        migrations.AlterField(
            model_name='noteheader',
            name='uuid',
            field=models.UUIDField(
                default=_uuid.uuid4,
                editable=False,
                unique=True,
                db_index=True,
            ),
        ),
        migrations.AlterField(
            model_name='notetextcontent',
            name='uuid',
            field=models.UUIDField(
                default=_uuid.uuid4,
                editable=False,
                unique=True,
                db_index=True,
            ),
        ),
    ]
