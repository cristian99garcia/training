# -*- coding: utf-8 -*-
# Copyright (c) 2013,14 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import os
from gettext import gettext as _

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.datastore import datastore
from sugar3.graphics.alert import NotifyAlert

import logging
_logger = logging.getLogger('training-activity-tasks')

from activity import (NAME_UID, EMAIL_UID, SCHOOL_UID, ROLE_UID, SCHOOL_NAME,
                      POST_CODE)
from graphics import Graphics, FONT_SIZES
import utils
from reporter import Reporter

# These tasks are requirements for other tasks
_ENTER_NAME_TASK = 'enter-name-task'
_ENTER_EMAIL_TASK = 'enter-email-task'
_VALIDATE_EMAIL_TASK = 'validate-email-task'
_WELCOME_BADGE_TASK = 'welcome-badge-task'
_TOOLBAR_BADGE_TASK = 'toolbar-badge-task'
_ENTER_SCHOOL_TASK = 'enter-school-task'
_ENTER_ROLE_TASK = 'enter-role-task'
CONNECTED_BADGE_TASK = 'connected-badge-task'
_RECORD_SAVE_TASK = 'record-save-task'
_WRITE_SAVE_TASK = 'write-save-task'
_ACTIVITIES_BADGE_TASK = 'activity-badge-task'
_PORTFOLIO_TASK = 'portfolio-task'
_JOURNAL_BADGE_TASK = 'journal-badge-task'
_FAVORITES_TASK = 'adding-favorites-task'
_VIEWS_BADGE_TASK = 'view-badge-task'
_FRAME_BADGE_TASK = 'frame-badge-task'
_SETTINGS_BADGE_TASK = 'settings-badge-task'
_TURTLE_SQUARE_TASK = 'turtle-square-task'
_TURTLE_SHOW_TASK = 'turtle-show-task'
_PHYSICS_PLAY_TASK = 'physics-play-task'
_PHYSICS_COLLABORATION_TASK = 'physics-collaboration-task'
_XO_TABLET_TASK = 'xo-tablet-task'
_XO_BADGE_TASK = 'xo-badge-task'
_ASSESSMENT_DOCUMENT_TASK = 'assessment-document-task'
_ASSESSMENT_BADGE_TASK = 'assessment-badge-task'
GET_CONNECTED_TASK = 'get-connected-task'

# _ASSESSMENT_MIME_TYPE = 'application/vnd.oasis.opendocument.text'
# _ASSESSMENT_SUFFIX = '.odt'
# _ASSESSMENT_MIME_TYPE = 'application/msword'
# _ASSESSMENT_SUFFIX = '.doc'
_ASSESSMENT_MIME_TYPE = 'application/vnd.ms-excel'
_ASSESSMENT_SUFFIX = '.xls'

_ROLES = {
    'Teacher': [_('Teacher'), True],
    'Principal': [_('Principal'), True],
    'ICT Coordinator': [_('ICT Coordinator'), True],
    'Assistant Teacher': [_('Assistant Teacher'), True],
    'Assistant Principal': [_('Assistant Principal'), True],
    'Volunteer': [_('Volunteer'), False],
    'Parent': [_('Parent'), False],
    'Community': [_('Community'), False],
    'School Administrator': [_('School Administrator'), True],
    'Curriculum Coach': [_('Curriculum Coach'), True],
    'Pre Service Teachers': [_('Pre-service Teacher'), True]}


def get_tasks(task_master):
    task_list = [
        {'name': _('Welcome to Sugar Labs Academy'),
         'icon': 'badge-intro',
         'tasks': [Welcome1Task(task_master),
                   Welcome2Task(task_master),
                   Welcome3Task(task_master),
                   Welcome4Task(task_master),
                   Welcome5Task(task_master),
                   Welcome6Task(task_master),
                   Welcome7Task(task_master, 0)]},
        {'name': _('Getting to Know the Toolbar'),
         'icon': 'badge-toolbar',
         'tasks': [Toolbar1Task(task_master),
                   Toolbar2Task(task_master),
                   Toolbar3Task(task_master),
                   Toolbar4Task(task_master),
                   Toolbar5Task(task_master),
                   Toolbar6Task(task_master),
                   Toolbar7Task(task_master),
                   Toolbar8Task(task_master),
                   Toolbar9Task(task_master, 1)]},
        {'name': _('Getting to Know the Frame'),
         'icon': 'badge-frame',
         'tasks': [Frame1Task(task_master),
                   Frame2Task(task_master),
                   Frame3Task(task_master),
                   Frame4Task(task_master),
                   Frame5Task(task_master),
                   Frame6Task(task_master),
                   Frame7Task(task_master),
                   Frame8Task(task_master, 2)]},
        {'name': _('Getting to Know the Views'),
         'icon': 'badge-views',
         'tasks': [Views1Task(task_master),
                   Views2Task(task_master),
                   Views3Task(task_master),
                   Views4Task(task_master),
                   Views5Task(task_master),
                   Views6Task(task_master),
                   Views7Task(task_master),
                   Views8Task(task_master, 3)]},
        {'name': _('Getting Connected'),
         'icon': 'badge-connected',
         'tasks': [Connected1Task(task_master),
                   Connected2Task(task_master),
                   Connected3Task(task_master),
                   Connected4Task(task_master),
                   # Connected5Task(task_master),
                   Connected6Task(task_master),
                   Connected7Task(task_master),
                   Connected8Task(task_master),
                   Connected9Task(task_master),
                   Connected10Task(task_master, 4)]},
        {'name': _('Getting to Know Sugar Activities'),
         'icon': 'badge-activities',
         'tasks': [Activities1Task(task_master),
                   Activities2Task(task_master),
                   Activities3Task(task_master),
                   Activities4Task(task_master),
                   Activities5Task(task_master),
                   Activities6Task(task_master),
                   Activities7Task(task_master),
                   Activities8Task(task_master),
                   Activities9Task(task_master, 5)]},
        {'name': _('Getting to Know the Journal'),
         'icon': 'badge-journal',
         'tasks': [Journal1Task(task_master),
                   Journal2Task(task_master),
                   Journal3Task(task_master),
                   Journal4Task(task_master),
                   Journal5Task(task_master),
                   Journal6Task(task_master),
                   Journal7Task(task_master),
                   Journal8Task(task_master, 6)]},
        {'name': _('Getting to Know Settings'),
         'icon': 'badge-settings',
         'tasks': [Settings1Task(task_master),
                   Settings2Task(task_master),
                   Settings3Task(task_master),
                   Settings4Task(task_master),
                   Settings5Task(task_master)]},
    ]

    if utils.is_XO():
        task_list[-1]['tasks'].append(Settings6Task(task_master, 7))
        task_list.append(
            {'name': _('Learning More About the XO'),
             'icon': 'badge-xo',
             'tasks': [XO1Task(task_master),
                       XO2Task(task_master),
                       XO3Task(task_master),
                       XO4Task(task_master),
                       XO5Task(task_master),
                       XO6Task(task_master),
                       XO7Task(task_master),
                       XO8Task(task_master, 8)]},
        )
        section_counter = 9
    else:
        task_list[-1]['tasks'].append(Settings7Task(task_master, 7))
        section_counter = 8

    task_list.append(
        {'name': _('Getting to Know more Activities'),
         'icon': 'badge-more-activities',
         'tasks': [MoreActivities1Task(task_master),
                   Turtle1Task(task_master),
                   Turtle2Task(task_master),
                   Turtle3Task(task_master),
                   Turtle4Task(task_master),
                   Turtle5Task(task_master),
                   Turtle6Task(task_master),
                   Turtle7Task(task_master),
                   Turtle8Task(task_master),
                   Turtle9Task(task_master),
                   Turtle10Task(task_master),
                   Turtle11Task(task_master),
                   MoreActivities2Task(task_master, section_counter)]})
    task_list.append(
        {'name': _('Getting to Know Collaboration'),
         'icon': 'badge-collaboration',
         'tasks': [Collaboration1Task(task_master),
                   Collaboration2Task(task_master),
                   Physics1Task(task_master),
                   Physics2Task(task_master),
                   Collaboration3Task(task_master),
                   Collaboration4Task(task_master),
                   Collaboration5Task(task_master),
                   Collaboration6Task(task_master),
                   Collaboration7Task(task_master),
                   Collaboration8Task(task_master, section_counter + 1)]})
    task_list.append(
        {'name': _('Assessment'),
         'icon': 'badge',
         'tasks': [Assessment1Task(task_master),
                   Assessment2Task(task_master),
                   Assessment3Task(task_master, section_counter + 2)]})

    return task_list


class Task():
    ''' Generate class for defining tasks '''

    def __init__(self, task_master):
        self._name = 'Generic Task'
        self.uid = None
        self._task_master = task_master
        self._font_size = 5
        self._zoom_level = 1.0
        self._pause_between_checks = 1000
        self._requires = []
        self._prompt = _('Next')

    def get_yes_no_tasks(self):
        return None, None

    def set_font_size(self, size):
        if size < len(FONT_SIZES):
            self._font_size = size

    def get_font_size(self):
        return self._font_size

    font_size = GObject.property(type=object, setter=set_font_size,
                                 getter=get_font_size)

    def set_zoom_level(self, level):
        self._zoom_level = level

    def get_zoom_level(self):
        return self._zoom_level

    zoom_level = GObject.property(type=object, setter=set_zoom_level,
                                  getter=get_zoom_level)

    def test(self, task_data):
        ''' The test to determine if task is completed '''
        raise NotImplementedError

    def grab_focus(self):
        return

    def after_button_press(self):
        ''' Anything special to do after the task is completed? '''
        return True

    def get_success(self):
        ''' String to present to the user when task is completed '''
        return _('Success!')

    def get_retry(self):
        ''' String to present to the user when task is not completed '''
        return _('Keep trying')

    def get_refresh(self):
        ''' Does the task need a refresh button for its graphics? '''
        return False

    def get_my_turn(self):
        ''' Does the task need a my turn button to goto home view? '''
        return False

    def get_skip(self):
        ''' Does the task need a skip button to goto the next section? '''
        return False

    def get_data(self):
        ''' Any data needed for the test '''
        return None

    def skip_if_completed(self):
        ''' Should we skip this task if it is already complete? '''
        return False

    def get_pause_time(self):
        ''' How long should we pause between testing? '''
        return self._pause_between_checks

    def set_requires(self, requires):
        self._requires = requires[:]

    def get_requires(self):
        ''' Return list of tasks (uids) required prior to completing this
            task '''
        return []

    requires = GObject.property(type=object, setter=set_requires,
                                getter=get_requires)

    def is_collectable(self):
        ''' Should this task's data be collected? '''
        return False

    def get_name(self):
        ''' String to present to the user to define the task '''
        return self._name

    def get_help_info(self):
        ''' Is there help associated with this task? '''
        return (None, None)  # title, url (from Help.activity)

    def get_graphics(self):
        ''' Graphics to present with the task '''
        self._task_master.activity.set_copy_widget()
        self._task_master.activity.set_paste_widget()
        return None, _('Next')

    def is_completed(self):
        ''' Has this task been marked as complete? '''
        data = self._task_master.read_task_data(self.uid)
        if data is not None and 'completed' in data:
            return data['completed']
        return False

    def _get_user_name(self):
        ''' Get user's name. '''
        name = self._task_master.read_task_data(NAME_UID)
        if name is not None:
            return name
        else:
            return ''


class HTMLTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._uri = 'introduction1.html'
        self._height = 610

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class BadgeTask(HTMLTask):

    def __init__(self, task_master, section_index):
        HTMLTask.__init__(self, task_master)
        self._name = _('Badge Task')
        self.uid = 'badge-task'
        self._section_index = section_index
        self._uri = 'Welcome/welcome7.html'

    def _report_progress(self):
        _logger.debug('reporting...')
        reporter = Reporter(self._task_master.activity)
        reporter.report([self._task_master.read_task_data()])

    def after_button_press(self):
        self._task_master.activity.mark_section_as_complete(
            self._section_index)

        task_data = self._task_master.read_task_data(self.uid)
        if not 'badge' in task_data:
            task_data['badge'] = True
            self._task_master.activity.add_badge(
                self._name,
                icon=self._task_master.get_section_icon(self._section_index))
            self._task_master.write_task_data(self.uid, task_data)

        GObject.idle_add(self._report_progress)
        return True

    def test(self, task_data):
        return self._task_master.button_was_pressed


class Welcome1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Welcome')
        self.uid = 'welcome-1-task'
        self._uri = 'Welcome/welcome1.html'
        self._prompt = _("Let's go!")


class Welcome2Task(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Enter Your Name')
        self.uid = _ENTER_NAME_TASK
        self._uri = 'Welcome/welcome2.html'
        self._first_entry = None
        self._last_entry = None
        self._height = 400
        self._task_data = None

    def is_collectable(self):
        return True

    def _first_enter_entered(self, widget):
        # Switch focus to last entry
        if len(self._first_entry.get_text()) > 1:
            self.grab_focus()

    def _last_enter_entered(self, widget):
        if len(self._first_entry.get_text()) > 1 and \
           len(self._last_entry.get_text()) > 1:
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        self._task_data = task_data
        return len(self._first_entry.get_text()) > 1 and \
            len(self._last_entry.get_text()) > 1

    def after_button_press(self):
        name = '%s,%s' % (self._first_entry.get_text(),
                          self._last_entry.get_text())
        self._task_master.write_task_data(NAME_UID, name)
        self._task_master.activity.update_activity_title()
        return True

    def get_graphics(self):
        target = self._get_user_name()
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        if target is not None and len(target) > 0:
            first, last = target.split(',')
        else:
            first = ''
            last = ''
        self._first_entry, self._last_entry = graphics.add_two_entries(
            _('First name(s):'), first, _('Last name(s):'), last)

        self._first_entry.connect('activate', self._first_enter_entered)
        self._last_entry.connect('activate', self._last_enter_entered)

        return graphics, self._prompt

    def grab_focus(self):
        self._first_entry.set_can_focus(True)
        self._last_entry.set_can_focus(True)
        if len(self._first_entry.get_text()) == 0:
            self._first_entry.grab_focus()
            self._task_master.activity.set_copy_widget(
                text_entry=self._last_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._first_entry)
        else:
            self._last_entry.grab_focus()
            self._task_master.activity.set_copy_widget(
                text_entry=self._first_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._last_entry)


class Welcome3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Greetings')
        self.uid = 'welcome-3-task'
        self._uri = 'Welcome/welcome3.html'

    def get_graphics(self):
        name = self._get_user_name().split(',')[0]
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' %
                           (self._uri, utils.get_safe_text(name)))
        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Welcome4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Your Email')
        self.uid = _ENTER_EMAIL_TASK
        self._uri = 'Welcome/welcome4.html'
        self._entry = None
        self._height = 400
        self._task_data = None

    def get_requires(self):
        return [_ENTER_NAME_TASK]

    def skip_if_completed(self):
        return True

    def _enter_entered(self, widget):
        if self._is_valid_email_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_email_entry()

    def _is_valid_email_entry(self):
        entry = self._entry.get_text()
        return utils.is_valid_email_entry(entry)

    def after_button_press(self):
        _logger.debug('Writing email address: %s' % self._entry.get_text())
        self._task_master.write_task_data(EMAIL_UID, self._entry.get_text())
        return True

    def get_graphics(self):
        email_address = self._task_master.read_task_data(EMAIL_UID)
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        if email_address is not None:
            self._entry = graphics.add_entry(text=email_address)
        else:
            self._entry = graphics.add_entry()

        self._entry.connect('activate', self._enter_entered)
        self._task_master.activity.set_copy_widget(text_entry=self._entry)
        self._task_master.activity.set_paste_widget(text_entry=self._entry)

        return graphics, self._prompt

    def grab_focus(self):
        self._entry.set_can_focus(True)
        self._entry.grab_focus()


class Welcome5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Validate Email')
        self.uid = _VALIDATE_EMAIL_TASK
        self._uri = 'Welcome/welcome5.html'
        self._entries = []
        self._task_data = None

    def is_collectable(self):
        return True

    def skip_if_completed(self):
        return True

    def get_requires(self):
        return [_ENTER_EMAIL_TASK]

    def _enter_entered(self, widget):
        if self._is_valid_email_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_email_entry()

    def _is_valid_email_entry(self):
        entry0 = self._entries[0].get_text()
        entry1 = self._entries[1].get_text()
        if len(entry0) == 0 or len(entry1) == 0:
            return False
        if entry0.lower() != entry1.lower():
            return False
        return utils.is_valid_email_entry(entry0)

    def after_button_press(self):
        self._task_master.write_task_data(EMAIL_UID,
                                          self._entries[1].get_text())
        return True

    def get_graphics(self):
        self._entries = []
        email_address = self._task_master.read_task_data(EMAIL_UID)
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        if email_address is None:
            # This should not happen except if data file is corrupted
            self._entries.append(graphics.add_entry(text=''))
            _logger.error('email was missing in Task %s' % self.uid)
        else:
            self._entries.append(graphics.add_entry(text=email_address))
        graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)
        if email_address is None:  # Should never happen
            email_address = ''
        self._entries.append(graphics.add_entry())

        self._entries[0].connect('activate', self._enter_entered)
        self._entries[1].connect('activate', self._enter_entered)
        # Paste to second entry
        self._task_master.activity.set_copy_widget(text_entry=self._entries[0])
        self._task_master.activity.set_paste_widget(
            text_entry=self._entries[-1])

        return graphics, self._prompt

    def grab_focus(self):
        self._entries[-1].set_can_focus(True)
        self._entries[-1].grab_focus()


class Welcome6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Chapters')
        self.uid = 'check-progress-task'
        self._uri = 'Welcome/welcome6.html'
        self._goals = []

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if len(self._goals) == 0:
            if utils.is_expanded(
                    self._task_master.activity.progress_toolbar_button):
                self._goals.append(True)
        else:
            return not utils.is_expanded(
                self._task_master.activity.progress_toolbar_button)
        # return self._task_master.progress_checked


class Welcome7Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Welcome Badge')
        self.uid = _WELCOME_BADGE_TASK
        self._uri = 'Welcome/welcome7.html'

    def get_graphics(self):
        name = self._get_user_name().split(',')[0]
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' %
                           (self._uri, utils.get_safe_text(name)))
        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Toolbar1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introduction to the Toolbar')
        self.uid = 'toolbar-1-task'
        self._uri = 'Toolbar/toolbar1.html'


class Toolbar2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Stopping an Activity')
        self.uid = 'toolbar-2-task'
        self._uri = 'Toolbar/toolbar2.html'


class Toolbar3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Stopping an Activity (Video)')
        self.uid = 'toolbar-3-task'
        self._uri = 'Toolbar/toolbar3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = \
                utils.get_launch_count(self._task_master.activity)
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            _logger.debug(utils.get_launch_count(self._task_master.activity))
            launch_count = utils.get_launch_count(self._task_master.activity)
            if launch_count > task_data['data']:
                return True
            else:
                # FIX ME: If the user switches to a new instance, the
                # the launch count is no longer valid. Reseting it here,
                # but this may require an extra cycle of stop and start.
                task_data['data'] = launch_count


class Toolbar4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('More re Toolbars')
        self.uid = 'toolbar-4-task'
        self._uri = 'Toolbar/toolbar4.html'


class Toolbar5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Using the View Menu')
        self.uid = 'toolbar-5-task'
        self._uri = 'Toolbar/toolbar5.html'


class Toolbar6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Trying Full Screen')
        self.uid = 'toolbar-6-task'
        self._uri = 'Toolbar/toolbar6.html'
        self._goals = []

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if len(self._goals) == 0:
            if utils.is_expanded(
                    self._task_master.activity.view_toolbar_button):
                self._goals.append(True)
        elif len(self._goals) == 1:
            if utils.is_fullscreen(self._task_master.activity):
                self._goals.append(True)
        elif len(self._goals) == 2:
            if not utils.is_fullscreen(self._task_master.activity):
                self._goals.append(True)
        else:
            return not utils.is_expanded(
                self._task_master.activity.view_toolbar_button)


class Toolbar7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Activity Toolbar')
        self.uid = 'toolbar-7-task'
        self._uri = 'Toolbar/toolbar7.html'


class Toolbar8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter a Description')
        self.uid = 'toolbar-8-task'
        self._uri = 'Toolbar/toolbar8.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        return len(utils.get_description(self._task_master.activity)) > 0


class Toolbar9Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Toolbar Badge')
        self.uid = _TOOLBAR_BADGE_TASK
        self._uri = 'Toolbar/toolbar9.html'


class Connected1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting Connected')
        self.uid = 'connected-1-task'
        self._uri = 'Connected/connected1.html'


class Connected2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Network View')
        self.uid = 'connected-2-task'
        self._uri = 'Connected/connected2.html'


class Connected3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Connecting to a WiFi Network')
        self.uid = 'connected-3-task'
        self._uri = 'Connected/connected3.html'


class Connected4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Connecting to a WiFi Network (Video)')
        self.uid = GET_CONNECTED_TASK
        self._uri = 'Connected/connected4.html'

    def get_skip(self):
        return True

    def get_refresh(self):
        return True

    def after_button_press(self):
        self._task_master.activity.set_notify_transfer_status(True)
        return True

    def test(self, task_data):
        return True  # utils.nm_status() == 'network-wireless-connected'

    def is_collectable(self):
        return True


'''
class Connected5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _("You're online")
        self.uid = 'connected-5-task'
        self._uri = 'Connected/connected5.html'
        self._entries = []

    def skip_if_completed(self):
        return True

    def get_requires(self):
        return [_ENTER_NAME_TASK, _VALIDATE_EMAIL_TASK]

    def test(self, task_data):
        entry0 = self._entries[0].get_text()
        entry1 = self._entries[1].get_text()
        if len(entry0) == 0 or len(entry1) == 0:
            return False
        return utils.is_valid_email_entry(entry1)

    def after_button_press(self):
        self._task_master.write_task_data(EMAIL_UID,
                                          self._entries[1].get_text())
        return True

    def get_graphics(self):
        self._entries = []
        name = self._task_master.read_task_data(NAME_UID)
        if name is None:  # Should never happen
            name = ''
        email_address = self._task_master.read_task_data(EMAIL_UID)
        if email_address is None:  # Should never happen
            email_address = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s&EMAIL=%s' %
                           (self._uri,
                            utils.get_safe_text(name),
                            utils.get_safe_text(email_address)))

        graphics = Graphics()
        graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)
        self._entries.append(graphics.add_entry(text=name))
        self._entries.append(graphics.add_entry(text=email_address))
        # Copy/Paste to second entry
        self._task_master.activity.set_copy_widget(text_entry=self._entries[1])
        self._task_master.activity.set_paste_widget(
            text_entry=self._entries[1])

        return graphics, self._prompt
'''


class Connected6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter School Name')
        self.uid = _ENTER_SCHOOL_TASK
        self._uri = ['Connected/connected6a.html',
                     'Connected/connected6b.html']
        self._height = 60
        self._graphics = None
        self._school_entry = None
        self._postal_code_entry = None
        self._postal_code_changed = True
        self._postal_code = -1
        self._buttons = []
        self._schools = []
        self._sf_ids = []
        self._results = []
        self._default_sf_id = '0019000000pETbT'
        self._completer = None
        self._task_data = None

    def is_collectable(self):
        return True

    def _postal_code_enter_entered(self, widget):
        # Force new list
        self._postal_code_changed = True
        if self._is_valid_postal_code_entry():
            self._school_entry.grab_focus()
            self._is_valid_school_entry()

    def _postal_code_entry_cb(self, widget, event):
        if self._is_valid_postal_code_entry():
            self._is_valid_school_entry()

    def _is_valid_postal_code_entry(self, target=None):
        if target is None:
            target = self._postal_code_entry.get_text()
        if len(target) < 3:
            return False
        try:
            i = int(target)
        except:
            return False
        if i >= 0 and i < 9999:
            # if self._postal_code != i or self._postal_code_changed:
            self._postal_code_changed = True
            self._postal_code = i
            self._task_master.write_task_data(POST_CODE, target)
            # else:
            #     self._postal_code_changed = False
            return True
        else:
            return False

    def _school_enter_entered(self, widget):
        if self._is_valid_school_entry():
            self._task_master.enter_entered(self._task_data, self.uid)

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return self._is_valid_school_entry()

    def _is_valid_school_entry(self):
        # build a completer for this postal code
        if self._postal_code < 0:
            return False

        if self._postal_code_changed:
            # get rid of any old buttons
            for button in self._buttons:
                button.destroy()

            f = open(os.path.join(self._task_master.activity.bundle_path,
                                  'schools.txt'), 'r')
            schools = f.read().split('\n')
            f.close()
            self._schools = []
            self._sf_ids = []
            for school in schools:
                if len(school) == 0:
                    continue
                try:
                    sf_id, name, campus, address, city, state, postal_code = \
                        school.split(',')
                except:
                    _logger.debug('bad school data? (%s)' % school)
                # save the SF_ID from One Education in case we need it
                if name == 'One Education School':
                    self._default_sf_id = sf_id
                try:
                    if int(postal_code) != self._postal_code:
                        continue
                except:
                    _logger.error('bad postal code? (%s: %s)' %
                                  (name, postal_code))
                    continue
                if len(campus) > 0:
                    self._schools.append('%s %s, %s, %s' %
                                         (name, campus, city, state))
                else:
                    self._schools.append('%s, %s, %s' % (name, city, state))
                self._sf_ids.append(sf_id)
            # _logger.debug('%d schools in the list' %  (len(self._schools)))
            self._completer = utils.Completer(self._schools)
            if len(self._schools) < 10:
                self._make_buttons(self._schools)

        self._postal_code_changed = False
        if len(self._school_entry.get_text()) == 0:
            return False
        else:
            return True

    def _make_buttons(self, school_list):
        for button in self._buttons:
            button.destroy()
        self._buttons = []
        for i, school in enumerate(school_list):
            self._buttons.append(
                self._graphics.add_button(school, self._button_cb, arg=school))
            self._buttons[-1].show()

    def _button_cb(self, widget, text):
        self._school_entry.set_text(text)
        for button in self._buttons:
            button.destroy()

    def _school_entry_focus_cb(self, widget, event):
        if not self._is_valid_postal_code_entry():
            return
        elif len(widget.get_text()) == 0 and len(self._schools) > 0:
            self._make_buttons(self._schools)

    def _school_entry_release_cb(self, widget, event):
        if len(self._results) == 1:
            widget.set_text(self._results[0])
            for button in self._buttons:
                button.destroy()
        elif len(self._results) < 10:
            for button in self._buttons:
                button.destroy()
            self._make_buttons(self._results)

    def _school_entry_press_cb(self, widget, event):
        if not self._is_valid_postal_code_entry():
            return
        self._results = self._completer.complete(
            widget.get_text() + Gdk.keyval_name(event.keyval), 0)

    def _yes_no_cb(self, widget, arg):
        if arg == 'yes':
            self._task_master.write_task_data(SCHOOL_UID, None)
            school = self._school_entry.get_text()
            postal_code = self._postal_code_entry.get_text()
            self._task_data[SCHOOL_NAME] = school
            self._task_data[POST_CODE] = postal_code
            self._task_master.write_task_data(self.uid, self._task_data)
            self._task_master.write_task_data(SCHOOL_NAME, school)
            self._task_master.write_task_data(POST_CODE, postal_code)
            self._task_master.write_task_data(SCHOOL_UID, self._default_sf_id)
            _logger.debug('Wrote SCHOOL_UID AND SCHOOL_NAME to task_data file')
            self._task_master.current_task += 1
            self._task_master.write_task_data('current_task',
                                              self._task_master.current_task)
        self._task_master.task_master()

    def after_button_press(self):
        school = self._school_entry.get_text()
        if school in self._schools:
            i = self._schools.index(school)
            self._task_master.write_task_data(SCHOOL_UID, self._sf_ids[i])
            self._task_master.write_task_data(SCHOOL_NAME, school)
            _logger.debug('Wrote SCHOOL_UID AND SCHOOL_NAME to task_data file')
            return True
        else:
            # Confirm that it is OK to use a school not in the list.
            self._task_master.task_button.hide()
            self._graphics.add_text(_('Your school does not appear in our '
                                      'list of schools in Australia. '
                                      'OK to continue?'))
            self._graphics.add_yes_no_buttons(self._yes_no_cb)
            return False

    def get_graphics(self):
        self._graphics = Graphics()

        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri[0])
        self._graphics.add_uri('file://' + url, height=self._height)
        self._graphics.set_zoom_level(self._zoom_level)

        target = self._task_master.read_task_data(POST_CODE)
        if target is not None and \
           self._is_valid_postal_code_entry(target=target):
            self._postal_code_entry = self._graphics.add_entry(text=target)
        else:
            self._postal_code_entry = self._graphics.add_entry()

        self._postal_code_entry.connect('key-release-event',
                                        self._postal_code_entry_cb)
        self._postal_code_entry.connect('key-press-event',
                                        self._postal_code_entry_cb)
        self._postal_code_entry.connect('activate',
                                        self._postal_code_enter_entered)

        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri[1])
        self._graphics.add_uri('file://' + url, height=self._height)
        self._graphics.set_zoom_level(self._zoom_level)

        target = self._task_master.read_task_data(SCHOOL_NAME)
        if target is not None:
            self._school_entry = self._graphics.add_entry(text=target)
        else:
            self._school_entry = self._graphics.add_entry()

        self._school_entry.connect('key-release-event',
                                   self._school_entry_release_cb)
        self._school_entry.connect('key-press-event',
                                   self._school_entry_press_cb)
        self._school_entry.connect('focus-in-event',
                                   self._school_entry_focus_cb)
        self._school_entry.connect('activate', self._school_enter_entered)

        self._postal_code_entry.grab_focus()

        return self._graphics, self._prompt

    def grab_focus(self):
        self._postal_code_entry.set_can_focus(True)
        self._school_entry.set_can_focus(True)
        if len(self._postal_code_entry.get_text()) < 3:
            self._task_master.activity.set_copy_widget(
                text_entry=self._postal_code_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._postal_code_entry)
        else:
            self._task_master.activity.set_copy_widget(
                text_entry=self._school_entry)
            self._task_master.activity.set_paste_widget(
                text_entry=self._school_entry)


class Connected7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Enter Roll')
        self.uid = _ENTER_ROLE_TASK
        self._uri = 'Connected/connected7.html'
        self._height = 60
        self._graphics = None
        self._role = None
        self._buttons = None
        self._task_data = None

    def is_collectable(self):
        return True

    def after_button_press(self):
        self._task_master.write_task_data(ROLE_UID, self._role)
        return True

    def _role_button_callback(self, widget, roll):
        for button in self._buttons:
            button.set_sensitive(not button == widget)
        self._role = 'Other'
        for key in list(_ROLES.keys()):
            if _ROLES[key][0] == roll:
                self._role = key
                _logger.debug(self._role)
                break

    def test(self, task_data):
        if self._task_data is None:
            self._task_data = task_data
        return not self._role is None

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        roles = []
        for key in sorted(_ROLES.keys()):
            roles.append(_ROLES[key][0])
        roles.append(_('Other'))

        self._role = self._task_master.read_task_data(ROLE_UID)

        self._buttons = graphics.add_list_buttons(roles)
        for i, button in enumerate(self._buttons):
            button.connect('clicked', self._role_button_callback, roles[i])
            if self._role in list(_ROLES.keys()) and \
               _ROLES[self._role][0] == roles[i]:
                button.set_sensitive(False)
        if self._role == 'Other':
            self._buttons[-1].set_sensitive(False)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Connected8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Connected')
        self.uid = 'connected-8-task'
        self._uri = 'Connected/connected8.html'

    def get_requires(self):
        return [_ENTER_NAME_TASK, _VALIDATE_EMAIL_TASK, _ENTER_SCHOOL_TASK,
                _ENTER_ROLE_TASK]

    def get_graphics(self):
        self._entries = []
        name = self._task_master.read_task_data(NAME_UID)
        if name is None:  # Should never happen
            name = ''
        email_address = self._task_master.read_task_data(EMAIL_UID)
        if email_address is None:  # Should never happen
            email_address = ''
        school = self._task_master.read_task_data(SCHOOL_NAME)
        if school is None:  # Should never happen
            school = ''
        role = self._task_master.read_task_data(ROLE_UID)
        if role is None:  # Should never happen
            role = ''
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s&EMAIL=%s&SCHOOL=%s&ROLE=%s' %
                           (self._uri,
                            utils.get_safe_text(name),
                            utils.get_safe_text(email_address),
                            utils.get_safe_text(school),
                            utils.get_safe_text(role)))

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=400)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Connected9Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Notifications')
        self.uid = 'connected-9-task'
        self._uri = 'Connected/connected9.html'


class Connected10Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Connected Badge')
        self.uid = CONNECTED_BADGE_TASK
        self._uri = 'Connected/connected10.html'


class Activities1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know Sugar Activities')
        self.uid = 'activities-1-task'
        self._uri = 'Activities/activities1.html'


class Activities2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Take a Picture with Record')
        self.uid = 'activities-2-task'
        self._uri = 'Activities/activities2.html'


class Activities3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Take a Picture with Record (Video)')
        self.uid = _RECORD_SAVE_TASK
        self._uri = 'Activities/activities3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if not utils.saw_new_launch('org.laptop.RecordActivity',
                                    utils.recently(task_data['start_time'])):
            return False
        paths = utils.get_jpg()
        return len(paths) > 0 and (utils.get_modified_time(paths[0]) >
                                   utils.recently(task_data['start_time']))


class Activities4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Insert a Picture into a Write Document')
        self.uid = 'activities-4-task'
        self._uri = 'Activities/activities4.html'


class Activities5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Insert a Picture into a Write Document (Video)')
        self.uid = _WRITE_SAVE_TASK
        self._uri = 'Activities/activities5.html'

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _RECORD_SAVE_TASK]

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if not utils.saw_new_launch('org.laptop.AbiWordActivity',
                                    utils.recently(task_data['start_time'])):
            return False
        # We need the clipboard text for the Speak task
        # if not utils.is_clipboard_text_available():
        #     return False
        paths = utils.get_odt()
        for path in paths:
            # Check to see if there is a picture in the file:
            # look for '\\pict' in RTF, 'Pictures' in ODT
            if utils.find_string(path, 'Pictures'):
                return True
        return False


class Activities6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Make Speak Talk to You')
        self.uid = 'activities-6-task'
        self._uri = 'Activities/activities6.html'


class Activities7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Make Speak Talk to You (Video)')
        self.uid = 'speak-task'
        self._uri = 'Activities/activities7.html'

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _WRITE_SAVE_TASK]

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if not utils.saw_new_launch('vu.lux.olpc.Speak',
                                    utils.recently(task_data['start_time'])):
            return False
        # Has any setting changed?
        status = utils.get_speak_settings(
            utils.get_most_recent_instance('vu.lux.olpc.Speak'))
        if status is None:
            return False
        if len(status['eyes']) != 2 or \
           status['eyes'][0] != 1 or \
           status['pitch'] != 49 or \
           status['rate'] != 49 or \
           status['mouth'] != 1:
            return True
        return False


class Activities8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Start New')
        self.uid = 'activities-8-task'
        self._uri = 'Activities/activities8.html'


class Activities9Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Activities Badge')
        self.uid = _ACTIVITIES_BADGE_TASK
        self._uri = 'Activities/activities9.html'


class Journal1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know the Journal')
        self.uid = 'journal-1-task'
        self._uri = 'Journal/journal1.html'


class Journal2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Viewing the Journal')
        self.uid = 'journal-2-task'
        self._uri = 'Journal/journal2.html'


class Journal3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Viewing the Journal (Video)')
        self.uid = 'journal-3-task'
        self._uri = 'Journal/journal3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            activity = utils.get_most_recent_instance(
                'org.laptop.AbiWordActivity')
            if activity is not None and 'description' in activity.metadata:
                task_data['data'] = activity.metadata['description']
            else:
                task_data['data'] = ''
            return False
        else:
            # Make sure description has changed and entry is 'starred'
            activity = utils.get_most_recent_instance(
                'org.laptop.AbiWordActivity')
            if activity is None or not 'keep' in activity.metadata or \
               not 'description' in activity.metadata:
                return False
            return \
                not task_data['data'] == activity.metadata['description']
                # 'starred' is no longer part of task
                # and int(activity.metadata['keep']) == 1


class Journal4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introducing the Portfolio')
        self.uid = 'journal-4-task'
        self._uri = 'Journal/journal4.html'


class Journal5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Using the Portfolio (Video)')
        self.uid = _PORTFOLIO_TASK
        self._uri = 'Journal/journal5.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        # Make sure there are newly starred items and that the Portfolio
        # activity has been launched; then look for a PDF file.
        if task_data['data'] is None:
            task_data['data'] = utils.get_starred_count()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        # Portfolio will check for starred items, so no need to check here.
        # if not utils.get_starred_count() > task_data['data']:
        #     return False
        if not utils.saw_new_launch('org.sugarlabs.PortfolioActivity',
                                    utils.recently(task_data['start_time'])):
            return False
        paths = utils.get_pdf()
        if len(paths) == 0:
            return False
        for path in paths:
            if utils.get_modified_time(path) > \
               utils.recently(task_data['start_time']):
                return True
        return False


class Journal6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Copy your Presentation to USB')
        self.uid = 'journal-6-task'
        self._uri = 'Journal/journal6.html'

    def get_graphics(self):
        name = utils.get_safe_text('"%s %s"' % (utils.get_nick(),
                                                _('Portfolio')))
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' % (self._uri, name))

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Journal7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Copy your Presentation to USB (Video)')
        self.uid = 'journal-7-task'
        self._uri = 'Journal/journal7.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _PORTFOLIO_TASK]

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        paths = utils.look_for_file_type(
            self._task_master.activity.volume_data[0]['usb_path'], '.pdf')
        for path in paths:
            if utils.get_modified_time(path) > \
               utils.recently(task_data['start_time']):
                return True
        return False


class Journal8Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Journal Badge')
        self.uid = _JOURNAL_BADGE_TASK
        self._uri = 'Journal/journal8.html'


class Frame1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know the Frame')
        self.uid = 'frame-1-task'
        self._uri = 'Frame/frame1.html'


class Frame2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Three Ways to Open the Frame')
        self.uid = 'frame-2-task'
        self._uri = 'Frame/frame2.html'

    # FIX ME: We need some sort of test here


class Frame3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Checking the Battery')
        self.uid = 'frame-3-task'
        self._uri = 'Frame/frame3.html'
        self._battery_level = None
        self._height = 400

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if self._battery_level is None:
            return False
        level = utils.get_battery_level()
        if abs(level - self._battery_level) <= 10:
            return True
        else:
            return False

    def _battery_button_callback(self, widget, i):
        self._battery_level = i * 20

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        buttons = graphics.add_radio_buttons(['battery-000', 'battery-020',
                                              'battery-040', 'battery-060',
                                              'battery-080', 'battery-100'],
                                             colors=utils.get_colors())
        for i, button in enumerate(buttons):
            button.connect('clicked', self._battery_button_callback, i)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Frame4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Changing the Volume')
        self.uid = 'frame-4-task'
        self._uri = 'Frame/frame4.html'

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            task_data['data'] = utils.get_sound_level()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            return not utils.get_sound_level() == task_data['data']


class Frame5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Using the Frame to Read Text')
        self.uid = 'frame-5-task'
        self._uri = 'Frame/frame5.html'

    # FIX ME: We need some sort of test here


class Frame6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Bottom of the Frame Recap')
        self.uid = 'frame-6-task'
        self._uri = 'Frame/frame6.html'


class Frame7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Top of the Frame Recap')
        self.uid = 'frame-7-task'
        self._uri = 'Frame/frame7.html'


class Frame8Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Frame Badge')
        self.uid = _FRAME_BADGE_TASK
        self._uri = 'Frame/frame8.html'


class Views1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting to Know the Views')
        self.uid = 'views-1-task'
        self._uri = 'Views/views1.html'


class Views2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Four Views of Sugar')
        self.uid = 'views-2-task'
        self._uri = 'Views/views2.html'


class Views3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('The Views of Sugar (Video)')
        self.uid = 'views-3-task'
        self._uri = 'Views/views3.html'

    def get_refresh(self):
        return True


class Views4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Adding a Favourite to the Home View')
        self.uid = 'views-4-task'
        self._uri = 'Views/views4.html'


class Views5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Adding a Favourite to the Home View (Video)')
        self.uid = _FAVORITES_TASK
        self._uri = 'Views/views5.html'

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def get_refresh(self):
        return True

    def is_collectable(self):
        return True

    def get_my_turn(self):
        return True

    def get_data(self):
        favorites_list = utils.get_favorites()
        # logging.error('%s: get length of favorites list: %d' % 
        #               (self._name, len(favorites_list.keys())))
        return self._task_master.activity.favorites_count
        # return len(favorites_list.keys())

    def test(self, task_data):
        if not 'data' in task_data or task_data['data'] is None:
            favorites_list = utils.get_favorites()
            task_data['data'] = self._task_master.activity.favorities_count
            # task_data['data'] = len(favorites_list)
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            # logging.error('%s: %d > %d???' % 
            #               (self._name, len(utils.get_favorites().keys()),
            #                self._task_master.activity.favorites_count))
            # return len(utils.get_favorites().keys()) > task_data['data']
            return len(list(utils.get_favorites().keys())) > \
                   self._task_master.activity.favorites_count


class Views6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Removing a Favourite from the Home View')
        self.uid = 'removing-favorites-task'
        self._uri = 'Views/views6.html'

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _FAVORITES_TASK]

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def get_my_turn(self):
        return True

    def get_data(self):
        favorites_list = utils.get_favorites()
        # logging.error('%s: get length of favorites list: %d' % 
        #               (self._name, len(favorites_list)))
        return self._task_master.activity.favorites_count
        # return len(favorites_list)

    def test(self, task_data):
        if not 'data' in task_data or task_data['data'] is None:
            favorites_list = utils.get_favorites()
            task_data['data'] = self._task_master.activity.favorites_count
            # task_data['data'] = len(favorites_list.keys())
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            # logging.error('%s: %d < %d' % 
            #               (self._name, len(utils.get_favorites().keys()),
            #                self._task_master.activity.favorites_count))
            # return len(utils.get_favorites().keys()) < task_data['data']
            return len(list(utils.get_favorites().keys())) < \
                   self._task_master.activity.favorites_count

class Views7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch Between the Four Views')
        self.uid = 'views-7-task'
        self._uri = 'Views/views7.html'
        self._views = []

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if utils.is_activity_view():
            if 'activity' not in self._views:
                self._views.append('activity')
        elif utils.is_home_view():
            if 'home' not in self._views:
                self._views.append('home')
        elif utils.is_neighborhood_view():
            if 'neighborhood' not in self._views:
                self._views.append('neighborhood')
        return True  #len(self._views) > 2


class Views8Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Views Badge')
        self.uid = _VIEWS_BADGE_TASK
        self._uri = 'Views/views8.html'


class Settings1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Exploring the Sugar Settings')
        self.uid = 'settings-1-task'
        self._uri = 'Settings/settings1.html'


class Settings2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Changing the XO Nickname and Colours')
        self.uid = 'settings-2-task'
        self._uri = 'Settings/settings2.html'


class Settings3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Changing the XO Nickname and Colours (Video)')
        self.uid = 'settings-3-task'
        self._uri = 'Settings/settings3.html'

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def get_refresh(self):
        return True

    def get_my_turn(self):
        return True

    def test(self, task_data):
        if task_data['data'] is None:
            _logger.debug('saving nick value as %s' % utils.get_nick())
            self._task_master.write_task_data('nick', utils.get_nick())
            task_data['data'] = utils.get_nick()
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            if not utils.get_nick() == task_data['data']:
                task_data['new_nick'] = utils.get_nick()
                self._task_master.write_task_data(self.uid, task_data)
                return True
            else:
                return False


class Settings4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Important Settings')
        self.uid = 'settings-4-task'
        self._uri = 'Settings/settings4.html'


class Settings5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Other Settings')
        self.uid = 'settings-5-task'
        self._uri = 'Settings/settings5.html'

# We use either task 6 or task 7 depending on whether or not we are on an XO


class Settings6Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Badge Settings')
        self.uid = _SETTINGS_BADGE_TASK
        self._uri = 'Settings/settings6.html'


class Settings7Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Badge Settings')
        self.uid = _SETTINGS_BADGE_TASK
        self._uri = 'Settings/settings7.html'


class MoreActivities1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Learning About More Activities')
        self.uid = 'more-activities-1-task'
        self._uri = 'MoreActivities/moreactivities1.html'

    def get_skip(self):
        return True


class Turtle1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Blocks Introduction')
        self.uid = 'turtle-1-task'
        self._uri = 'MoreActivities/turtle1.html'


class Turtle2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Square')
        self.uid = 'turtle-2-task'
        self._uri = 'MoreActivities/turtle2.html'


class Turtle3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Square (Video)')
        self.uid = _TURTLE_SQUARE_TASK
        self._uri = 'MoreActivities/turtle3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def test(self, task_data):
        if not utils.saw_new_launch('org.laptop.TurtleArtActivity',
                                    utils.recently(task_data['start_time'])):
            return False
        activity = utils.get_most_recent_instance(
            'org.laptop.TurtleArtActivity')
        if activity is not None:
            path = activity.file_path
            if os.path.exists(path):
                if not utils.find_string(path, 'left') and \
                   not utils.find_string(path, 'right'):
                    return False
                if not utils.find_string(path, 'forward') and \
                   not utils.find_string(path, 'back'):
                    return False
                return True
        return False

    def get_my_turn(self):
        return True


class Turtle4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Square')
        self.uid = 'turtle-4-task'
        self._uri = 'MoreActivities/turtle4.html'


class Turtle5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Square (Video)')
        self.uid = 'turtle-5-task'
        self._uri = 'MoreActivities/turtle5.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _TURTLE_SQUARE_TASK]

    def test(self, task_data):
        if not utils.saw_new_launch('org.laptop.TurtleArtActivity',
                                    utils.recently(task_data['start_time'])):
            return False
        activity = utils.get_most_recent_instance(
            'org.laptop.TurtleArtActivity')
        if activity is not None:
            path = activity.file_path
            return utils.find_string(path, 'repeat')
        return False

    def get_my_turn(self):
        return True


class Turtle6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Pen')
        self.uid = 'turtle-6-task'
        self._uri = 'MoreActivities/turtle6.html'


class Turtle7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Pen')
        self.uid = 'turtle-pen-task'
        self._uri = 'MoreActivities/turtle7.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _TURTLE_SQUARE_TASK]

    def test(self, task_data):
        if not utils.saw_new_launch('org.laptop.TurtleArtActivity',
                                    utils.recently(task_data['start_time'])):
            return False
        activity = utils.get_most_recent_instance(
            'org.laptop.TurtleArtActivity')
        if activity is not None:
            path = activity.file_path
            if not utils.find_string(path, 'setpensize') and \
               not utils.find_string(path, 'setcolor'):
                return False
            return True
        return False

    def get_my_turn(self):
        return True


class Turtle8Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Show Text')
        self.uid = 'turtle-8-task'
        self._uri = 'MoreActivities/turtle8.html'


class Turtle9Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Show Text')
        self.uid = _TURTLE_SHOW_TASK
        self._uri = 'MoreActivities/turtle9.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _TURTLE_SQUARE_TASK]

    def test(self, task_data):
        activity = utils.get_most_recent_instance(
            'org.laptop.TurtleArtActivity')
        if activity is not None:
            path = activity.file_path
            if not utils.find_string(path, 'show'):
                return False
            return True
        return False

    def get_my_turn(self):
        return True


class Turtle10Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Show Image')
        self.uid = 'turtle-10-task'
        self._uri = 'MoreActivities/turtle10.html'


class Turtle11Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Turtle Show Image')
        self.uid = 'turtle-journal-task'
        self._uri = 'MoreActivities/turtle11.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _TURTLE_SHOW_TASK]

    def test(self, task_data):
        activity = utils.get_most_recent_instance(
            'org.laptop.TurtleArtActivity')
        if activity is not None:
            path = activity.file_path
            if not utils.find_string(path, 'journal'):
                return False
        return True

    def get_my_turn(self):
        return True


class Physics1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Physics Play')
        self.uid = 'physics-1-task'
        self._uri = 'MoreActivities/physics1.html'


class Physics2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Physics Play (Video)')
        self.uid = _PHYSICS_PLAY_TASK
        self._uri = 'MoreActivities/physics2.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def test(self, task_data):
        return utils.saw_new_launch('org.laptop.physics',
                                    utils.recently(task_data['start_time']))

    def get_my_turn(self):
        return True


class MoreActivities2Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('More Activities Badge')
        self.uid = 'more-activities-badge-task'
        self._uri = 'MoreActivities/moreactivities2.html'


class Collaboration1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Introduction to Collaboration')
        self.uid = 'collaboration-1-task'
        self._uri = 'Collaboration/collaboration1.html'

    def get_skip(self):
        return True


class Collaboration2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Getting Connected')
        self.uid = 'collaboration-2-task'
        self._uri = 'Collaboration/collaboration2.html'


class Collaboration3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Collaborating with Physics')
        self.uid = 'collaboration-3-task'
        self._uri = 'Collaboration/collaboration3.html'


class Collaboration4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Collaborating with Physics (Video)')
        self.uid = _PHYSICS_COLLABORATION_TASK
        self._uri = 'Collaboration/collaboration4.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _PHYSICS_PLAY_TASK]

    # def is_collectable(self):
    #     return True

    def test(self, task_data):
        for activity in utils.get_activity('org.laptop.physics'):
            if utils.get_share_scope(activity):
                return True
        return False

    def get_my_turn(self):
        return True


class Collaboration5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Collaboration')
        self.uid = 'collaboration-5-task'
        self._uri = 'Collaboration/collaboration5.html'


class Collaboration6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Collaboration')
        self.uid = 'collaboration-6-task'
        self._uri = 'Collaboration/collaboration6.html'

    def get_my_turn(self):
        return True

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _PHYSICS_COLLABORATION_TASK]


class Collaboration7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Collaboration')
        self.uid = 'collaboration-7-task'
        self._uri = 'Collaboration/collaboration7.html'


class Collaboration8Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Collaboration Badge')
        self.uid = 'collaboration-badge-task'
        self._uri = 'Collaboration/collaboration8.html'


'''
class ClipboardTask(Task):

    def __init__(self, task_master):
        Task.__init__(self, task_master)
        self._name = _('Copy to Clipboard')
        self.uid = 'copy-to-clipboard-task'
        self._uri = 'clipboard1.html'
        self._entries = []
        self._prompt = _('Next')
        self._height = 500

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        self._entries.append(graphics.add_entry())

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget(
            text_entry=self._entries[-1])

        return graphics, self._prompt

    def test(self, task_data):
        if not utils.is_clipboard_text_available():
            return False
        if len(self._entries[0].get_text()) > 0:
            return True
        return False
'''


class XO1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Learning More About the XO')
        self.uid = 'xo-1-task'
        self._uri = 'XO/xo1.html'


class XO2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch to Tablet Mode')
        self.uid = 'xo-2-task'
        self._uri = 'XO/xo2.html'


class XO3Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch to Tablet Mode (Video)')
        self.uid = _XO_TABLET_TASK
        self._uri = 'XO/xo3.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        return utils.is_tablet_mode()


class XO4Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Play with the Gamepad Keys')
        self.uid = 'xo-gamepad-task'
        self._uri = 'XO/xo4.html'
        self._height = 400
        self._boxes = None
        self._LEFT_OFF = os.path.join(self._task_master.get_bundle_path(),
                                      'html-content', 'images',
                                      'gamepad-left-off.svg')
        self._LEFT_UP = os.path.join(self._task_master.get_bundle_path(),
                                     'html-content', 'images',
                                     'gamepad-left-up.svg')
        self._LEFT_RIGHT = os.path.join(self._task_master.get_bundle_path(),
                                        'html-content', 'images',
                                        'gamepad-left-right.svg')
        self._LEFT_DOWN = os.path.join(self._task_master.get_bundle_path(),
                                       'html-content', 'images',
                                       'gamepad-left-down.svg')
        self._LEFT_LEFT = os.path.join(self._task_master.get_bundle_path(),
                                       'html-content', 'images',
                                       'gamepad-left-left.svg')
        self._RIGHT_OFF = os.path.join(self._task_master.get_bundle_path(),
                                       'html-content', 'images',
                                       'gamepad-right-off.svg')
        self._RIGHT_CHECK = os.path.join(self._task_master.get_bundle_path(),
                                         'html-content', 'images',
                                         'gamepad-right-check.svg')
        self._RIGHT_CIRCLE = os.path.join(self._task_master.get_bundle_path(),
                                          'html-content', 'images',
                                          'gamepad-right-circle.svg')
        self._RIGHT_SQUARE = os.path.join(self._task_master.get_bundle_path(),
                                          'html-content', 'images',
                                          'gamepad-right-square.svg')
        self._RIGHT_X = os.path.join(self._task_master.get_bundle_path(),
                                     'html-content', 'images',
                                     'gamepad-right-x.svg')

        self._LEFT_KEYMAP = {'KP_Up': self._LEFT_UP,
                             'KP_Down': self._LEFT_DOWN,
                             'KP_Left': self._LEFT_LEFT,
                             'KP_Right': self._LEFT_RIGHT}
        self._RIGHT_KEYMAP = {'KP_Page_Up': self._RIGHT_CIRCLE,
                              'KP_Page_Down': self._RIGHT_X,
                              'KP_Home': self._RIGHT_SQUARE,
                              'KP_End': self._RIGHT_CHECK}

    def is_collectable(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def test(self, task_data):
        self._task_master.grab_focus()

        if task_data['data'] is None:
            self._task_master.keyname = None
            task_data['data'] = ' '
            self._task_master.write_task_data(self.uid, task_data)
            return False
        else:
            if self._task_master.keyname is not None:
                _logger.debug(self._task_master.keyname)
            if utils.is_game_key(self._task_master.keyname):
                task_data['data'] = self._task_master.keyname
                self._task_master.write_task_data(self.uid, task_data)

                if self._task_master.keyname in self._LEFT_KEYMAP:
                    image = Gtk.Image.new_from_file(
                        self._LEFT_KEYMAP[self._task_master.keyname])
                else:
                    image = Gtk.Image.new_from_file(self._LEFT_OFF)
                self._boxes[0].get_children()[0].destroy()
                self._boxes[0].add(image)
                image.show()

                if self._task_master.keyname in self._RIGHT_KEYMAP:
                    image = Gtk.Image.new_from_file(
                        self._RIGHT_KEYMAP[self._task_master.keyname])
                else:
                    image = Gtk.Image.new_from_file(self._RIGHT_OFF)
                self._boxes[1].get_children()[0].destroy()
                self._boxes[1].add(image)
                image.show()

            if self._task_master.keyname == 'KP_End':
                return True
            else:
                return False

    def get_graphics(self):
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           self._uri)

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)
        self._boxes = graphics.add_two_images(self._LEFT_OFF, self._RIGHT_OFF)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt

    def grab_focus(self):
        self._task_master.set_can_focus(True)
        self._task_master.grab_focus()


class XO5Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch Back to Laptop Mode')
        self.uid = 'xo-5-task'
        self._uri = 'XO/xo5.html'


class XO6Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Switch Back to Laptop Mode (Video)')
        self.uid = 'xo-laptop-task'
        self._uri = 'XO/xo6.html'

    def get_refresh(self):
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _XO_TABLET_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        return not utils.is_tablet_mode()


class XO7Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Change the Screen Orientation')
        self.uid = 'xo-rotate-task'
        self._uri = 'XO/xo7.html'
        self._goals = []

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK]

    def is_collectable(self):
        return True

    def test(self, task_data):
        if len(self._goals) == 0:
            if not utils.is_landscape():
                self._goals.append(True)
            return False
        elif len(self._goals) == 1:
            if utils.is_landscape():
                self._goals.append(True)
            return False
        elif len(self._goals) == 2:
            if not utils.is_landscape():
                self._goals.append(True)
            return False
        else:
            return utils.is_landscape()


class XO8Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('XO Badge')
        self.uid = _XO_BADGE_TASK
        self._uri = 'XO/xo8.html'


class Assessment1Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Assessment')
        self.uid = 'assessment-1-task'
        self._uri = ['Assessment/assessment1.html',
                     'Assessment/assessment1a.html']
        self._result = None
        self._yes_no_required = True

    def get_requires(self):
        required = [_WELCOME_BADGE_TASK, CONNECTED_BADGE_TASK,
                    _TOOLBAR_BADGE_TASK, _ACTIVITIES_BADGE_TASK,
                    _JOURNAL_BADGE_TASK, _VIEWS_BADGE_TASK,
                    _FRAME_BADGE_TASK, _SETTINGS_BADGE_TASK]
        if utils.is_XO():
            required.append(_XO_BADGE_TASK)

        # If the connected section is not completed, just to it.
        if not self._task_master.uid_to_task(
                CONNECTED_BADGE_TASK, section=None).is_completed():
            alert = NotifyAlert()
            alert.props.title = _('Opening chapter: Getting Connected')
            alert.props.msg = _('You must complete the getting connected '
                                'tasks before you can finish Sugar Labs Academy.')
            alert.connect('response',
                          self._task_master.activity.remove_alert_cb)
            self._task_master.activity.add_alert(alert)
            return [CONNECTED_BADGE_TASK]
        else:
            return required

    def _remove_alert_cb(self, alert, response_id):
        self.remove_alert(alert)

    def get_yes_no_tasks(self):
        if self._yes_no_required:
            return _ASSESSMENT_DOCUMENT_TASK, _ASSESSMENT_BADGE_TASK
        else:
            return None, _ASSESSMENT_BADGE_TASK

    def test(self, task_data):
        return self._task_master.button_was_pressed

    def get_graphics(self):
        role = self._task_master.read_task_data(ROLE_UID)
        if role is not None:
            role = utils.get_safe_text(role)
        else:
            role = None

        for key in list(_ROLES.keys()):
            if key == role:
                role = _ROLES[key][0]
                self._yes_no_required = _ROLES[key][1]
                break
        if role is None:
            role = _('Other')
            self._yes_no_required = True

        _logger.debug('%s %s' % (role, str(self._yes_no_required)))

        if self._yes_no_required:
            url = os.path.join(self._task_master.get_bundle_path(),
                               'html-content',
                               '%s?NAME=%s' % (self._uri[0], role))
        else:
            url = os.path.join(self._task_master.get_bundle_path(),
                               'html-content', self._uri[1])

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Assessment2Task(HTMLTask):

    def __init__(self, task_master):
        HTMLTask.__init__(self, task_master)
        self._name = _('Assessment Document')
        self.uid = _ASSESSMENT_DOCUMENT_TASK
        self._uri = 'Assessment/assessment-yes.html'
        self.collectable = True

    def after_button_press(self):
        self._task_master.update_completion_percentage()
        _logger.debug('reporting...')
        reporter = Reporter(self._task_master.activity)
        reporter.report([self._task_master.read_task_data()])
        return True

    def get_requires(self):
        return [_VALIDATE_EMAIL_TASK, _ENTER_SCHOOL_TASK]

    def test(self, task_data):
        if not 'data' in task_data or task_data['data'] is None:
            task_data['data'] = '%s-%s%s' % (
                _('Assessment'),
                self._get_user_name().replace(',', '-'),
                _ASSESSMENT_SUFFIX)
            self._task_master.write_task_data(self.uid, task_data)

            # Create the assessment document in the Journal
            dsobject = datastore.create()
            if dsobject is not None:
                _logger.debug('creating Assessment entry in Journal')
                dsobject.metadata['title'] = task_data['data']
                dsobject.metadata['icon-color'] = \
                    utils.get_colors().to_string()
                dsobject.metadata['tags'] = \
                    self._task_master.activity.volume_data[0]['uid']
                dsobject.metadata['mime_type'] = _ASSESSMENT_MIME_TYPE
                dsobject.set_file_path(
                    os.path.join(self._task_master.activity.bundle_path,
                                 'Assessment' + _ASSESSMENT_SUFFIX))
                datastore.write(dsobject)
                dsobject.destroy()

            # Create the assessment instructions document in the Journal
            dsobject = datastore.create()
            if dsobject is not None:
                _logger.debug('creating Assessment entry in Journal')
                dsobject.metadata['title'] = _('Assessment-Instructions.pdf')
                dsobject.metadata['icon-color'] = \
                    utils.get_colors().to_string()
                dsobject.metadata['tags'] = \
                    self._task_master.activity.volume_data[0]['uid']
                dsobject.metadata['mime_type'] = 'application/pdf'
                dsobject.set_file_path(
                    os.path.join(self._task_master.activity.bundle_path,
                                 'Assessment-Instructions.pdf'))
                datastore.write(dsobject)
                dsobject.destroy()
            return False
        else:
            # Workaround to Sugar mimetype bug that causes file copied
            # to USB has .xlw extension...
            targets = utils.look_for_xlw(
                self._task_master.activity.volume_data[0]['usb_path'])
            for target in targets:
                utils.remove_xlw_suffix(target)
            # ...and read_only
            targets = utils.look_for_xls(
                self._task_master.activity.volume_data[0]['usb_path'])
            for target in targets:
                utils.set_read_write(target)

            # Look for the assessment document on the USB stick
            return os.path.exists(os.path.join(
                self._task_master.activity.volume_data[0]['usb_path'],
                task_data['data']))

    def get_graphics(self):
        name = utils.get_safe_text('"%s-%s%s" and "%s"' %
                                   (_('Assessment'),
                                    self._get_user_name().replace(',', '-'),
                                    _ASSESSMENT_SUFFIX,
                                    _('Assessment-Instructions.pdf')))
        url = os.path.join(self._task_master.get_bundle_path(), 'html-content',
                           '%s?NAME=%s' % (self._uri, name))

        graphics = Graphics()
        webkit = graphics.add_uri('file://' + url, height=self._height)
        graphics.set_zoom_level(self._zoom_level)

        self._task_master.activity.set_copy_widget(webkit=webkit)
        self._task_master.activity.set_paste_widget()

        return graphics, self._prompt


class Assessment3Task(BadgeTask):

    def __init__(self, task_master, section_index):
        BadgeTask.__init__(self, task_master, section_index)
        self._name = _('Assessment Badge')
        self.uid = _ASSESSMENT_BADGE_TASK
        self._uri = 'Assessment/assessment-no.html'
        self._prompt = _('Finish!')

    def is_collectable(self):
        return True

    def after_button_press(self):
        return True

    def test(self, task_data):
        # All done, so inform the user even before task is "collected"
        self._task_master.update_completion_percentage(finished=True)
        return True
