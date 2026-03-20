import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from django.urls import reverse

from apps.integrations import registry
from apps.integrations.models import (
    IntegrationDefinition,
    PublishTarget,
    PublishLog,
)
from blog.models import Integration, Blog, Note


@pytest.mark.django_db
def test_create_integration_definition():
    definition = IntegrationDefinition.objects.create(
        code='test_code',
        name='Test Integration',
        category='social',
        description='desc',
        config_schema={'type': 'object'},
        handler_path='apps.integrations.handlers.webhook.WebhookHandler',
    )
    assert definition.pk is not None
    assert definition.code == 'test_code'
    assert definition.is_active


@pytest.mark.django_db
def test_create_integration_with_definition():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='u', password='pass')

    definition = IntegrationDefinition.objects.create(
        code='test2',
        name='Test2',
        category='automation',
        config_schema={'type': 'object'},
        handler_path='apps.integrations.handlers.webhook.WebhookHandler',
    )
    integ = Integration.objects.create(
        owner=user,
        definition=definition,
        name='legacy',
        title='Human Title',
        provider='telegram',
    )
    assert integ.definition == definition
    assert integ.title == 'Human Title'


@pytest.mark.django_db
def test_publish_target_generic_fk():
    # prepare objects
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='u2', password='pass')
    blog = Blog.objects.create(owner=user, title='b')
    note = Note.objects.create(blog=blog, title='n')

    definition = IntegrationDefinition.objects.create(
        code='test3',
        name='Test3',
        category='feed',
        config_schema={'type': 'object'},
        handler_path='apps.integrations.handlers.webhook.WebhookHandler',
    )
    integ = Integration.objects.create(
        owner=user,
        definition=definition,
        name='n',
        title='t',
        provider='telegram',
    )
    ct = ContentType.objects.get_for_model(note)
    target = PublishTarget.objects.create(
        integration=integ,
        content_type=ct,
        object_id=note.uuid,  # store uuid identifier, not pk
    )
    assert target.content_type == ct
    assert target.object_id == note.uuid


class DummyHandler:
    def publish(self, integration, publish_target, content):
        # pretend successful
        return {'ok': True}


class ErrorHandler:
    def publish(self, integration, publish_target, content):
        raise RuntimeError('fail')


@pytest.mark.django_db
def test_successful_publish(monkeypatch):
    # create objects similar to above
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='u3', password='pass')
    blog = Blog.objects.create(owner=user, title='b3')
    note = Note.objects.create(blog=blog, title='n3')

    definition = IntegrationDefinition.objects.create(
        code='test4',
        name='Test4',
        category='feed',
        config_schema={'type': 'object'},
        handler_path='unused',
    )
    integ = Integration.objects.create(
        owner=user,
        definition=definition,
        name='n4',
        title='t4',
        provider='telegram',
    )
    ct = ContentType.objects.get_for_model(note)
    target = PublishTarget.objects.create(
        integration=integ,
        content_type=ct,
        object_id=note.uuid,
    )
    # register dummy
    registry.register('test4', DummyHandler)
    from apps.integrations.services.publish_service import publish_target
    publish_target(target, {'foo': 'bar'})
    target.refresh_from_db()
    assert target.status == PublishTarget.STATUS_PUBLISHED
    assert target.retry_count == 0
    log = PublishLog.objects.filter(publish_target=target).first()
    assert log is not None
    assert log.status == PublishLog.STATUS_SUCCESS


@pytest.mark.django_db
def test_error_publish(monkeypatch):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='u4', password='pass')
    blog = Blog.objects.create(owner=user, title='b4')
    note = Note.objects.create(blog=blog, title='n4')

    definition = IntegrationDefinition.objects.create(
        code='test5',
        name='Test5',
        category='feed',
        config_schema={'type': 'object'},
        handler_path='unused',
    )
    integ = Integration.objects.create(
        owner=user,
        definition=definition,
        name='n5',
        title='t5',
        provider='telegram',
    )
    ct = ContentType.objects.get_for_model(note)
    target = PublishTarget.objects.create(
        integration=integ,
        content_type=ct,
        object_id=note.uuid,
    )
    registry.register('test5', ErrorHandler)
    from apps.integrations.services.publish_service import publish_target
    publish_target(target, {'foo': 'b'})
    target.refresh_from_db()
    assert target.status == PublishTarget.STATUS_FAILED
    assert target.retry_count == 1
    log = PublishLog.objects.filter(publish_target=target).first()
    assert log is not None
    assert log.status == PublishLog.STATUS_ERROR
    assert 'fail' in log.error_message


# API endpoints tests start here


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_list_integration_definitions(api_client):
    IntegrationDefinition.objects.create(
        code='a1',
        name='Active',
        category='cat',
        config_schema={},
        handler_path='h',
    )
    IntegrationDefinition.objects.create(
        code='i1',
        name='Inactive',
        category='cat',
        config_schema={},
        handler_path='h',
        is_active=False,
    )
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='u5', password='pass')
    api_client.force_authenticate(user=user)
    url = reverse('integration-definitions-list')
    resp = api_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    codes = {item['code'] for item in data}
    assert 'a1' in codes and 'i1' not in codes


@pytest.mark.django_db
def test_integration_crud(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='u6', password='pass')
    api_client.force_authenticate(user=user)
    defn = IntegrationDefinition.objects.create(
        code='c2',
        name='Def2',
        category='cat',
        config_schema={'type': 'object'},
        handler_path='h',
    )
    url = reverse('integrations-list')
    resp = api_client.post(
        url,
        {'title': 'T', 'definition_id': str(defn.pk), 'credentials': {}},
        format='json',
    )
    assert resp.status_code == 201, resp.content
    integ_id = resp.json()['id']
    url2 = reverse('integrations-detail', args=[integ_id])
    resp = api_client.patch(url2, {'title': 'T2'}, format='json')
    assert resp.status_code == 200
    assert resp.json()['title'] == 'T2'
    resp = api_client.delete(url2)
    assert resp.status_code == 204


@pytest.mark.django_db
def test_publish_target_api_and_permissions(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user1 = User.objects.create_user(username='u7', password='pass')
    user2 = User.objects.create_user(username='u8', password='pass')
    api_client.force_authenticate(user=user1)
    blog = Blog.objects.create(owner=user1, title='b7')
    note = Note.objects.create(blog=blog, title='n7')
    defn = IntegrationDefinition.objects.create(
        code='c3',
        name='Def3',
        category='cat',
        config_schema={},
        handler_path='h',
    )
    integ = Integration.objects.create(
        owner=user1,
        definition=defn,
        name='n',
        title='t',
        provider='telegram',
    )
    url = reverse('publish-targets-list')
    resp = api_client.post(
        url,
        {
            'integration_id': integ.id,
            'content_type_id': ContentType.objects.get_for_model(note).id,
            'object_id': str(note.uuid),
        },
        format='json',
    )
    assert resp.status_code == 201
    target_id = resp.json()['id']
    api_client.force_authenticate(user=user2)
    url_detail = reverse('publish-targets-detail', args=[target_id])
    assert api_client.get(url_detail).status_code == 404
    api_client.force_authenticate(user=user1)
    registry.register(defn.code, DummyHandler)
    resp = api_client.post(f"{url_detail}publish/", {}, format='json')
    assert resp.status_code == 200
    resp = api_client.get(f"{url_detail}logs/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
