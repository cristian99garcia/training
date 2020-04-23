# Copyright (c) 2014 Martin Abente - tch@sugarlabs.org

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import json

from gi.repository import Gio 
from gi.repository import Soup


class ZendeskError(Exception):
    pass


class FieldHelper(object):

    IDS = 'zendesk/fields'

    def __init__(self):
        # FIXME #3926 GConf get_list is missing
        settings = Gio.Settings('org.sugarlabs.services') 
        raw = settings.get(self.IDS)
        if not raw:
            raise ZendeskError('soupdesk is missing fields')
        self._ids = [int(e.get_string()) for e in raw.get_list()]

    def get_field(self, index, value):
        field = {}
        field['id'] = self._ids[index]
        field['value'] = value
        return field


class Request(object):

    URL = 'zendesk/url'
    TOKEN = 'zendesk/token'

    def __init__(self):
        settings = Gio.Settings('org.sugarlabs.services') 
        self._url = settings.get_string(self.URL)

        self._token = settings.get_string(self.TOKEN)
        self._data = None

        if not self._url or not self._token:
            raise ZendeskError('soupdesk is missing URL or TOKEN')

    def _authorize(self):
        return 'Basic %s' % self._token

    def _request(self, method, url, data, content):
        uri = Soup.URI.new(url)

        message = Soup.Message(method=method, uri=uri)
        message.request_body.append(data)
        message.request_headers.append('Content-Type', content)
        message.request_headers.append('Authorization', self._authorize())

        #logger = Soup.Logger.new(Soup.LoggerLogLevel.BODY, -1)

        session = Soup.SessionSync()
        #session.add_feature(logger)
        session.add_feature_by_type(Soup.ProxyResolverDefault)
        session.send_message(message)

        self._data = message.response_body.data
        if not 200 <= message.status_code < 300:
            raise ZendeskError(self._data)


class Ticket(Request):

    RESOURCE = '/api/v2/tickets.json'
    CONTENT = 'application/json'

    def _endpoint(self):
        return '%s%s' % (self._url, self.RESOURCE)

    def create(self, subject, body, uploads, name, email, fields):
        ticket = {}
        ticket['subject'] = subject
        ticket['comment'] = {}
        ticket['comment']['body'] = body
        if uploads:
            ticket['comment']['uploads'] = uploads
        if name and email:
            ticket['requester'] = {}
            ticket['requester']['name'] = name
            ticket['requester']['email'] = email
        if fields:
            ticket['custom_fields'] = fields
        data = json.dumps({'ticket': ticket})
        self._request('POST', self._endpoint(), data, self.CONTENT)


class Attachment(Request):

    RESOURCE = '/api/v2/uploads.json'

    def _endpoint(self, filename):
        endpoint = '%s%s?filename=%s' % (self._url, self.RESOURCE, filename)
        return endpoint

    def create(self, path, filename, content):
        with open(path, 'rb') as source:
            data = source.read()
        self._request('POST', self._endpoint(filename), data, content)

    def token(self):
        if self._data is None:
            return None
        return json.loads(self._data)['upload']['token']
