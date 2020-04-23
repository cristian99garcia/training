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
import logging


from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Soup

from activity import (TRAINING_DATA_UID, EMAIL_UID, NAME_UID,
                      SCHOOL_UID, COMPLETION_PERCENTAGE,
                      VERSION_NUMBER, ROLE_UID)


_logger = logging.getLogger('training-activity-reporter')


def _extract_trainee(data):
    trainee = []
    trainee.append(data.get(TRAINING_DATA_UID, None))
    trainee.append(data.get(EMAIL_UID, None))
    trainee.append(data.get(NAME_UID, None))
    trainee.append(data.get(SCHOOL_UID, None))
    trainee.append(data.get(COMPLETION_PERCENTAGE, None))
    trainee.append(data.get(VERSION_NUMBER, None))
    trainee.append(data.get(ROLE_UID, None))
    return trainee


def _extract_task(rawtask):
    task = []
    task.append(rawtask.get('task', None))
    task.append(rawtask.get('start_time', None))
    task.append(rawtask.get('end_time', None))
    task.append(rawtask.get('accumulated_time', None))
    return task


def _extract_tasks(data):
    tasks = []
    for uid in data:
        if 'task' in uid and isinstance(data[uid], dict) and \
                'completed' in data[uid] and data[uid]['completed']:
            tasks.append(_extract_task(data[uid]))
    return tasks


class Reporter(GObject.GObject):

    URL = '/training/url'
    API_KEY = 'training/api_key'
    TYPE = 'application/json'

    def __init__(self, activity):
        GObject.GObject.__init__(self)
        settings = Gio.Settings('org.sugarlabs.services') 
        self._url = settings.get_string(self.URL)
        self._api_key = settings.get_string(self.API_KEY)
        self._activity = activity

    def report(self, tasks_data_list):
        if not self._url or not self._api_key:
            _logger.error('reporter is missing URL or API-KEY')
            self._activity.transfer_failed_signal.emit()
            return

        transport_data = []
        for tasks_data in tasks_data_list:
            transport_data.append([_extract_trainee(tasks_data),
                                   _extract_tasks(tasks_data)])

        self._send(json.dumps(transport_data))

    def _send(self, data):
        uri = Soup.URI.new(self._url)

        message = Soup.Message(method='POST', uri=uri)
        message.request_headers.append('x-api-key', self._api_key)
        message.set_request(self.TYPE, Soup.MemoryUse.COPY, data, len(data))
        message.connect('network-event', self.__network_event_cb)
        message.connect('wrote-body-data', self.__wrote_body_data_cb)
        message.connect('finished', self.__finished_cb)

        session = Soup.SessionSync()
        session.add_feature_by_type(Soup.ProxyResolverDefault)
        session.send_message(message)

    def __network_event_cb(self, message, event, connection):
        if event == Gio.SocketClientEvent.CONNECTED:
            _logger.debug('reporter connected to server')
            self._activity.transfer_started_signal.emit()

    def __wrote_body_data_cb(self, message, chunk):
        _logger.debug('reporter is trasmitting')
        self._activity.transfer_progressed_signal.emit()

    def __finished_cb(self, message):
        code = message.status_code
        if code == 200:
            _logger.debug('reporter completed transmission')
            self._activity.transfer_completed_signal.emit()
        else:
            # error codes can be found at http://goo.gl/tWVJv2
            _logger.error('reporter failed transmitting, with code %d', code)
            self._activity.transfer_failed_signal.emit()
