# -*- coding: utf-8 -*-
#
# This file is part of django-ca (https://github.com/mathiasertl/django-ca).
#
# django-ca is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# django-ca is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-ca.  If not,
# see <http://www.gnu.org/licenses/>

from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils import timezone

from ..models import Certificate
from .base import DjangoCAWithCertTestCase


class AdminTestCase(DjangoCAWithCertTestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='user', password='password',
                                                  email='user@example.com')
        self.add_url = reverse('admin:django_ca_certificate_add')
        self.changelist_url = reverse('admin:django_ca_certificate_changelist')
        self.client = Client()
        self.assertTrue(self.client.login(username='user', password='password'))
        super(AdminTestCase, self).setUp()

    def assertCSS(self, response, path):
        css = '<link href="%s" type="text/css" media="all" rel="stylesheet" />' % static(path)
        self.assertInHTML(css, response.content.decode('utf-8'), 1)

    def change_url(self, pk=None):
        if pk is None:
            pk = self.cert.pk

        return reverse('admin:django_ca_certificate_change', args=(pk, ))


class ChangelistTestCase(AdminTestCase):
    """Test the changelist view."""

    def assertCerts(self, response, certs):
        self.assertEqual(set(response.context['cl'].result_list), set(certs))

    def test_get(self):
        response = self.client.get(self.changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertCerts(response, [self.cert])

        self.assertCSS(response, 'django_ca/admin/css/monospace.css')
        self.assertCSS(response, 'django_ca/admin/css/certificateadmin.css')

    def test_status(self):
        response = self.client.get('%s?status=valid' % self.changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertCerts(response, [self.cert])
        response = self.client.get('%s?status=expired' % self.changelist_url)
        self.assertCerts(response, [])
        self.assertEqual(response.status_code, 200)
        response = self.client.get('%s?status=revoked' % self.changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertCerts(response, [])

        # get the cert and manipulate it so that it shows up in the changelist:
        cert = Certificate.objects.get(serial=self.cert.serial)
        cert.expires = timezone.now() - timedelta(days=1)
        cert.save()

        response = self.client.get('%s?status=expired' % self.changelist_url)
        self.assertCerts(response, [self.cert])
        self.assertEqual(response.status_code, 200)

        cert.revoke()
        response = self.client.get('%s?status=revoked' % self.changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertCerts(response, [self.cert])

    def test_unauthorized(self):
        client = Client()
        response = client.get(self.changelist_url)
        self.assertEqual(response.status_code, 302)


class RevokeActionTestCase(AdminTestCase):
    """Test the "revoke" action in the changelist."""

    def test_basic(self):
        data = {
            'action': 'revoke', '_selected_action': [self.cert.pk],
        }
        response = self.client.post(self.changelist_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.changelist_url)

        cert = Certificate.objects.get(serial=self.cert.serial)
        self.assertTrue(cert.revoked)
        self.assertIsNone(cert.revoked_reason)

        # revoking revoked certs does nothing:
        response = self.client.post(self.changelist_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.changelist_url)


class ChangeTestCase(AdminTestCase):
    def test_basic(self):
        response = self.client.get(self.change_url())
        self.assertEqual(response.status_code, 200)

        templates = [t.name for t in response.templates]
        self.assertIn('django_ca/admin/change_form.html', templates)
        self.assertIn('admin/change_form.html', templates)
        self.assertCSS(response, 'django_ca/admin/css/monospace.css')
        self.assertCSS(response, 'django_ca/admin/css/certificateadmin.css')


class AddTestCase(AdminTestCase):
    def test_get(self):
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        templates = [t.name for t in response.templates]
        self.assertIn('django_ca/admin/change_form.html', templates)
        self.assertIn('admin/change_form.html', templates)
        self.assertCSS(response, 'django_ca/admin/css/monospace.css')
        self.assertCSS(response, 'django_ca/admin/css/certificateadmin.css')

    def test_add(self):
        cn = 'test-add.example.com'
        response = self.client.post(self.add_url, data={
            'csr': self.csr_pem,
            'ca': self.ca.pk,
            'profile': 'webserver',
            'subject_0': 'US',
            'subject_5': cn,
            'subjectAltName_1': True,
            'algorithm': 'sha256',
            'expires': '2018-04-12',
            'keyUsage_0': ['digitalSignature', 'keyAgreement', ],
            'keyUsage_1': True,
            'extendedKeyUsage_0': ['clientAuth', 'serverAuth', ],
            'extendedKeyUsage_1': False,
        })
        self.assertEqual(response.status_code, 302)
        cert = Certificate.objects.get(cn=cn)
        self.assertEqual(response['Location'], self.changelist_url)

        self.assertSubject(cert.x509, {'C': 'US', 'CN': cn})
        self.assertEqual(cert.subjectAltName(), 'DNS:%s' % cn)
        self.assertEqual(cert.basicConstraints(), 'critical,CA:FALSE')
        self.assertEqual(cert.keyUsage(), 'critical,Digital Signature, Key Agreement')
        self.assertEqual(cert.extendedKeyUsage(),
                         'TLS Web Client Authentication, TLS Web Server Authentication')
        self.assertEqual(cert.ca, self.ca)
        self.assertEqual(cert.csr, self.csr_pem)