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

from django.forms import widgets
from django.utils.translation import ugettext as _


class CriticalWidget(widgets.CheckboxInput):
    def render(self, name, value, attrs=None):
        html = super(CriticalWidget, self).render(name, value, attrs=attrs)
        label = '<label for="%s">%s</label>' % (attrs.get('id'), _('critical'))
        html = '<span class="critical-widget-wrapper">%s%s</span>' % (html, label)
        return html

    class Media:
        css = {
            'all': ('django_ca/admin/css/criticalwidget.css', ),
        }

class PathlenWidget(widgets.TextInput):
    def render(self, name, value, attrs=None):
        html = super(PathlenWidget, self).render(name, value, attrs=attrs)
        label = '<label for="%s">%s</label>' % (attrs.get('id'), _('pathlen:'))
        html = '<span class="pathlen-widget-wrapper">%s%s</span>' % (label, html)
        return html

    class Media:
        css = {
            'all': ('django_ca/admin/css/pathlenwidget.css', ),
        }


class CustomMultiWidget(widgets.MultiWidget):
    """Wraps the multi widget into a <p> element."""

    def format_output(self, rendered_widgets):
        # NOTE: We use a <p> because djangos stock forms.css takes care of indent this way.
        rendered_widgets.insert(0, '<p class="multi-widget">')
        rendered_widgets.append('</p>')
        return ''.join(rendered_widgets)


class KeyUsageWidget(CustomMultiWidget):
    def __init__(self, choices, attrs=None):
        _widgets = (
            widgets.SelectMultiple(choices=choices, attrs=attrs),
            CriticalWidget(),
        )
        super(KeyUsageWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return value
        return ([], True)


class BasicConstraintsWidget(CustomMultiWidget):
    def __init__(self, choices, attrs=None):
        _widgets = (
            widgets.Select(choices=choices, attrs=attrs),
            PathlenWidget(),
            CriticalWidget(),
        )
        super(BasicConstraintsWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return value
        return ['CA:FALSE', None, True]

    class Media:
        js = (
            'django_ca/admin/js/basicconstraints.js',
        )
