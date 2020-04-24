# -*- coding: utf-8 -*-
#Copyright (c) 2013,14 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

import dbus
import os
import json
import subprocess
from time import sleep
from configparser import ConfigParser
from gettext import gettext as _

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

from gi.repository import SugarExt

from sugar3.activity import activity
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.toolbarbox import ToolbarButton
from sugar3.graphics.alert import ConfirmationAlert, NotifyAlert
from sugar3.graphics import style

NAME_UID = 'name'
EMAIL_UID = 'email_address'
SCHOOL_UID = 'school_sf_id'
SCHOOL_NAME = 'school_name'
POST_CODE = 'post_code'
ROLE_UID = 'role'
TRAINING_DATA_UID = 'training_data_uid'
VERSION_NUMBER = 'version_number'
COMPLETION_PERCENTAGE = 'completion_percentage'
TRAINING_DATA_EMAIL = 'training_data_email'
TRAINING_DATA_FULLNAME = 'training_data_fullname'
_NEW_TRAINING_SESSION = -1
_TRAINING_DATA_NOT_FOUND = -2
_USB_NOT_FOUND = -3

from utils import TRAINING_DATA, TRAINING_SUFFIX

from tasks import GET_CONNECTED_TASK
from taskmaster import TaskMaster
from graphics import Graphics, FONT_SIZES
from helppanel import HelpPanel
import utils
from power import get_power_manager

import logging
_logger = logging.getLogger('training-activity')


_MINIMUM_SPACE = 1024 * 1024 * 10  # 10MB is very conservative
_REQUIRED_SUGARSERVICES_VERSION = 5


def _check_gconf_settings():
    from gi.repository import GConf

    client = GConf.Client.get_default()

    # Training server
    client.set_string(
        '/desktop/sugar/services/training/url',
        'https://training.one-education.org/training/report ')
    client.set_string('/desktop/sugar/services/training/api_key',
                      'SbCeK4nH8dpQJsHNn9djza9g')

    # Zendesk
    client.set_string('/desktop/sugar/services/zendesk/url',
                      'https://oneedu.zendesk.com')
    client.set_string('/desktop/sugar/services/zendesk/token',
                      'eG8tc3VwcG9ydEBsYXB0b3Aub3JnLmF1L3Rva2VuOlZTaWM4'
                      'TThZbjZBRTJkMWxYNkFGbFhkZzUxSjlJSHFUQ01DYzNjOHY=')
    try:
        SugarExt.gconf_client_set_string_list(
            client, '/desktop/sugar/services/zendesk/fields',
            ['21891880', '21729904', '21729914'])
    except Exception as e:
        _logger.error('Could not set zendesk fields: %s' % e)


class TrainingActivity(activity.Activity):
    ''' A series of training exercises '''
    transfer_started_signal = GObject.Signal('started', arg_types=([]))
    transfer_progressed_signal = GObject.Signal('progressed', arg_types=([]))
    transfer_completed_signal = GObject.Signal('completed', arg_types=([]))
    transfer_failed_signal = GObject.Signal('failed', arg_types=([]))

    def __init__(self, handle):
        ''' Initialize the toolbars and restore any saved data '''
        try:
            super(TrainingActivity, self).__init__(handle)
        except dbus.exceptions.DBusException as e:
            _logger.error(str(e))

        self.connect('realize', self.__realize_cb)
        self.connect('started', self.__transfer_started_cb)
        self.connect('progressed', self.__transfer_progressed_cb)
        self.connect('completed', self.__transfer_completed_cb)
        self.connect('failed', self.__transfer_failed_cb)

        self.volume_monitor = Gio.VolumeMonitor.get()
        self._mount_added_id = self.volume_monitor.connect(
            'mount-added', self._mount_added_cb)
        self._mount_removed_id = self.volume_monitor.connect(
            'mount-removed', self._mount_removed_cb)

        if hasattr(self, 'metadata') and 'font_size' in self.metadata:
            self.font_size = int(self.metadata['font_size'])
        else:
            self.font_size = 8
        self.zoom_level = self.font_size / float(len(FONT_SIZES))
        _logger.debug('zoom level is %f' % self.zoom_level)

        # _check_gconf_settings()  # For debugging purposes

        self._setup_toolbars()
        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_WHITE.get_gdk_color())

        self.bundle_path = activity.get_bundle_path()
        self.volume_data = []
        self._selected_volume = None
        self._saved_uid = None
        self._new_session = False

        self.help_palette = None
        self.help_panel_visible = False
        self._copy_entry = None
        self._paste_entry = None
        self._webkit = None
        self._clipboard_text = ''
        self._fixed = None
        self._fatal_error = False
        self._notify_transfer_status = False

        if self.check_volume_data():
            if self.volume_data[0]['uid'] is not None:
                GObject.idle_add(self._launcher)

    def _launcher(self):
        get_power_manager().inhibit_suspend()

        # We are resuming the activity or we are launching a new instance?
        # * Is there a data file to sync on the USB key?
        # * Do we create a new data file on the USB key?
        path = self._check_for_USB_data()
        logging.debug('USB path is %s' % (path))
        if path is None:
            self._launch_task_master()
        elif self.sync_data_from_USB(path):
            self._copy_data_from_USB()
            if not self._new_session:
                # Flash a welcome back screen.
                self._load_intro_graphics(file_name='welcome-back.html')
            GObject.timeout_add(1500, self._launch_task_master)

    def can_close(self):
        get_power_manager().restore_suspend()
        return True

    def busy_cursor(self):
        self._old_cursor = self.get_window().get_cursor()
        self.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

    def reset_cursor(self):
        if hasattr(self, '_old_cursor'):
            self.get_window().set_cursor(self._old_cursor)

    def check_volume_data(self):
        # Before we begin (and before each task),
        # we need to find any and all USB keys
        # and any and all training-data files on them.

        if self._fatal_error:
            # We need to resolve the error before continuing
            _logger.error('Saw a fatal error, '
                          'so shutting down instead of checking volume data.')
            self.close()

        _logger.debug(utils.get_volume_paths())
        self.volume_data = []
        for path in utils.get_volume_paths():
            os.path.basename(path)
            self.volume_data.append(
                {'basename': os.path.basename(path),
                 'files': utils.look_for_training_data(path),
                 'sugar_path': os.path.join(self.get_activity_root(), 'data'),
                 'usb_path': path})
            _logger.debug(self.volume_data[-1])

        # (1) We require a USB key
        if len(self.volume_data) == 0:
            _logger.error('NO USB KEY INSERTED')
            alert = ConfirmationAlert()
            alert.props.title = _('USB key required')
            alert.props.msg = _('You must insert a USB key before launching '
                                'this activity.')
            alert.connect('response', self.remove_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(file_name='insert-usb.html')
            return False

        # (2) Only one USB key
        if len(self.volume_data) > 1:
            _logger.error('MULTIPLE USB KEYS INSERTED')
            alert = ConfirmationAlert()
            alert.props.title = _('Multiple USB keys found')
            alert.props.msg = _('Only one USB key must be inserted while '
                                'running this program.\nPlease remove any '
                                'additional USB keys before launching '
                                'this activity.')
            alert.connect('response', self.remove_alert_cb)
            # self.add_alert(alert)
            # self._load_intro_graphics(message=alert.props.msg)
            # return False
            self._load_usb_selection_graphics(self._select_usb_button_cb)
            # FIX ME: we need to wait for the user input here.
            volume = self.volume_data[self._selected_volume]
            if self._selected_volume is None:
                self.add_alert(alert)
                self._load_intro_graphics(message=alert.props.msg)
                return False

        volume = self.volume_data[0]

        # (3) At least 10MB of free space
        if utils.is_full(volume['usb_path'],
                         required=_MINIMUM_SPACE):
            _logger.error('USB IS FULL')
            alert = ConfirmationAlert()
            alert.props.title = _('USB key is full')
            alert.props.msg = _('No room on USB')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
            return False

        # (4) File is read/write
        if not utils.is_writeable(volume['usb_path']):
            _logger.error('CANNOT WRITE TO USB')
            alert = ConfirmationAlert()
            alert.props.title = _('Cannot write to USB')
            alert.props.msg = _('USB key seems to be read-only.')
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
            return False

        # (5) Only one set of training data per USB key
        # We expect UIDs to formated as XXXX-XXXX.txt
        # We need to make sure we have proper UIDs associated with
        # the USBs and the files on them match the UID.
        # (a) If there are no files, we will assign the UID based on the
        #     volume path;
        # (b) If there is one file with a valid UID, we use that UID;
        if len(volume['files']) == 0:
            _logger.debug('0 FILES FOUND')
            basename = TRAINING_DATA % \
                       utils.format_volume_name(volume['basename'])
            _logger.debug('volume basename: %s' % basename)
            volume['uid'] = basename + TRAINING_SUFFIX
            _logger.debug('No training data found. Using UID %s' %
                          volume['uid'])
            return True
        elif len(volume['files']) == 1:
            _logger.debug('1 FILE FOUND')
            volume['uid'] = utils.check_volume_suffix(volume['files'][0])
            # In case we renamed the files, rescan
            volume['files'] = utils.look_for_training_data(path)
            _logger.debug(volume['files'])
            _logger.debug('Training data found. Using UID %s' %
                          volume['uid'])
            return True
        else:
            _logger.error('MULTIPLE TRAINING-DATA FILES FOUND.')
            if self._saved_uid is not None:
                # Make sure the saved uid is in the list
                logging.debug(self._saved_uid)
                logging.debug(volume['files'])
                if os.path.join(volume['usb_path'],
                                self._saved_uid) in volume['files']:
                    volume['uid'] = self._saved_uid
                    return True
                else:
                    # FIXME: need better feedback to the user here
                    alert = NotifyAlert()
                    alert.props.title = _('Multiple training-data files found.')
                    alert.props.msg = _('Your taining data seems to be '
                                        'missing.')
                    self._load_intro_graphics(message=alert.props.msg)
                    return False

            email_list = []
            completed_list = []
            name_list = []
            for file_name in volume['files']:
                path = os.path.join(volume['usb_path'], file_name)
                email_list.append(utils.get_email_from_training_data(path))
                completed_list.append(
                    utils.get_completed_from_training_data(path))
                name_list.append(utils.get_name_from_training_data(path))
            emails_match = True
            for email in email_list:
                if email != email_list[0]:
                    emails_match = False
                    break

            # If the email address is set and is the same in all of
            # the training-data files, then we'll use the dataset that
            # has the most completed tasks.
            if email_list[0] is not None and emails_match:
                max_index = 0
                max_completed = completed_list[0]
                for i, completed in enumerate(completed_list):
                    if completed > max_completed:
                        max_index = i
                        max_completed = completed
                volume['uid'] = utils.check_volume_suffix(
                    volume['files'][max_index])
                self._saved_uid = volume['uid']
                return True

            # If the email address is set and is *not* the same in all
            # of the training-data files, then we'll prompt the user
            # to select the correct one.
            alert = NotifyAlert()
            alert.props.title = _('Multiple training-data files found.')
            alert.props.msg = _('Please select the training data that '
                                'corresponds to your session.')
            alert.connect('response', self.remove_alert_cb)
            self.add_alert(alert)
            self._load_selection_graphics(email_list, name_list,
                                          self._select_file_button_cb)
            volume['uid'] = None
            return True

    def _load_usb_selection_graphics(self, callback):
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        graphics = Graphics()
        # FIXME: need some better instructions here
        graphics.add_text(
            _('Please select your USB key from the list below.'))
        for i, volume in enumerate(self.volume_data):
            # FIXME: temporary kludge for NextGen machine
            if not 'Volume' in volume['basename']:
                self._selected_volume = i
                return True
            button = graphics.add_button(volume['basename'], callback, arg=i)
            button.show()

        button = graphics.add_button(_('My USB is not in the list.'),
                                     callback, arg=-1)
        button.show()

        center_in_panel.add(graphics)
        graphics.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

    def _load_selection_graphics(self, email_list, name_list, callback):
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        graphics = Graphics()
        # FIXME: need some better instructions here
        graphics.add_text(
            _('Please select your name/email from the list below.'))
        for i in range(len(email_list)):
            # Use str so as to accept None as a valid name or email
            name = str(name_list[i])
            email = str(email_list[i])

            button = graphics.add_button('%s <%s>' % (name_list[i], email),
                                         callback, arg=i)
            button.show()

        button = graphics.add_button(_('Start a new training session.'),
                                     callback, arg=_NEW_TRAINING_SESSION)
        button.show()

        button = graphics.add_button(_('My name/email is not in the list.'),
                                     callback, arg=_TRAINING_DATA_NOT_FOUND)
        button.show()

        center_in_panel.add(graphics)
        graphics.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

    def _is_uid_unique(self, uid):
        for file_name in self.volume_data[0]['files']:
            if file_name == TRAINING_DATA % (uid):
                return False
            elif file_name == TRAINING_DATA % (uid) + TRAINING_SUFFIX:
                return False
            elif file_name == TRAINING_DATA % (uid) + '.bin':  # See SEP-33
                return False
            return True

    def _select_usb_button_cb(self, widget, i):
        logging.debug('SELECT USB BUTTON %d' % i)
        if i < 0:
            self._selected_volume = None
        else:
            self._selected_volume = i

    def _select_file_button_cb(self, widget, i):
        logging.debug('SELECT FILE BUTTON %d' % i)
        if i == _NEW_TRAINING_SESSION:
            # Start a new session
            uid = utils.generate_uid()
            while not self._is_uid_unique(uid):
                uid = utils.generate_uid()
            logging.error('Creating new uid %s' % (uid))
            self._saved_uid = self.volume_data[0]['uid'] = \
                             TRAINING_DATA % (uid) + TRAINING_SUFFIX

            # Create new session on volume
            data = {}
            data[TRAINING_DATA_UID] = self.volume_data[0]['uid']
            data[VERSION_NUMBER] = self.get_activity_version()
            json_data = json.dumps(data)

            write_failed = False
            usb_data_path = os.path.join(self.volume_data[0]['usb_path'],
                                         self.volume_data[0]['uid'])
            try:
                fd = open(usb_data_path, 'w')
                fd.write(json_data)
                fd.close()
            except Exception as e:
                write_failed = True
                _logger.error('Could not write to USB %s: %s' %
                              (usb_data_path, e))
            if write_failed:
                alert = NotifyAlert()
                alert.props.title = _('Could not launch new session.')
                alert.props.msg = _('Please contact One Education.')
                logging.error(alert.props.msg)
                alert.connect('response', self._close_alert_cb)
                self.add_alert(alert)
                self._load_intro_graphics(message=alert.props.msg)
            else:
                self._new_session = True
                self._launcher()
        elif i == _TRAINING_DATA_NOT_FOUND:
            # Name not in list
            alert = NotifyAlert()
            alert.props.title = _('No match in training data found.')
            alert.props.msg = _('Please contact One Education.')
            logging.error(alert.props.msg)
            alert.connect('response', self._close_alert_cb)
            self.add_alert(alert)
            self._load_intro_graphics(message=alert.props.msg)
        else:
            # Continue with selected session
            volume = self.volume_data[0]
            logging.error('Opting for %s' % (volume['files'][i]))
            volume['uid'] = TRAINING_DATA % volume['files'][i][-9:]
            self._saved_uid = volume['uid']
            self._launcher()

    def _check_for_USB_data(self):
        usb_path = os.path.join(self.volume_data[0]['usb_path'],
                                self.volume_data[0]['uid'])
        if os.path.exists(usb_path):
            return usb_path
        else:
            return None

    def sync_data_from_USB(self, usb_data_path=None):
        # We need to sync up file on USB with file on disk,
        # but only if the email addresses match. Otherwise,
        # raise an error.
        if self._fatal_error:
            # We need to resolve the error before continuing
            _logger.error('Saw a fatal error, '
                          'so shutting down instead of syncing data.')
            self.close()

        if usb_data_path is not None:
            usb_data = {}
            if os.path.exists(usb_data_path):
                fd = open(usb_data_path, 'r')
                json_data = fd.read()
                fd.close()
                if len(json_data) > 0:
                    try:
                        usb_data = json.loads(json_data)
                    except ValueError as e:
                        _logger.error('Cannot load USB data: %s' % e)
            else:
                _logger.error('Cannot find USB data: %s' % usb_data_path)

            sugar_data_path = os.path.join(
                self.volume_data[0]['sugar_path'],
                self.volume_data[0]['uid'])
            sugar_data = {}
            if os.path.exists(sugar_data_path):
                fd = open(sugar_data_path, 'r')
                json_data = fd.read()
                fd.close()
                if len(json_data) > 0:
                    try:
                        sugar_data = json.loads(json_data)
                    except ValueError as e:
                        _logger.error('Cannot load Sugar data: %s' % e)
            else:
                _logger.error('Cannot find Sugar data: %s' % sugar_data_path)

            # First, check to make sure email_address matches
            if EMAIL_UID in usb_data:
                usb_email = usb_data[EMAIL_UID]
            else:
                usb_email = None
            if EMAIL_UID in sugar_data:
                sugar_email = sugar_data[EMAIL_UID]
            else:
                sugar_email = None
            if usb_email != sugar_email:
                if usb_email is None and sugar_email is not None:
                    _logger.warning('Using email address from Sugar: %s' %
                                    sugar_email)
                    usb_data[EMAIL_UID] = sugar_email
                elif usb_email is not None and sugar_email is None:
                    _logger.warning('Using email address from USB: %s' %
                                    usb_email)
                    sugar_data[EMAIL_UID] = usb_email
                elif usb_email is None and sugar_email is None:
                    _logger.warning('No email address found')
                else:
                    # FIX ME: We need to resolve this, but for right now, punt.
                    alert = ConfirmationAlert()
                    alert.props.title = _('Data mismatch')
                    alert.props.msg = _('Are you %(usb)s or %(sugar)s?' %
                                        {'usb': usb_email,
                                         'sugar': sugar_email})
                    alert.connect('response', self._close_alert_cb)
                    self.add_alert(alert)
                    self._load_intro_graphics(message=alert.props.msg)
                    return False

            def count_completed(data):
                count = 0
                for key in data:
                    if isinstance(data[key], dict) and \
                       'completed' in data[key] and \
                       data[key]['completed']:
                        count += 1
                return count

            # The database with the most completed tasks takes precedence.
            if count_completed(usb_data) >= count_completed(sugar_data):
                _logger.debug('data sync: USB data takes precedence')
                data_one = usb_data
                data_two = sugar_data
            else:
                _logger.debug('data sync: Sugar data takes precedence')
                data_one = sugar_data
                data_two = usb_data

            # Copy completed tasks from one to two
            for key in data_one:
                if isinstance(data_one[key], dict) and \
                   'completed' in data_one[key] and \
                   data_one[key]['completed']:
                    data_two[key] = data_one[key]

            # Copy completed tasks from two to one
            for key in data_two:
                if isinstance(data_two[key], dict) and \
                   'completed' in data_two[key] and \
                   data_two[key]['completed']:
                    data_one[key] = data_two[key]

            # Copy incompleted tasks from one to two
            for key in data_one:
                if isinstance(data_one[key], dict) and \
                   (not 'completed' in data_one[key] or
                    not data_one[key]['completed']):
                        data_two[key] = data_one[key]

            # Copy incompleted tasks from two to one
            for key in data_two:
                if isinstance(data_two[key], dict) and \
                   (not 'completed' in data_two[key] or
                    not data_two[key]['completed']):
                        data_one[key] = data_two[key]

            # Copy name, email_address, current_task...
            for key in data_one:
                if not isinstance(data_one[key], dict):
                    data_two[key] = data_one[key]
            for key in data_two:
                if not isinstance(data_two[key], dict):
                    data_one[key] = data_two[key]

            # Finally, write to the USB and ...
            json_data = json.dumps(data_one)
            try:
                fd = open(usb_data_path, 'w')
                fd.write(json_data)
                fd.close()
            except Exception as e:
                self._fatal_error = True
                _logger.error('Fatal error: could not write to %s: %s' %
                              (usb_data_path, e))

                # Don't try remounting since we are going to close.
                self.volume_monitor.disconnect(self._mount_added_id)
                self.volume_monitor.disconnect(self._mount_removed_id)

                alert = ConfirmationAlert()
                alert.props.title = _('USB key problem')
                alert.props.msg = \
                    _('We need to run a file check.')
                alert.connect('response', self._dos_fsck_alert_cb)
                self.add_alert(alert)
                self._load_intro_graphics(file_name='fsck-usb.html')
                return False

            # ...save a shadow copy in Sugar
            fd = open(sugar_data_path, 'w')
            fd.write(json_data)
            fd.close()
            return True
        else:
            _logger.error('No data to sync on USB')
            return False

    def _copy_data_from_USB(self):
        usb_path = self._check_for_USB_data()
        if usb_path is not None:
            try:
                subprocess.call(['cp', usb_path,
                                 self.volume_data[0]['sugar_path']])
            except OSError as e:
                _logger.error('Could not copy %s to %s: %s' % (
                    usb_path, self.volume_data[0]['sugar_path'], e))
        else:
            _logger.error('No data found on USB')

    def toolbar_expanded(self):
        if self.activity_button.is_expanded():
            return True
        elif self.edit_toolbar_button.is_expanded():
            return True
        elif self.view_toolbar_button.is_expanded():
            return True
        elif hasattr(self, 'progress_toolbar_button') and \
             self.progress_toolbar_button.is_expanded():
            return True
        return False

    def _launch_task_master(self):
        # Most things need only be done once
        if self._fixed is None:
            self._fixed = Gtk.Fixed()
            self._fixed.set_size_request(Gdk.Screen.width(),
                                         Gdk.Screen.height())

            # Offsets from the bottom of the screen
            dy1 = 3 * style.GRID_CELL_SIZE
            dy2 = 2 * style.GRID_CELL_SIZE

            self._progress_area = Gtk.Alignment.new(0.5, 0, 0, 0)
            self._progress_area.set_size_request(Gdk.Screen.width(), -1)
            self._fixed.put(self._progress_area, 0, Gdk.Screen.height() - dy2)
            self._progress_area.show()

            self._button_area = Gtk.Alignment.new(0.5, 0, 0, 0)
            self._button_area.set_size_request(Gdk.Screen.width(), -1)
            self._fixed.put(self._button_area, 0, Gdk.Screen.height() - dy1)
            self._button_area.show()

            self._scrolled_window = Gtk.ScrolledWindow()
            self._scrolled_window.set_size_request(
                Gdk.Screen.width(), Gdk.Screen.height() - dy1)
            self._set_scroll_policy()
            self._graphics_area = Gtk.Alignment.new(0.5, 0, 0, 0)
            self._scrolled_window.add_with_viewport(self._graphics_area)
            self._graphics_area.show()
            self._fixed.put(self._scrolled_window, 0, 0)
            self._scrolled_window.show()

            self.favorites_count = len(utils.get_favorites())

            self._task_master = TaskMaster(self)
            self._task_master.show()

            # Now that we have the tasks, we can build the progress toolbar and
            # help panel.
            self._build_progress_toolbar()

            self._help_panel = HelpPanel(self._task_master)
            self.help_palette = self._help_button.get_palette()
            self.help_palette.set_content(self._help_panel)
            self._help_panel.show()
            self._help_button.set_sensitive(True)

            Gdk.Screen.get_default().connect('size-changed',
                                             self._configure_cb)
            self._toolbox.connect('hide', self._resize_hide_cb)
            self._toolbox.connect('show', self._resize_show_cb)

            self._task_master.set_events(Gdk.EventMask.KEY_PRESS_MASK)
            self._task_master.connect('key_press_event',
                                      self._task_master.keypress_cb)
            self._task_master.set_can_focus(True)
            self._task_master.grab_focus()

        self.set_canvas(self._fixed)
        self._fixed.show()

        self._update_completed_sections()
        self._check_connected_task_status()
        self._task_master.task_master()

    def reset_scrolled_window_adjustments(self):
        adj = self._scrolled_window.get_hadjustment()
        if adj is not None:
            adj.set_value(0)
        adj = self._scrolled_window.get_vadjustment()
        if adj is not None:
            adj.set_value(0)

    def load_graphics_area(self, widget):
        self._graphics_area.add(widget)

    def load_button_area(self, widget):
        self._button_area.add(widget)

    def load_progress_area(self, widget):
        self._progress_area.add(widget)

    def _load_intro_graphics(self, file_name='generic-problem.html',
                             message=None):
        center_in_panel = Gtk.Alignment.new(0.5, 0, 0, 0)
        url = os.path.join(self.bundle_path, 'html-content', file_name)
        graphics = Graphics()
        if message is None:
            graphics.add_uri('file://' + url)
        else:
            graphics.add_uri('file://' + url + '?MSG=' +
                             utils.get_safe_text(message))
        graphics.set_zoom_level(0.667)
        center_in_panel.add(graphics)
        graphics.show()
        self.set_canvas(center_in_panel)
        center_in_panel.show()

    def _resize_hide_cb(self, widget):
        self._resize_canvas(widget, True)

    def _resize_show_cb(self, widget):
        self._resize_canvas(widget, False)

    def _configure_cb(self, event):
        self._fixed.set_size_request(Gdk.Screen.width(), Gdk.Screen.height())
        self._set_scroll_policy()
        self._resize_canvas(None)
        self._task_master.reload_graphics()

    def _resize_canvas(self, widget, fullscreen=False):
        # When a toolbar is expanded or collapsed, resize the canvas
        # to ensure that the progress bar is still visible.
        if hasattr(self, '_task_master'):
            if self.toolbar_expanded():
                dy1 = 4 * style.GRID_CELL_SIZE
                dy2 = 3 * style.GRID_CELL_SIZE
            else:
                dy1 = 3 * style.GRID_CELL_SIZE
                dy2 = 2 * style.GRID_CELL_SIZE

            if fullscreen:
                dy1 -= 2 * style.GRID_CELL_SIZE
                dy2 -= 2 * style.GRID_CELL_SIZE

            self._scrolled_window.set_size_request(
                Gdk.Screen.width(), Gdk.Screen.height() - dy1)
            self._fixed.move(self._progress_area, 0, Gdk.Screen.height() - dy2)
            self._fixed.move(self._button_area, 0, Gdk.Screen.height() - dy1)

        self.help_panel_visible = False

    def get_activity_version(self):
        info_path = os.path.join(self.bundle_path, 'activity', 'activity.info')
        try:
            info_file = open(info_path, 'r')
        except Exception as e:
            _logger.error('Could not open %s: %s' % (info_path, e))
            return 'unknown'

        cp = ConfigParser()
        cp.readfp(info_file)

        section = 'Activity'

        if cp.has_option(section, 'activity_version'):
            activity_version = cp.get(section, 'activity_version')
        else:
            activity_version = 'unknown'
        return activity_version

    def get_uid(self):
        if len(self.volume_data) == 1:
            return self.volume_data[0]['uid']
        else:
            return 'unknown'

    def write_file(self, file_path):
        # Only write if we have a valid USB/data file to work with.
        if len(self.volume_data) == 1 and \
           len(self.volume_data[0]['files']) == 1:
            self.metadata[TRAINING_DATA_UID] = self.volume_data[0]['uid']

            # We may have failed before getting to init of taskmaster
            if hasattr(self, '_task_master'):
                self._task_master.write_task_data(
                    'current_task', self._task_master.current_task)
                self._task_master.write_current_task_data()
                self.update_activity_title()
                email = self._task_master.read_task_data(EMAIL_UID)
                if email is None:
                    email = ''
                self.metadata[TRAINING_DATA_EMAIL] = email
                name = self._task_master.read_task_data(NAME_UID)
                if name is None:
                    name = ''
                self.metadata[TRAINING_DATA_FULLNAME] = name

        self.metadata['font_size'] = str(self.font_size)

    def update_activity_title(self):
        name = self._task_master.read_task_data(NAME_UID)
        if name is not None:
            bundle_name = activity.get_bundle_name()
            self.metadata['title'] = _('%(name)s %(bundle)s Activity') % \
                {'name': name, 'bundle': bundle_name}

    def _setup_toolbars(self):
        ''' Setup the toolbars. '''
        self.max_participants = 1  # No sharing

        self._toolbox = ToolbarBox()

        self.activity_button = ActivityToolbarButton(self)
        self.activity_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.activity_button, 0)
        self.activity_button.show()

        self.set_toolbar_box(self._toolbox)
        self._toolbox.show()
        self.toolbar = self._toolbox.toolbar

        view_toolbar = Gtk.Toolbar()
        self.view_toolbar_button = ToolbarButton(
            page=view_toolbar,
            label=_('View'),
            icon_name='toolbar-view')
        self.view_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.view_toolbar_button, 1)
        view_toolbar.show()
        self.view_toolbar_button.show()

        button = ToolButton('view-fullscreen')
        button.set_tooltip(_('Fullscreen'))
        button.props.accelerator = '<Alt>Return'
        view_toolbar.insert(button, -1)
        button.show()
        button.connect('clicked', self._fullscreen_cb)

        self._zoom_in = ToolButton('zoom-in')
        self._zoom_in.set_tooltip(_('Increase size'))
        view_toolbar.insert(self._zoom_in, -1)
        self._zoom_in.show()
        self._zoom_in.connect('clicked', self._zoom_in_cb)

        self._zoom_out = ToolButton('zoom-out')
        self._zoom_out.set_tooltip(_('Decrease size'))
        view_toolbar.insert(self._zoom_out, -1)
        self._zoom_out.show()
        self._zoom_out.connect('clicked', self._zoom_out_cb)

        self._zoom_eq = ToolButton('zoom-original')
        self._zoom_eq.set_tooltip(_('Restore original size'))
        view_toolbar.insert(self._zoom_eq, -1)
        self._zoom_eq.show()
        self._zoom_eq.connect('clicked', self._zoom_eq_cb)

        self._set_zoom_buttons_sensitivity()

        edit_toolbar = Gtk.Toolbar()
        self.edit_toolbar_button = ToolbarButton(
            page=edit_toolbar,
            label=_('Edit'),
            icon_name='toolbar-edit')
        self.edit_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.edit_toolbar_button, 1)
        edit_toolbar.show()
        self.edit_toolbar_button.show()

        self._copy_button = ToolButton('edit-copy')
        self._copy_button.set_tooltip(_('Copy'))
        self._copy_button.props.accelerator = '<Ctrl>C'
        edit_toolbar.insert(self._copy_button, -1)
        self._copy_button.show()
        self._copy_button.connect('clicked', self._copy_cb)
        self._copy_button.set_sensitive(False)

        self._paste_button = ToolButton('edit-paste')
        self._paste_button.set_tooltip(_('Paste'))
        self._paste_button.props.accelerator = '<Ctrl>V'
        edit_toolbar.insert(self._paste_button, -1)
        self._paste_button.show()
        self._paste_button.connect('clicked', self._paste_cb)
        self._paste_button.set_sensitive(False)

        self._progress_toolbar = Gtk.Toolbar()
        self.progress_toolbar_button = ToolbarButton(
            page=self._progress_toolbar,
            label=_('Check progress'),
            icon_name='check-progress')
        self.progress_toolbar_button.connect('clicked', self._resize_canvas)
        self._toolbox.toolbar.insert(self.progress_toolbar_button, -1)
        self._progress_toolbar.show()
        self.progress_toolbar_button.show()

        self._help_button = ToolButton('toolbar-help')
        self._help_button.set_tooltip(_('Help'))
        self._help_button.props.accelerator = '<Ctrl>H'
        self._toolbox.toolbar.insert(self._help_button, -1)
        self._help_button.show()
        self._help_button.connect('clicked', self._help_cb)
        self._help_button.set_sensitive(False)
        self._help_button.palette_invoker.props.lock_palette = True

        self.transfer_button = ToolButton('transfer')
        self.transfer_button.set_tooltip(_('Training data upload status'))
        self._toolbox.toolbar.insert(self.transfer_button, -1)
        self.transfer_button.connect('clicked', self._transfer_cb)
        self.transfer_button.hide()

        self.progress_label = Gtk.Label()
        self.progress_label.set_line_wrap(True)
        self.progress_label.set_size_request(300, -1)
        self.progress_label.set_use_markup(True)
        toolitem = Gtk.ToolItem()
        toolitem.add(self.progress_label)
        self.progress_label.show()
        self._toolbox.toolbar.insert(toolitem, -1)
        toolitem.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        self._toolbox.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        self._toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def _build_progress_toolbar(self):
        self.progress_buttons = []
        progress = self._task_master.get_completed_sections()

        for section_index in range(self._task_master.get_number_of_sections()):
            icon = self._task_master.get_section_icon(section_index)
            if section_index in progress:
                icon = icon + '-white'
            else:
                icon = icon + '-grey'

            name = self._task_master.get_section_name(section_index)

            if section_index == 0:
                group = None
            else:
                group = self.progress_buttons[0]

            self.progress_buttons.append(RadioToolButton(group=group))
            self.progress_buttons[-1].set_icon_name(icon)
            self.progress_buttons[-1].set_tooltip(name)
            self._progress_toolbar.insert(self.progress_buttons[-1], -1)
            self.progress_buttons[-1].show()
            self.progress_buttons[-1].connect(
                'clicked', self._jump_to_section_cb, section_index)

        self._radio_buttons_live = False
        section_index, task_index = \
            self._task_master.get_section_and_task_index()
        self.progress_buttons[section_index].set_active(True)
        self._radio_buttons_live = True

    def _check_connected_task_status(self):
        ''' We only want to turn on notifications if we expect connectivity '''
        task = self._task_master.uid_to_task(GET_CONNECTED_TASK)
        self.set_notify_transfer_status(task.is_completed())

    def _update_completed_sections(self):
        progress = self._task_master.get_completed_sections()

        for section in range(self._task_master.get_number_of_sections()):
            icon = self._task_master.get_section_icon(section)
            if section in progress:
                icon = icon + '-white'
            else:
                icon = icon + '-grey'
            self.progress_buttons[section].set_icon_name(icon)

        self._radio_buttons_live = False
        section_index, task_index = \
            self._task_master.get_section_and_task_index()
        self.progress_buttons[section_index].set_active(True)
        self._radio_buttons_live = True

    def mark_section_as_complete(self, section):
        icon = self._task_master.get_section_icon(section) + '-white'
        self.progress_buttons[section].set_icon_name(icon)
        if section < self._task_master.get_number_of_sections() - 1:
            self._radio_buttons_live = False
            self.progress_buttons[section + 1].set_active(True)
            self._radio_buttons_live = True

    def set_notify_transfer_status(self, state):
        _logger.debug('Setting transfer status to %s' % (str(state)))
        self._notify_transfer_status = state

    def _update_transfer_button(self, icon_name, tooltip):
        self.transfer_button.set_icon_name(icon_name)
        self.transfer_button.set_tooltip(tooltip)
        if self._notify_transfer_status:
            self.transfer_button.show()
        else:
            self.transfer_button.hide()

    def _transfer_cb(self, button):
        ''' Hide the button to dismiss notification '''
        self.transfer_button.set_tooltip(_('Training data upload status'))
        self.transfer_button.hide()

    def __transfer_started_cb(self, widget):
        self._update_transfer_button('transfer', _('Data transfer started'))

    def __transfer_progressed_cb(self, widget):
        self._update_transfer_button('transfer',
                                     _('Data transfer progressing'))

    def __transfer_completed_cb(self, widget):
        self._update_transfer_button('transfer-complete',
                                     _('Data transfer completed'))

    def __transfer_failed_cb(self, widget):
        self._update_transfer_button('transfer-failed',
                                     _('Data transfer failed'))

    def __realize_cb(self, window):
        self.window_xid = window.get_window().get_xid()

    def set_copy_widget(self, webkit=None, text_entry=None):
        # Each task is responsible for setting a widget for copy
        if webkit is not None:
            self._webkit = webkit
        else:
            self._webkit = None
        if text_entry is not None:
            self._copy_entry = text_entry
        else:
            self._copy_entry = None

        self._copy_button.set_sensitive(webkit is not None or
                                        text_entry is not None)

    def _copy_cb(self, button):
        if self._copy_entry is not None:
            self._copy_entry.copy_clipboard()
        elif self._webkit is not None:
            self._webkit.copy_clipboard()
        else:
            _logger.debug('No widget set for copy.')

    def set_paste_widget(self, text_entry=None):
        # Each task is responsible for setting a widget for paste
        if text_entry is not None:
            self._paste_entry = text_entry
        self._paste_button.set_sensitive(text_entry is not None)

    def _paste_cb(self, button):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        self.clipboard_text = clipboard.wait_for_text()
        if self._paste_entry is not None:
            self._paste_entry.paste_clipboard()
        else:
            _logger.debug('No widget set for paste (%s).' %
                          self.clipboard_text)

    def _fullscreen_cb(self, button):
        ''' Hide the Sugar toolbars. '''
        self.fullscreen()

    def _set_zoom_buttons_sensitivity(self):
        if self.font_size < len(FONT_SIZES) - 1:
            self._zoom_in.set_sensitive(True)
        else:
            self._zoom_in.set_sensitive(False)
        if self.font_size > 0:
            self._zoom_out.set_sensitive(True)
        else:
            self._zoom_out.set_sensitive(False)

        if hasattr(self, '_scrolled_window'):
            self._set_scroll_policy()

    def _set_scroll_policy(self):
        if Gdk.Screen.width() < Gdk.Screen.height() or self.zoom_level > 0.667:
            self._scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                             Gtk.PolicyType.AUTOMATIC)
        else:
            self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                             Gtk.PolicyType.AUTOMATIC)

    def _zoom_eq_cb(self, button):
        self.font_size = 8
        self.zoom_level = 0.667
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _zoom_in_cb(self, button):
        if self.font_size < len(FONT_SIZES) - 1:
            self.font_size += 1
            self.zoom_level *= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _zoom_out_cb(self, button):
        if self.font_size > 0:
            self.font_size -= 1
            self.zoom_level /= 1.1
        self._set_zoom_buttons_sensitivity()
        self._task_master.reload_graphics()

    def _jump_to_section_cb(self, button, section_index):
        if self._radio_buttons_live:
            if self._task_master.requirements_are_met(section_index, 0):
                uid = self._task_master.section_and_task_to_uid(section_index)
                self._task_master.current_task = \
                    self._task_master.uid_to_task_number(uid)
                self._task_master.reload_graphics()
            else:
                section_index, task_index = \
                    self._task_master.get_section_and_task_index()
                self.progress_buttons[section_index].set_active(True)

    def _help_cb(self, button):
        # title, help_file = self._task_master.get_help_info()
        # _logger.debug('%s: %s' % (title, help_file))
        # if not hasattr(self, 'window_xid'):
        #    self.window_xid = self.get_window().get_xid()
        # if title is not None and help_file is not None:
        #     self.viewhelp = ViewHelp(title, help_file, self.window_xid)
        #     self.viewhelp.show()
        try:
            self._help_panel.set_connected(
                utils.nm_status() == 'network-wireless-connected')
        except Exception as e:
            _logger.error('Could not read NM status: %s' % (e))
            self._help_panel.set_connected(False)

        if self.help_palette:
            # FIXME: is_up() is always returning False, so we
            # "debounce" using help_panel_visible.
            if not self.help_palette.is_up() and not self.help_panel_visible:
                self.help_palette.popup(immediate=True)
                self.help_panel_visible = True
            else:
                self.help_palette.popdown(immediate=True)
                self.help_panel_visible = False
                self._help_button.set_expanded(False)

    def add_badge(self, msg, icon="training-trophy", name="Sugar Labs Academy"):
        sugar_icons = os.path.join(os.path.expanduser('~'), '.icons')
        if not os.path.exists(sugar_icons):
            try:
                subprocess.call(['mkdir', sugar_icons])
            except OSError as e:
                _logger.error('Could not mkdir %s, %s' % (sugar_icons, e))

        badge = {
            'icon': icon,
            'from': name,
            'message': msg
        }

        # Use icons from html-content directory since default colors are
        # intended for white background.
        icon_dir = os.path.join(self.bundle_path, 'html-content', 'images')
        icon_path = os.path.join(icon_dir, icon + '.svg')
        try:
            subprocess.call(['cp', icon_path, sugar_icons])
        except OSError as e:
            _logger.error('Could not copy %s to %s, %s' %
                          (icon_path, sugar_icons, e))

        if 'comments' in self.metadata:
            comments = json.loads(self.metadata['comments'])
            comments.append(badge)
            self.metadata['comments'] = json.dumps(comments)
        else:
            self.metadata['comments'] = json.dumps([badge])

    def remove_alert_cb(self, alert, response_id=None):
        self.remove_alert(alert)

    def _dos_fsck_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            _logger.debug('dos_fsck: looking for mount for %s' %
                          self.volume_data[0]['usb_path'])
            target = utils.get_device_path(self.volume_data[0]['usb_path'])
            if target is not None:
                _logger.error('running dosfsck -a %s' % target)
                utils.dos_fsck(target)
                utils.unmount(self.volume_data[0]['usb_path'])

                alert = ConfirmationAlert()
                alert.props.title = _('The USB filesystem has been checked')
                alert.props.msg = \
                    _('Please remove and reinsert your USB.')
                alert.connect('response', self._close_alert_cb)
                self.add_alert(alert)
                self._load_intro_graphics(file_name='reinsert-usb.html')

    def _close_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            self.close()

    def _reboot_alert_cb(self, alert, response_id):
        self.remove_alert(alert)
        if response_id is Gtk.ResponseType.OK:
            try:
                utils.reboot()
            except Exception as e:
                _logger.error('Cannot reboot: %s' % e)

    def _mount_added_cb(self, volume_monitor, device):
        _logger.error('mount added')
        if self.check_volume_data():
            _logger.debug('launching')
            self._launcher()

    def _mount_removed_cb(self, volume_monitor, device):
        _logger.error('mount removed')
        if self.check_volume_data():
            _logger.debug('launching')
            self._launcher()
