# -*- coding: utf-8 -*-

import re
import hmac
import hashlib
import logging

from nameparser import HumanName
from werkzeug.utils import cached_property

from framework.flask import request

from website import settings
from website.conferences.exceptions import ConferenceError


logger = logging.getLogger(__name__)

SSCORE_MAX_VALUE = 5
DKIM_PASS_VALUES = ['Pass']
SPF_PASS_VALUES = ['Pass', 'Neutral']

ANGLE_BRACKETS_REGEX = re.compile(r'<(.*?)>')
ROUTE_REGEX = re.compile(
    r'''
        (?P<test>test-)?
        (?P<meeting>\w*?)
        -
        (?P<category>poster|talk)
        @osf\.io
    ''',
    re.IGNORECASE | re.VERBOSE
)


class ConferenceMessage(object):

    def __init__(self):
        self.request = request._get_current_object()

    def verify(self):
        self.verify_signature()
        _ = [self.sender_email, self.route]  # noqa

    def verify_signature(self):
        """Verify that request comes from Mailgun. Based on sample code from
        http://documentation.mailgun.com/user_manual.html#webhooks
        """
        signature = hmac.new(
            key=settings.MAILGUN_API_KEY,
            msg='{}{}'.format(
                self.form['timestamp'],
                self.form['token'],
            ),
            digestmod=hashlib.sha256,
        ).hexdigest()
        if signature != self.form['signature']:
            raise ConferenceError('Invalid headers on incoming mail')

    @cached_property
    def is_spam(self):
        """Check SSCORE, DKIM, and SPF headers for spam.
        See http://documentation.mailgun.com/user_manual.html#spam-filter for
        details.

        :return: At least one header indicates spam
        """
        try:
            # Mailgun only inserts score headers for messages checked for spam.
            sscore_header = float(self.form.get('X-Mailgun-Sscore', 0))
        except (TypeError, ValueError):
            return True
        dkim_header = self.form.get('X-Mailgun-Dkim-Check-Result')
        spf_header = self.form.get('X-Mailgun-Spf')
        return (
            (sscore_header and sscore_header > SSCORE_MAX_VALUE) or
            (dkim_header and dkim_header not in DKIM_PASS_VALUES) or
            (spf_header and spf_header not in SPF_PASS_VALUES)
        )

    @cached_property
    def form(self):
        return self.request.form

    @cached_property
    def raw(self):
        return {
            'headers': dict(self.request.headers),
            'form': self.request.form.to_dict(),
            'args': self.request.args.to_dict(),
        }

    @cached_property
    def subject(self):
        subject = self.form['subject']
        subject = re.sub(r'^re:', '', subject, flags=re.I)
        subject = re.sub(r'^fwd:', '', subject, flags=re.I)
        return subject.strip()

    @cached_property
    def recipient(self):
        return self.form['recipient']

    @cached_property
    def text(self):
        return self.form['stripped-text']

    @cached_property
    def sender(self):
        return self.form['from']

    @cached_property
    def sender_name(self):
        name = ANGLE_BRACKETS_REGEX.sub('', self.sender)
        name = name.strip().replace('"', '')
        return unicode(HumanName(name))

    @cached_property
    def sender_email(self):
        match = ANGLE_BRACKETS_REGEX.search(self.sender)
        if match:
            return match.groups()[0]
        raise ConferenceError('Could not extract sender email')

    @cached_property
    def sender_display(self):
        return self.sender_name or self.sender_email.split('@')[0]

    @cached_property
    def route(self):
        match = re.search(ROUTE_REGEX, self.form['recipient'])
        if not match:
            raise ConferenceError('Invalid recipient: '.format(self.form['recipient']))
        data = match.groupdict()
        if bool(settings.DEV_MODE) != bool(data['test']):
            raise ConferenceError(
                'Mismatch between `DEV_MODE` and recipient {0}'.format(
                    self.form['recipient']
                )
            )
        return data

    @cached_property
    def conference_name(self):
        return self.route['meeting']

    @cached_property
    def conference_category(self):
        return self.route['category']

    @cached_property
    def attachments(self):
        count = self.form.get('attachment-count', 0)
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 0
        return filter(
            lambda value: value is not None,
            map(
                lambda idx: self.request.files.get('attachment-{0}'.format(idx + 1)),
                range(count),
            ),
        )
