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
# see <http://www.gnu.org/licenses/>.

from django.core.management.base import CommandError

from django_ca.crl import get_crl
from django_ca.management.base import BaseCommand
from django.utils.encoding import force_bytes


class Command(BaseCommand):
    help = "Write the certificate revocation list (CRL)."
    binary_output = True

    def add_arguments(self, parser):
        parser.add_argument(
            '-e', '--expires', type=int, default=86400, metavar='SECONDS',
            help="Seconds until a new CRL will be available (default: %(default)s).")
        parser.add_argument('--digest', default='sha512',
                            help="The name of the message digest to use (default: %(default)s).")
        parser.add_argument('path', nargs='?', default='-',
                            help='Path for the output file. Use "-" for stdout.')
        self.add_format(parser)
        self.add_ca(parser)
        super(Command, self).add_arguments(parser)

    def handle(self, path, **options):
        kwargs = {
            'type': options['format'],
            'expires': options['expires'],
            'digest': force_bytes(options['digest']),
        }

        crl = get_crl(ca=options['ca'], **kwargs)

        if path == '-':
            self.stdout.write(crl, ending=b'')
        else:
            try:
               # mistakenly reported by coverage 4.0.3 as missed branch, fixed in 4.1:
               # https://bitbucket.org/ned/coveragepy/issues/146/context-managers-confuse-branch-coverage#comment-24552176
                with open(path, 'wb') as stream:  # pragma: no branch
                    stream.write(crl)
            except IOError as e:
                raise CommandError(e)
