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
import json
import time
from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from sugar3.graphics import style
from sugar3.graphics.toolbutton import ToolButton

import logging
_logger = logging.getLogger('training-activity-taskmaster')

import tasks
from progressbar import ProgressBar
import utils
from reporter import Reporter
from graphics import Graphics
from activity import (TRAINING_DATA_UID, NAME_UID, EMAIL_UID,
                      VERSION_NUMBER, COMPLETION_PERCENTAGE)


class TaskMaster(Gtk.Alignment):

    def __init__(self, activity):
        ''' Initialize the task list '''
        Gtk.Alignment.__init__(self)
        self.activity = activity

        self.set_size_request(Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)

        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path('style.css')
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.button_was_pressed = True
        self.current_task = None
        self.keyname = None
        self.task_button = None
        self.progress_checked = False

        self._name = None
        self._email = None
        self._graphics = None
        self._first_time = True
        self._accumulated_time = 0
        self._yes_task = None
        self._no_task = None
        self._task_list = tasks.get_tasks(self)
        self._task_data = None
        self._sugar_data_path = None
        self._resync_required = False
        self._uid = None
        self._start_time = time.time()
        self._accumulated_time = 0

        self._assign_required()

        self.current_task = self.read_task_data('current_task')
        if self.current_task is None:
            self.current_task = 0

        self._graphics_grid = Gtk.Grid()
        self._graphics_grid.set_row_spacing(style.DEFAULT_SPACING)
        self._graphics_grid.set_column_spacing(style.DEFAULT_SPACING)

        self.set(xalign=0.5, yalign=0, xscale=0, yscale=0)
        self.add(self._graphics_grid)
        self._graphics_grid.show()

        self.activity.load_graphics_area(self)

        self._task_button_alignment = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        self._task_button_alignment.set_size_request(
            Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)

        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_column_homogeneous(True)

        self._refresh_button = Gtk.Button(_('Refresh'), name='refresh-button')
        self._refresh_button.connect('clicked', self._refresh_button_cb)
        left = Gtk.Alignment.new(xalign=0, yalign=0.5, xscale=0, yscale=0)
        left.add(self._refresh_button)
        self._refresh_button.hide()
        grid.attach(left, 0, 0, 1, 1)
        left.show()

        mid = Gtk.Alignment.new(xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        yes_next_no_grid = Gtk.Grid()
        yes_next_no_grid.set_row_spacing(style.DEFAULT_SPACING)
        yes_next_no_grid.set_column_spacing(style.DEFAULT_SPACING)
        yes_next_no_grid.set_column_homogeneous(True)

        self._yes_button = Gtk.Button(_('Yes'), name='next-button')
        self._yes_button.connect('clicked', self._jump_to_task_cb, 'yes')
        yes_next_no_grid.attach(self._yes_button, 0, 0, 1, 1)
        self._yes_button.hide()

        self.task_button = Gtk.Button(_('Next'), name='next-button')
        self.task_button.connect('clicked', self._task_button_cb)
        yes_next_no_grid.attach(self.task_button, 1, 0, 1, 1)
        self.task_button.show()

        self._no_button = Gtk.Button(_('No'), name='next-button')
        self._no_button.connect('clicked', self._jump_to_task_cb, 'no')
        yes_next_no_grid.attach(self._no_button, 2, 0, 1, 1)
        self._no_button.hide()

        mid.add(yes_next_no_grid)
        yes_next_no_grid.show()
        grid.attach(mid, 1, 0, 1, 1)
        mid.show()

        right_grid = Gtk.Grid()

        self._my_turn_button = Gtk.Button(_('My Turn'), name='my-turn-button')
        self._my_turn_button.connect('clicked', self._my_turn_button_cb)
        right_grid.attach(self._my_turn_button, 0, 0, 1, 1)
        self._my_turn_button.hide()

        self._skip_button = Gtk.Button(_('Skip this section'),
                                       name='my-turn-button')
        self._skip_button.connect('clicked', self._skip_button_cb)
        right_grid.attach(self._skip_button, 1, 0, 1, 1)
        self._skip_button.hide()

        right = Gtk.Alignment.new(xalign=1.0, yalign=0.5, xscale=0, yscale=0)
        right.add(right_grid)
        right_grid.show()
        grid.attach(right, 2, 0, 1, 1)
        right.show()

        self._task_button_alignment.add(grid)
        grid.show()

        self.activity.load_button_area(self._task_button_alignment)
        self._task_button_alignment.show()

        self._progress_bar = None
        self._progress_bar_alignment = Gtk.Alignment.new(
            xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        self._progress_bar_alignment.set_size_request(
            Gdk.Screen.width() - style.GRID_CELL_SIZE, -1)

        self.activity.load_progress_area(self._progress_bar_alignment)
        self._progress_bar_alignment.show()

    def keypress_cb(self, widget, event):
        self.keyname = Gdk.keyval_name(event.keyval)

    def task_master(self):
        ''' 'nough said. '''

        # Recheck USB status each time
        if not self.activity.check_volume_data():
            _logger.error('Check volume data failed')
            # return

        self._destroy_graphics()
        self.activity.button_was_pressed = False
        if self.current_task < self._get_number_of_tasks():
            section_index, task_index = self.get_section_and_task_index()

            # Do we skip this task?
            task = self._task_list[section_index]['tasks'][task_index]
            while(task.is_completed() and task.skip_if_completed()):
                _logger.debug('Skipping task %d' % task_index)
                self.current_task += 1
                if self.current_task == self._get_number_of_tasks():
                    self.current_task = 0
                section_index, task_index = self.get_section_and_task_index()
                task = self._task_list[section_index]['tasks'][task_index]

            # Check to make sure all the requirements at met
            i = 0
            while not self.requirements_are_met(section_index, task_index):
                _logger.debug('Switching to a required task %d' %
                              self.current_task)
                section_index, task_index = self.get_section_and_task_index()
                i += 1
                if i > 10:
                    # Shouldn't happen but we want to avoid infinite loops
                    _logger.error('Breaking out of required task loop.')

            self._first_time = True
            self._run_task(section_index, task_index)
        else:
            self.update_completion_percentage(finished=True)
            _logger.error('Sending final report.')
            self._reported = True
            reporter = Reporter(self.activity)
            reporter.report([self.read_task_data()])

            self._destroy_graphics()
            graphics = Graphics()
            self._graphics = graphics
            url = os.path.join(self.get_bundle_path(), 'html-content',
                               'completed.html')
            self._graphics.add_uri(
                'file://' + url + '?NAME=' + utils.get_safe_text(
                    self.read_task_data(NAME_UID).replace(',', ' ')))
            self._graphics.set_zoom_level(0.667)
            self._graphics_grid.attach(self._graphics, 0, 0, 1, 1)
            self._graphics.show()
            self.task_button.set_label(_('Exit'))

    def enter_entered(self, task_data, uid):
        ''' Enter was entered in a text entry '''
        if not 'completed' in task_data or not task_data['completed']:
            task_data = self.read_task_data(uid)
            task_data['end_time'] = int(time.time() + 0.5)
            task_data['completed'] = True
            self._update_accumutaled_time(task_data)
        self.write_task_data(uid, task_data)
        self.button_was_pressed = True
        section_index, task_index = self.get_section_and_task_index()
        task = self._task_list[section_index]['tasks'][task_index]
        if task.after_button_press():
            self.current_task += 1
            self.write_task_data('current_task', self.current_task)
            self.task_master()

    def _task_button_cb(self, button):
        ''' The button at the bottom of the page for each task: used to
            advance to the next task. '''
        self.button_was_pressed = True
        section_index, task_index = self.get_section_and_task_index()
        task = self._task_list[section_index]['tasks'][task_index]
        if task.after_button_press():
            if self.current_task == self._get_number_of_tasks():
                # We want to make sure that the final report is sent, hence
                # the delay before closing.
                self.activity.busy_cursor()
                _logger.debug('All done: closing in 5 seconds')
                GObject.timeout_add(5000, self.activity.close)
            elif self._yes_task is not None:
                self.update_completion_percentage()
                self._jump_to_task_cb(None, 'yes')
            elif self._no_task is not None:
                self.update_completion_percentage()
                self._jump_to_task_cb(None, 'no')
            else:
                self.current_task += 1
                self.write_task_data('current_task', self.current_task)
                self.task_master()

    def _my_turn_button_cb(self, button):
        ''' Take me to the Home Page and select favorites view. '''
        # First, make sure current task data is saved.
        self.write_current_task_data()

        utils.goto_home_view()
        utils.select_favorites_view()

    def _skip_button_cb(self, button):
        ''' Jump to next section '''
        # First, make sure current task data is saved.
        self.write_current_task_data()

        section_index, task_index = self.get_section_and_task_index()
        section_index += 1

        # Don't skip off the end
        if section_index == self.get_number_of_sections():
            logging.debug('Do not skip off the end.')
            section_index = 0
            task_index = 0

        # Don't skip to last section unless all requirements are met
        if section_index == self.get_number_of_sections() - 1 and \
           not self.requirements_are_met(section_index, 0, switch_task=False):
            logging.debug('Checking requirements for last section.')
            if not self.uid_to_task(
                    tasks.CONNECTED_BADGE_TASK, section=None).is_completed():
                logging.debug('Connecting Chapter not complete')
                self.current_task = self.uid_to_task_number(
                    tasks.CONNECTED_BADGE_TASK)
                section_index, task_index = self.get_section_and_task_index()
            else:
                logging.debug('Connecting Chapter complete!')
                section_index = 0
                task_index = 0

        task = self._task_list[section_index]['tasks'][0]
        self.current_task = self.uid_to_task_number(task.uid)
        self.activity.progress_buttons[section_index].set_active(True)
        self.task_master()

    def _refresh_button_cb(self, button):
        ''' Refresh the current page's graphics '''
        self._destroy_graphics()

        section_index, task_index = self.get_section_and_task_index()
        task = self._task_list[section_index]['tasks'][task_index]

        self._graphics, label = task.get_graphics()
        self._graphics_grid.attach(self._graphics, 0, 0, 1, 1)
        self._graphics.show()
        # self.task_button.show()

    def get_help_info(self):
        ''' Uses help from the Help activity '''
        if self.current_task is None:
            return (None, None)
        else:
            section_index, task_index = self.get_section_and_task_index()
            task = self._task_list[section_index]['tasks'][task_index]
            return task.get_help_info()

    def _run_task(self, section_index, task_index):
        '''To run a task, we need graphics to display, a test to call that
            returns True or False, and perhaps some data '''

        task = self._task_list[section_index]['tasks'][task_index]
        if self._first_time:
            _logger.error('Running task %d: %s' % (self.current_task,
                                                   task.uid))

            self._uid = task.uid
            '''
            title, help_file = task.get_help_info()
            if title is None or help_file is None:
                self.activity._help_button.set_sensitive(False)
            else:
                self.activity._help_button.set_sensitive(True)
            '''
            self._load_graphics()

            self._task_data = self.read_task_data(self._uid)
            if self._task_data is None:
                self._init_task_data(task)
            elif 'completed' in self._task_data and \
                 self._task_data['completed']:
                _logger.debug('Revisiting a completed task')

            self._first_time = False

        GObject.timeout_add(task.get_pause_time(), self._test, task.test,
                            self._task_data, self._uid)

    def _init_task_data(self, task):
        # In order to calculate accumulated time, we need to monitor
        # our start time.
        self._start_time = time.time()
        self._accumulated_time = 0

        self._task_data = {}
        self._task_data['start_time'] = int(self._start_time + 0.5)
        self._task_data['accumulated_time'] = 0
        self._task_data['completed'] = False
        self._task_data['task'] = task.get_name()
        self._task_data['data'] = task.get_data()
        self._task_data['collectable'] = task.is_collectable()
        self.write_task_data(self._uid, self._task_data)

    def _update_accumutaled_time(self, task_data):
        end_time = time.time()
        self._accumulated_time += end_time - self._start_time
        task_data['accumulated_time'] += int(self._accumulated_time + 0.5)
        self._start_time = end_time

    def _test(self, test, task_data, uid):
        ''' Is the task complete? '''
        # We may have gotten here by jumping, so task_data may be None
        if task_data is None:        
            task_data = self.read_task_data(uid)
            if task_data is None:
                task = self.uid_to_task(uid)
                self._init_task_data(task)
                task_data = self._task_data

        if test(task_data):
            if not 'completed' in task_data or not task_data['completed']:
                task_data['end_time'] = int(time.time() + 0.5)
                task_data['completed'] = True
                self._update_accumutaled_time(task_data)
            self.write_task_data(uid, task_data)
            if self.task_button is not None:
                self.task_button.set_sensitive(True)
        else:
            if self.task_button is not None:
                self.task_button.set_sensitive(False)
            if not 'completed' in task_data or not task_data['completed']:
                self._update_accumutaled_time(task_data)
            # Don't save data at each test
            # self.write_task_data(uid, task_data)
            section_index, task_index = self.get_section_and_task_index()
            self._run_task(section_index, task_index)

    def write_current_task_data(self):
        if self._uid is not None:
            self.write_task_data(self._uid, self._task_data)

    def _jump_to_task_cb(self, widget, flag):
        ''' Jump to task associated with uid '''
        # First, make sure current task data is saved.
        self.write_current_task_data()

        section_index, task_index = self.get_section_and_task_index()
        task = self._task_list[section_index]['tasks'][task_index]

        self.button_was_pressed = True
        task.after_button_press()

        if flag == 'yes':
            uid = self._yes_task
        else:
            uid = self._no_task
        self.current_task = self.uid_to_task_number(uid)

        self.write_task_data('current_task', self.current_task)
        self.activity.progress_buttons[section_index].set_active(True)
        self.task_master()

    def _assign_required(self):
        ''' Add collectable tasks in each section to badge task. '''
        all_requirements = []
        for section in self._task_list:
            section_requirements = []
            for task in section['tasks']:
                if task.is_collectable():
                    section_requirements.append(task.uid)
                    all_requirements.append(task.uid)
            last = len(section['tasks']) - 1
            if section['tasks'][last].uid[0:5] == 'badge':
                section['tasks'][last].set_requires(section_requirements)
        self._task_list[-1]['tasks'][-1].set_requires(all_requirements)

    def requirements_are_met(self, section_index, task_index,
                             switch_task=True):
        ''' Check to make sure all the requirements at met '''
        task = self._task_list[section_index]['tasks'][task_index]
        requires = task.get_requires()
        for uid in requires:
            # Don't restrict search to current section
            if not self.uid_to_task(uid, section=None).is_completed():
                if switch_task:
                    _logger.debug('Task %s requires task %s... switching' %
                                  (task.uid, uid))
                    self.current_task = self.uid_to_task_number(uid)
                    section_index, task_index = \
                        self.get_section_and_task_index()
                    self.activity.progress_buttons[section_index].set_active(
                        True)
                return False
        return True

    def reload_graphics(self):
        ''' When changing font size and zoom level, we regenerate the task
           graphic. '''
        self._destroy_graphics()
        self._load_graphics()
        self._progress_bar.show()
        section_index, task_index = self.get_section_and_task_index()
        task = self._task_list[section_index]['tasks'][task_index]
        self._uid = self.section_and_task_to_uid(section_index, task_index)
        self._test(task.test, self._task_data, self._uid)

    def _destroy_graphics(self):
        ''' Destroy the graphics from the previous task '''
        if self._graphics is not None:
            self._graphics.destroy()
            self._graphics = None

    def _load_graphics(self):
        ''' Load the graphics for a task and define the task button '''
        section_index, task_index = self.get_section_and_task_index()
        task = self._task_list[section_index]['tasks'][task_index]

        task.set_font_size(self.activity.font_size)
        task.set_zoom_level(self.activity.zoom_level)

        self.activity.reset_scrolled_window_adjustments()

        if self._graphics is not None:
            self._graphics.destroy()
        graphics, label = task.get_graphics()
        self._graphics = graphics

        self._graphics_grid.attach(self._graphics, 0, 0, 1, 1)
        self._graphics.show()

        self._yes_task, self._no_task = task.get_yes_no_tasks()
        if self._yes_task is not None and self._no_task is not None:
            self.task_button.hide()
            self._yes_button.show()
            self._no_button.show()
        elif self.task_button is not None:
            self.task_button.set_label(label)
            self.task_button.set_sensitive(False)
            self.task_button.show()
            self._yes_button.hide()
            self._no_button.hide()

        if task.get_refresh():
            self._refresh_button.show()
        else:
            self._refresh_button.hide()

        if task.get_my_turn():
            self._next_task_button_cb(None)
            #self._my_turn_button.show()
        else:
            self._my_turn_button.hide()

        if task.get_skip():
            self._skip_button.show()
        else:
            self._skip_button.hide()

        self._update_progress()

        task.grab_focus()

    def get_bundle_path(self):
        return self.activity.bundle_path

    def get_number_of_sections(self):
        return len(self._task_list)

    def get_section_name(self, section_index):
        return self._task_list[section_index]['name']

    def get_section_icon(self, section_index):
        return self._task_list[section_index]['icon']

    def get_completed_sections(self):
        progress = []
        for section_index, section in enumerate(self._task_list):
            section_completed = True
            if self._get_number_of_collectables_in_section(section_index) == 0:
                for task in section['tasks']:
                    if self.read_task_data(task.uid) is None:
                        section_completed = False
            else:
                for task in section['tasks']:
                    if task.is_collectable() and not task.is_completed():
                        section_completed = False
            if section_completed:
                progress.append(section_index)
        return progress

    def section_and_task_to_uid(self, section_index, task_index=0):
        section = self._task_list[section_index]
        if section_index < 0 or (section_index >
                                 self.get_number_of_sections() - 1):
            _logger.error('Bad section index %d' % (section_index))
            return self._task_list[0]['tasks'][0].uid
        elif task_index > len(section['tasks']) - 1 or task_index < 0:
            _logger.error('Bad task index %d:%d' % (section_index, task_index))
            return self._task_list[0]['tasks'][0].uid
        else:
            return section['tasks'][task_index].uid

    def uid_to_task_number(self, uid):
        i = 0
        for section in self._task_list:
            for task in section['tasks']:
                if task.uid == uid:
                    return i
                i += 1
        _logger.error('UID %s not found' % uid)
        return 0

    def get_section_and_task_index(self):
        count = 0
        for section_index, section in enumerate(self._task_list):
            for task_index in range(len(section['tasks'])):
                if count == self.current_task:
                    return section_index, task_index
                count += 1
        return -1, -1

    def _get_number_of_tasks_in_section(self, section_index):
        return len(self._task_list[section_index]['tasks'])

    def _get_number_of_collectables_in_section(self, section_index):
        count = 0
        for task in self._task_list[section_index]['tasks']:
            if task.is_collectable():
                count += 1
        return count

    def _get_number_of_collectables(self):
        count = 0
        for section_index in range(len(self._task_list)):
            count += self._get_number_of_collectables_in_section(section_index)
        return count

    def _get_number_of_tasks(self):
        count = 0
        for section in self._task_list:
            count += len(section['tasks'])
        return count

    def uid_to_task(self, uid, section=None):
        if section:
            for task in section['tasks']:
                if task.uid == uid:
                    return task
        else:
            for section in self._task_list:
                for task in section['tasks']:
                    if task.uid == uid:
                        return task
        _logger.error('UID %s not found' % uid)
        return self._task_list[0]['tasks'][0]

    def _get_number_of_completed_tasks(self):
        count = 0
        for section in self._task_list:
            for task in section['tasks']:
                if task.is_completed():
                    count += 1
        return count

    def _get_number_of_completed_collectables(self):
        count = 0
        for section in self._task_list:
            for task in section['tasks']:
                if task.is_collectable() and task.is_completed():
                    count += 1
        return count

    def read_task_data(self, uid=None):
        usb_data_path = None
        sugar_data_path = self._sugar_data_path
        uid_data = None
        usb_read_failed = False
        data = {}

        if len(self.activity.volume_data) == 0:
            _logger.error('No USB device found... trying to read from Sugar.')
            usb_read_failed = True
        else:
            usb_data_path = os.path.join(
                self.activity.volume_data[0]['usb_path'],
                self.activity.volume_data[0]['uid'])
            sugar_data_path = os.path.join(
                self.activity.volume_data[0]['sugar_path'],
                self.activity.volume_data[0]['uid'])

        if usb_data_path is not None and os.path.exists(usb_data_path):
            if self._resync_required:
                # Last time, we couldn't read, so let's make sure the data
                # sets are in sync.
                _logger.error('Resyncing data sets')
                status = self.activity.sync_data_from_USB(usb_data_path)
                if not status:
                    _logger.error('RESYNC FAILED')
                self._resync_required = not status
            try:
                fd = open(usb_data_path, 'r')
                json_data = fd.read()
                fd.close()
            except Exception as e:
                # Maybe USB key has been pulled?
                _logger.error('Could not read from %s: %s' %
                              (usb_data_path, e))
                json_data = ''
                usb_read_failed = True
            try:
                if len(json_data) > 0:
                    data = json.loads(json_data)
            except ValueError as e:
                _logger.error('Cannot read training data: %s' % e)
                usb_read_failed = True

        # If for some reason USB read fails, try reading from Sugar
        if usb_read_failed and sugar_data_path is not None:
            _logger.error('read_task_data: Resync required')
            self._resync_required = True

            if os.path.exists(sugar_data_path):
                try:
                    fd = open(sugar_data_path, 'r')
                    json_data = fd.read()
                    fd.close()
                except Exception as e:
                    json_data = ''
                    _logger.error('Could not read from %s: %s' %
                                  (sugar_data_path, e))
                if len(json_data) > 0:
                    try:
                        data = json.loads(json_data)
                    except ValueError as e:
                        _logger.error('Cannot load training data: %s' % e)

        if uid is None:
            return data
        elif uid in data:
            uid_data = data[uid]

        return uid_data

    def write_task_data(self, uid, uid_data):
        usb_data_path = None
        sugar_data_path = self._sugar_data_path
        usb_read_failed = False
        sugar_read_failed = False
        data = {}

        if len(self.activity.volume_data) == 0:
            _logger.error('No USB device found... cannot save results.')
            usb_read_failed = True
        else:
            sugar_data_path = os.path.join(
                self.activity.volume_data[0]['sugar_path'],
                self.activity.volume_data[0]['uid'])
            usb_data_path = os.path.join(
                self.activity.volume_data[0]['usb_path'],
                self.activity.volume_data[0]['uid'])

        # Read before write
        if not usb_read_failed and os.path.exists(usb_data_path):
            try:
                fd = open(usb_data_path, 'r')
                json_data = fd.read()
                fd.close()
            except Exception as e:
                # Maybe USB key has been pulled?
                _logger.error('Could not read from %s: %s' %
                              (usb_data_path, e))
                json_data = ''
                usb_read_failed = True
            if len(json_data) > 0:
                try:
                    data = json.loads(json_data)
                except ValueError as e:
                    _logger.error('Cannot load training data: %s' % e)
                    usb_read_failed = True

        # If for some reason USB read fails, try reading from Sugar
        if usb_read_failed and sugar_data_path is not None:
            if os.path.exists(sugar_data_path):
                try:
                    fd = open(sugar_data_path, 'r')
                    json_data = fd.read()
                    fd.close()
                except Exception as e:
                    _logger.error('Could not read from %s: %s' %
                                  (sugar_data_path, e))
                    json_data = ''
                    sugar_read_failed = True
                if len(json_data) > 0:
                    try:
                        data = json.loads(json_data)
                    except ValueError as e:
                        _logger.error('Cannot load training data: %s' % e)
                        sugar_read_failed = True

        if usb_read_failed and sugar_read_failed:
            _logger.error('Cannot read training data in read before write')
            return

        data[uid] = uid_data

        # Make sure the volume UID and version number are present
        data[TRAINING_DATA_UID] = self.activity.get_uid()
        data[VERSION_NUMBER] = self.activity.get_activity_version()

        json_data = json.dumps(data)

        # Write to the USB and ...
        if not usb_read_failed:
            try:
                fd = open(usb_data_path, 'w')
                fd.write(json_data)
                fd.close()
            except Exception as e:
                _logger.error('Could not write to USB %s: %s' %
                              (usb_data_path, e))
                _logger.error('write_task_data: Resync required')
                self._resync_required = True

        # ... save shadow copy in Sugar
        try:
            fd = open(sugar_data_path, 'w')
            fd.write(json_data)
            fd.close()

            if usb_read_failed:
                _logger.error('write_task_data: Resync required')
                self._resync_required = True
        except Exception as e:
            _logger.error('Could not write to Sugar %s: %s' %
                          (sugar_data_path, e))

    def _prev_task_button_cb(self, button):
        section_index, task_index = self.get_section_and_task_index()
        if task_index == 0:
            return
        i = task_index
        while(i > 0):
            i -= 1
            if self.requirements_are_met(section_index, i,
                                         switch_task=False):
                self.current_task -= (task_index - i)
                break
        self.task_master()

    def _next_task_button_cb(self, button):
        section_index, task_index = self.get_section_and_task_index()
        tasks_in_section = self._get_number_of_tasks_in_section(section_index)
        if task_index > tasks_in_section - 1:
            return
        i = task_index + 1
        while(i < tasks_in_section - 1):
            if self.requirements_are_met(section_index, i,
                                         switch_task=False):
                self.current_task += (i - task_index)
                break
            i += 1
        self.task_master()

    def _look_for_next_task(self):
        section_index, task_index = self.get_section_and_task_index()
        tasks_in_section = self._get_number_of_tasks_in_section(section_index)
        if task_index > tasks_in_section - 1:
            return False
        i = task_index + 1
        while(i < tasks_in_section - 1):
            if self.requirements_are_met(section_index, i,
                                         switch_task=False):
                return True
            i += 1
        return False

    def _progress_button_cb(self, button, i):
        section_index, task_index = self.get_section_and_task_index()
        self.current_task += (i - task_index)
        self.task_master()

    def _update_progress(self):
        section_index, task_index = self.get_section_and_task_index()
        if section_index < 0:  # We haven't started yet
            return

        tasks_in_section = self._get_number_of_tasks_in_section(section_index)

        # If the task index is 0, then we need to create a new progress bar
        if task_index == 0 or self._progress_bar is None:
            if self._progress_bar is not None:
                self._progress_bar.destroy()

            buttons = []
            if tasks_in_section > 1:
                for i in range(tasks_in_section - 1):
                    task = self._task_list[section_index]['tasks'][i]
                    tooltip = task.get_name()
                    buttons.append({'label': str(i + 1), 'tooltip': tooltip})

            if self._name is None:
                self._name = self.read_task_data(NAME_UID)
            if self._name is not None:
                self._name = self._name.replace(',', ' ')
            if self._email is None:
                self._email = self.read_task_data(EMAIL_UID)
            if self._name is not None and self._email is not None:
                name = '%s\n%s' % (self._name, self._email)
            elif self._name is not None:
                name = self._name
            else:
                name = ''

            uid = self.activity.volume_data[0]['uid']

            self._progress_bar = ProgressBar(
                name,
                self._task_list[section_index]['name'],
                uid,
                buttons,
                self._prev_task_button_cb,
                self._next_task_button_cb,
                self._progress_button_cb)
            self._progress_bar_alignment.add(self._progress_bar)
            self._progress_bar.show()

        if tasks_in_section == 1:
            self._progress_bar.hide_prev_next_task_buttons()
        else:
            self._progress_bar.show_prev_next_task_buttons()

        # Set button sensitivity True for completed tasks and current task
        if task_index < tasks_in_section:
            for ti in range(tasks_in_section - 1):
                task = self._task_list[section_index]['tasks'][ti]
                if task.is_completed():
                    self._progress_bar.set_button_sensitive(ti, True)
                else:
                    self._progress_bar.set_button_sensitive(ti, False)
            # Current task (last task in section has no button)
            if task_index < tasks_in_section - 1:
                self._progress_bar.set_button_sensitive(task_index, True)

        if task_index > 0:
            self._progress_bar.prev_task_button.set_sensitive(True)
        else:
            self._progress_bar.prev_task_button.set_sensitive(False)

        if self._look_for_next_task():
            self._progress_bar.next_task_button.set_sensitive(True)
        else:
            self._progress_bar.next_task_button.set_sensitive(False)

        self.update_completion_percentage()

    def update_completion_percentage(self, finished=False):
        if finished:
            completion_percentage = 100
        else:
            # Round to nearest 5%
            completion_percentage = \
                self._get_number_of_completed_collectables() \
                * 100. / self._get_number_of_collectables()
            completion_percentage = (int(completion_percentage + 2.5) / 5) * 5
        self.activity.progress_label.set_markup(
            '<span foreground="%s" size="%s"><b>%s</b></span>' %
            (style.COLOR_WHITE.get_html(), 'x-large',
             _('Completed: %d%%' % (completion_percentage))))
        self.write_task_data(COMPLETION_PERCENTAGE, completion_percentage)
