# coding: utf-8
from common.tests import create_api_test_class
from django.contrib.admin import site
from django.test import TestCase
from django.urls import reverse
from model_mommy import mommy

from fallout.models import MODELS, Player


def create_admin_tests():
    """
    Crée des tests génériques de navigation sur l'ensemble des pages de l'administration
    :return: Tests
    """
    tests = {}
    base_urls, namespace, app_label = site.urls
    for base_url in base_urls:
        for url in getattr(base_url, 'url_patterns', []):
            view = getattr(url.callback, 'model_admin', None)
            if not view or not url.name or url.name.endswith('_autocomplete'):
                continue
            model = view.model
            if model not in MODELS:
                continue
            test = tests.get(model)
            pk_required = '?P<object_id>' in url.pattern.regex.pattern
            if not test:

                def setup(cls):
                    cls.player = Player.objects.create_superuser('admin', '', '')
                    cls.instance = mommy.make(cls.model)

                def get(self, url=url, pk_required=pk_required):
                    url = reverse(f'{namespace}:{url.name}', args=(self.instance.pk, ) if pk_required else ())
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 302)
                    self.client.force_login(self.player)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    return url

                test_name = f'{model._meta.object_name}AdminPageCheckTest'
                test = type(test_name, (TestCase, ), dict(name=test_name, model=model, get=get))
                test.setUpTestData = classmethod(setup)
                tests[model] = test

            setattr(test, f'test_admin_get_{url.name}', lambda s, u=url, p=pk_required: s.get(u, p))
    return tests


# Tests automatisées de l'interface d'administration
for model, test in create_admin_tests().items():
    locals().update({test.name: test})


RECIPES = {}

# Tests automatisées pour tous les modèles liés à une API REST
for model in MODELS:
    model_name = model._meta.object_name
    create_api_test_class(model, namespace='fallout-api', data=RECIPES.get(model, None))

# La création d'un nouvel utilisateur via l'API est autorisé sans authentification
create_api_test_class(Player, namespace='fallout-api', test_post=False)
