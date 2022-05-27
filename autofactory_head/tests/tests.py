import datetime

from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from packing.models import MarkingOperation

User = get_user_model()


class InterfaceTests(APITestCase):
    def setUp(self) -> None:
        User.objects.create_user(username='TestUser', password='1234567')
        self.client.login(username='TestUser', password='1234567')

    def test_marking_pages(self):
        response = self.client.get(reverse('marking'))
        self.assertEquals(response.status_code, 200)

        marking_operation = MarkingOperation.objects.create(production_date=datetime.datetime.today())

        response = self.client.get(reverse('marking_operation_edit', kwargs={'pk': marking_operation.guid}))
        self.assertEquals(response.status_code, 200)

        response = self.client.get(reverse('marking_detail', kwargs={'pk': marking_operation.guid}))
        self.assertEquals(response.status_code, 200)

    def test_common_pages(self):
        response = self.client.get(reverse('index'), format='json')
        self.assertEquals(response.status_code, 200)
