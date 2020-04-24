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
import subprocess
import dbus
import stat

import glob
import urllib.request, urllib.parse, urllib.error
from random import uniform
import tempfile
import cairo
import email.utils
import re
import time

from gi.repository import Vte
from gi.repository import Gio
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio 
from gi.repository import GObject

from sugar3 import env
from sugar3 import profile
from sugar3.datastore import datastore
from sugar3.graphics.xocolor import XoColor

from jarabe import config
from jarabe.model import shell

import logging
_logger = logging.getLogger('training-activity-testutils')

_user_extensions_path = os.path.join(env.get_profile_path(), 'extensions')

_STATUS_CHARGING = 0
_STATUS_DISCHARGING = 1
_STATUS_FULLY_CHARGED = 2
_STATUS_NOT_PRESENT = 3

_UP_DEVICE_IFACE = 'org.freedesktop.UPower.Device'

_UP_TYPE_BATTERY = 2

_UP_STATE_UNKNOWN = 0
_UP_STATE_CHARGING = 1
_UP_STATE_DISCHARGING = 2
_UP_STATE_EMPTY = 3
_UP_STATE_FULL = 4
_UP_STATE_CHARGE_PENDING = 5
_UP_STATE_DISCHARGE_PENDING = 6

_WARN_MIN_PERCENTAGE = 15

_MINIMUM_SPACE = 1024 * 1024 * 10

_DBUS_SERVICE = 'org.sugarlabs.SugarServices'
_DBUS_SHELL_IFACE = 'org.sugarlabs.SugarServices'
_DBUS_PATH = '/org/sugarlabs/SugarServices'

volume_monitor = None
battery_model = None
proxy = None

TRAINING_DATA = 'training-data-%s'
TRAINING_SUFFIX = '.txt'


def is_valid_email_entry(entry):
    if len(entry) == 0:
        return False
    realname, email_address = email.utils.parseaddr(entry)
    if email_address == '':
        return False
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email_address):
        return False
    return True


def recently(time):
    return time - (60 * 60)  # within the hour


def get_log_file(bundle_id):
    log_dir = os.path.join(env.get_profile_path(), 'logs')
    log_files = glob.glob(os.path.join(log_dir, '%s*.log' % bundle_id))
    if len(log_files) > 0:
        sorted_log_files = sorted(log_files)
        return sorted_log_files[-1]
    else:
        return None


def take_screen_shot():
    tmp_dir = os.path.join(env.get_profile_path(), 'data')
    fd, file_path = tempfile.mkstemp(dir=tmp_dir, suffix='.png')
    os.close(fd)

    window = Gdk.get_default_root_window()
    width, height = window.get_width(), window.get_height()

    screenshot_surface = Gdk.Window.create_similar_surface(
        window, cairo.CONTENT_COLOR, width, height)

    cr = cairo.Context(screenshot_surface)
    Gdk.cairo_set_source_window(cr, window, 0, 0)
    cr.paint()
    screenshot_surface.write_to_png(file_path)
    return file_path


def reboot():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        try:
            proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
        except Exception as e:
            _logger.error('ERROR rebooting Sugar (proxy): %s' % e)
            _vte_reboot()
    try:
        dbus.Interface(proxy, _DBUS_SERVICE).Reboot()
    except Exception as e:
        _logger.error('ERROR rebooting Sugar: %s' % e)
        _vte_reboot()


def _vte_reboot():
        _logger.error('Trying VTE method...')
        # If we cannot reboot using the Sugar service, try from a VT
        vt = Vte.Terminal()
        success_, pid = vt.fork_command_full(
            Vte.PtyFlags.DEFAULT,
            os.environ["HOME"],
            ['/usr/bin/sudo', '/usr/sbin/reboot'],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None)
        _logger.error('VTE %s %s' % (str(success_), str(pid)))


def look_for_file_type(path, suffix):
    return glob.glob(os.path.join(path, '*' + suffix))


def check_volume_suffix(volume_file):
    _logger.debug('check_volume_suffix %s' % (volume_file))
    if volume_file.endswith(TRAINING_SUFFIX):
        _logger.debug('return %s' % (TRAINING_DATA % volume_file[-13:]))
        return TRAINING_DATA % volume_file[-13:]
    elif volume_file.endswith('.bin'):  # See SEP-33
        new_volume_file = volume_file[:-4] + TRAINING_SUFFIX
        print(new_volume_file)
        os.rename(volume_file, new_volume_file)
        _logger.debug('return %s' % (TRAINING_DATA % new_volume_file[-13:]))
        return TRAINING_DATA % new_volume_file[-13:]
    else:  # No suffix
        _logger.debug('NO SUFFIX: %s' % volume_file)
        new_volume_file = volume_file + TRAINING_SUFFIX
        _logger.debug(new_volume_file)
        os.rename(volume_file, new_volume_file)
        _logger.debug('return %s' % (TRAINING_DATA % new_volume_file[-13:]))
        return TRAINING_DATA % new_volume_file[-13:]


def look_for_training_data(path):
    ''' look for .txt suffix, .bin suffix, and finally, no suffix '''
    training_data = []
    glob_data = glob.glob(os.path.join(path, 'training-data-*.txt'))
    for path in glob_data:
        # Ignore files starting with # or ending with ~
        if path[0] == '#':
            continue
        if path[-1] == '~':
            continue
        training_data.append(path)
    glob_data = glob.glob(os.path.join(path, 'training-data-*.bin'))
    for path in glob_data:
        # Ignore files starting with # or ending with ~
        if path[0] == '#':
            continue
        if path[-1] == '~':
            continue
        training_data.append(path)
    glob_data = glob.glob(os.path.join(path, 'training-data-*'))
    for path in glob_data:
        # Ignore files starting with # or ending with ~
        if path[0] == '#':
            continue
        if path[-1] == '~':
            continue
        # Make sure we are not adding the same file twice
        if path in training_data:
            continue
        training_data.append(path)
    return training_data


def get_email_from_training_data(path):
    try:
        fd = open(path, 'r')
        json_data = fd.read()
        fd.close()
    except Exception as e:
        _logger.error('Could not read from %s: %s' % (path, e))
        return None
    try:
        if len(json_data) > 0:
            data = json.loads(json_data)
        else:
            return None
    except ValueError as e:
        _logger.error('Cannot read training data: %s' % e)
        return None
    if 'email_address' in data:
        return data['email_address']
    else:
        return None


def get_name_from_training_data(path):
    try:
        fd = open(path, 'r')
        json_data = fd.read()
        fd.close()
    except Exception as e:
        _logger.error('Could not read from %s: %s' % (path, e))
        return None
    try:
        if len(json_data) > 0:
            data = json.loads(json_data)
        else:
            return None
    except ValueError as e:
        _logger.error('Cannot read training data: %s' % e)
        return None
    if 'name' in data:
        return data['name'].replace(',', ' ')
    else:
        return None


def get_completed_from_training_data(path):
    try:
        fd = open(path, 'r')
        json_data = fd.read()
        fd.close()
    except Exception as e:
        _logger.error('Could not read from %s: %s' % (path, e))
        return None
    try:
        if len(json_data) > 0:
            data = json.loads(json_data)
        else:
            return None
    except ValueError as e:
        _logger.error('Cannot read training data: %s' % e)
        return None
    if 'completion_percentage' in data:
        return data['completion_percentage']
    else:
        return None


def look_for_xlw(path):
    return glob.glob(os.path.join(path, '*.xlw'))


def look_for_xls(path):
    return glob.glob(os.path.join(path, '*.xls'))


def remove_xlw_suffix(path):
    if os.path.exists(path):
        if path[-4:] == '.xlw':
            results = subprocess.check_output(['mv', path, path[:-4]])


def set_read_write(path):
    if os.path.exists(path):
        # results = subprocess.check_output(['chmod', '+w', path])
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)


def unexpected_training_data_files(path, name):
    ''' There should be at most one file training-data-XXXX-XXXX and it should
        match the volume path basename. '''
    files = look_for_training_data(path)
    if len(files) > 1:
        _logger.error(files)
        return True
    if len(files) == 1 and not os.path.exists(os.path.join(path, name)):
        _logger.error(files)
        return True
    return False


def is_full(path, required=_MINIMUM_SPACE):
    ''' Make sure we have some room to write our data '''
    volume_status = os.statvfs(path)
    free_space = volume_status[os.statvfs.F_BSIZE] * \
                 volume_status[os.statvfs.F_BAVAIL]



    _logger.debug('free space: %d MB' % int(free_space / (1024 * 1024)))
    if free_space < required:
        _logger.error('free space: %d MB' % int(free_space / (1024 * 1024)))
        return True
    return False


def is_writeable(path):
    ''' Make sure we can write to the data file '''
    if not os.path.exists(path):
        return False
    stats = os.stat(path)
    if (stats.st_uid == os.geteuid() and stats.st_mode & stat.S_IWUSR) or \
       (stats.st_gid == os.getegid() and stats.st_mode & stat.S_IWGRP) or \
       (stats.st_mode & stat.S_IWOTH):
        return True
    return False


def is_landscape():
    return Gdk.Screen.width() > Gdk.Screen.height()


def get_safe_text(text):
    return urllib.request.pathname2url(text.encode('ascii', 'xmlcharrefreplace'))


def get_battery_level():
    global battery_model
    if battery_model is None:
        bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
        up_proxy = bus.get_object('org.freedesktop.UPower',
                                  '/org/freedesktop/UPower')
        upower = dbus.Interface(up_proxy, 'org.freedesktop.UPower')

        for device_path in upower.EnumerateDevices():
            device = bus.get_object('org.freedesktop.UPower', device_path)
            device_prop_iface = dbus.Interface(device, dbus.PROPERTIES_IFACE)
            device_type = device_prop_iface.Get(_UP_DEVICE_IFACE, 'Type')
            if device_type == _UP_TYPE_BATTERY:
                battery_model = DeviceModel(device)

    return battery_model.props.level


def get_sound_level():
    settings  = Gio.Settings('org.sugarlabs.sound') 
    return settings.get_int('volume')


def is_clipboard_text_available():
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    text_view = Gtk.TextView()
    text_buffer = text_view.get_buffer()
    text_buffer.paste_clipboard(clipboard, None, True)
    bounds = text_buffer.get_bounds()

    return len(text_buffer.get_text(bounds[0], bounds[1], True)) > 0


def get_volume_names():
    global volume_monitor
    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    names = []
    for mount in volume_monitor.get_mounts():
        names.append(mount.get_name())

    return names


def generate_uid(left=None):
    if left is None:
        left = '%04x' % int(uniform(0, int(0xFFFF)))
    right = '%04x' % int(uniform(0, int(0xFFFF)))
    uid = '%s-%s' % (left, right)
    return uid.upper()


def format_volume_name(name):
    ''' Looking for XXXX-XXXX format '''

    def is_hex(string):
        for c in string.upper():
            if not c in '0123456789ABCDEF':
                return False
        return True

    if not '-' in name:
        return generate_uid()
    hex_strings = name.split('-')
    if len(hex_strings) != 2:
        return generate_uid()
    if len(hex_strings[0]) != 4:
        return generate_uid()
    if not is_hex(hex_strings[0]):
        return generate_uid()
    if len(hex_strings[1]) < 4:
        return generate_uid(hex_strings[0])
    if not is_hex(hex_strings[0]):
        return generate_uid(hex_strings[0])
    return name[0:9]


def get_modified_time(path):
    try:
        return int(os.path.getmtime(path))
    except OSError as e:
        logging.error('Could not get modified time for %s: %s' % (path, e))
        return time.time()


def unmount(path):
    global volume_monitor

    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    target = None
    for mount in volume_monitor.get_mounts():
        if mount.get_root().get_path() == path:
            target = mount
            break

    def __unmount_cb(mount, result, user_data):
        logging.debug('__unmount_cb %r %r', mount, result)
        mount.unmount_with_operation_finish(result)

    if target is not None:
        _logger.debug('unmounting %s' % path)
        target.unmount_with_operation(0, None, None, __unmount_cb, None)


def get_volume_paths():
    global volume_monitor
    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    paths = []
    for mount in volume_monitor.get_mounts():
        paths.append(mount.get_root().get_path())

    return paths


def get_device_path(target):
    # There must be a Gio.VolumeMonitor way of doing this
    results = subprocess.check_output(['df']).split('\n')
    for line in results:
        mount = line.split(' ')
        if mount[-1] == target:
            return mount[0]
    return None


def dos_fsck(target):
    _logger.error('Using VTE to dosfsck -a %s' % target)
    vt = Vte.Terminal()
    success_, pid = vt.fork_command_full(
        Vte.PtyFlags.DEFAULT,
        os.environ["HOME"],
        ['/usr/bin/sudo', '/usr/sbin/dosfsck', '-a', target],
        [],
        GLib.SpawnFlags.DO_NOT_REAP_CHILD,
        None,
        None)
    _logger.error('VTE %s %s' % (str(success_), str(pid)))


def get_number_of_mounted_volumes():
    global volume_monitor
    if volume_monitor is None:
        volume_monitor = Gio.VolumeMonitor.get()

    return len(volume_monitor.get_mounts())


def _get_dmi(node):
    ''' The desktop management interface should be a reliable source
    for product and version information. '''
    path = os.path.join('/sys/class/dmi/id', node)
    try:
        return open(path).readline().strip()
    except:
        return None


def is_XO():
    version = _get_dmi('product_version')
    if version is None:
        hwinfo_path = '/bin/olpc-hwinfo'
        if os.path.exists(hwinfo_path) and os.access(hwinfo_path, os.X_OK):
            model = subprocess.check_output([hwinfo_path, 'model'])
            version = model.strip()
    if version in ['1', '1.5', '1.75', '4']:
        return True
    else:
        # Some systems (e.g. ARM) don't have dmi info
        if os.path.exists('/sys/devices/platform/lis3lv02d/position'):
            return True
        elif os.path.exists('/etc/olpc-release'):
            return True
    return False


def is_game_key(keyname):
    if keyname in ['KP_Up', 'KP_Down', 'KP_Left', 'KP_Right',
                   'KP_Page_Down', 'KP_Page_Up', 'KP_End', 'KP_Home']:
        return True
    else:
        return False


def is_tablet_mode():
    if not os.path.exists('/dev/input/event4'):
        return False
    try:
        output = subprocess.call(
            ['evtest', '--query', '/dev/input/event4', 'EV_SW',
             'SW_TABLET_MODE'])
    except (OSError, subprocess.CalledProcessError):
        return False
    if str(output) == '10':
        return True
    return False


def is_expanded(toolbar_button):
    return toolbar_button.is_expanded()


def is_fullscreen(activity):
    return activity._is_fullscreen


def get_starred():
    dsobjects, nobjects = datastore.find({'keep': '1'})
    return dsobjects


def get_starred_count():
    dsobjects, nobjects = datastore.find({'keep': '1'})
    return nobjects


def get_description(activity):
    if 'description' in activity.metadata:
        return activity.metadata['description']
    else:
        return ''


def get_title(activity):
    if 'title' in activity.metadata:
        return activity.metadata['title']
    else:
        return ''


def get_sugarservices_version():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        try:
            proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
        except Exception as e:
            _logger.error('ERROR getting sugarservice service: %s' % e)
            return 0
    try:
        return dbus.Interface(proxy, _DBUS_SERVICE).GetVersion()
    except Exception as e:
        _logger.error('ERROR getting sugarservice version: %s' % e)
        return 0


def is_activity_open(bundle_name):
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        return \
            dbus.Interface(proxy, _DBUS_SERVICE).GetActivityName() == \
            bundle_name and is_activity_view()
    except Exception as e:
        _logger.error('ERROR getting activity name %s' % e)
        return False


def is_journal_open():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        return dbus.Interface(proxy, _DBUS_SERVICE).IsJournal() and \
            is_activity_view()
    except Exception as e:
        _logger.error('ERROR getting zoom level %s' % e)
        return False


def is_activity_view():
    """
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        zoom_level = \
            dbus.Interface(proxy, _DBUS_SERVICE).GetZoomLevel()
    except Exception, e:
        _logger.error('ERROR getting zoom level %s' % e)
        return False

    return zoom_level == shell.ShellModel.ZOOM_ACTIVITY
    """
    return True


def is_home_view():
    """
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        zoom_level = \
            dbus.Interface(proxy, _DBUS_SERVICE).GetZoomLevel()
    except Exception, e:
        _logger.error('ERROR getting zoom level %s' % e)
        return False

    return zoom_level == shell.ShellModel.ZOOM_HOME
    """
    return True


def is_neighborhood_view():
    """
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        zoom_level = \
            dbus.Interface(proxy, _DBUS_SERVICE).GetZoomLevel()
    except Exception, e:
        _logger.error('ERROR getting zoom level %s' % e)
        return False

    return zoom_level == shell.ShellModel.ZOOM_MESH
    """
    return True


def goto_activity_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        dbus.Interface(proxy, _DBUS_SERVICE).SetZoomLevel(
            shell.ShellModel.ZOOM_ACTIVITY)
    except Exception as e:
        _logger.error('ERROR setting zoom level %s' % e)


def goto_journal():
    ''' Actually go to the journal '''
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
    try:
        if dbus.Interface(proxy, _DBUS_SERVICE).OpenJournal():
            dbus.Interface(proxy, _DBUS_SERVICE).SetZoomLevel(
                shell.ShellModel.ZOOM_ACTIVITY)
        else:
            _logger.error('Could not find journal to open???')
    except Exception as e:
        _logger.error('ERROR calling open journal: %s' % e)


def set_journal_active():
    ''' Just set the Journal as the active activity in the Home View '''
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
    try:
        if dbus.Interface(proxy, _DBUS_SERVICE).OpenJournal():
            dbus.Interface(proxy, _DBUS_SERVICE).SetZoomLevel(
                shell.ShellModel.ZOOM_HOME)
        else:
            _logger.error('Could not find journal to open???')
    except Exception as e:
        _logger.error('ERROR calling open journal: %s' % e)


def goto_home_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        dbus.Interface(proxy, _DBUS_SERVICE).SetZoomLevel(
            shell.ShellModel.ZOOM_HOME)
    except Exception as e:
        _logger.error('ERROR setting zoom level %s' % e)


def goto_neighborhood_view():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        dbus.Interface(proxy, _DBUS_SERVICE).SetZoomLevel(
            shell.ShellModel.ZOOM_MESH)
    except Exception as e:
        _logger.error('ERROR setting zoom level %s' % e)


def get_share_scope(activity):
    if 'share-scope' in activity.metadata:
        return activity.metadata['share-scope'] == 'public'
    return False


def saw_new_launch(bundle_id, timestamp):
    for activity in get_activity(bundle_id):
        if get_last_launch_time(activity) > int(timestamp):
            return True
    return False


def saw_new_instance(bundle_id, timestamp):
    for activity in get_activity(bundle_id):
        if get_creation_time(activity) > int(timestamp):
            return True
    return False


def get_creation_time(activity):
    if 'creation_time' in activity.metadata:
        return int(activity.metadata['creation_time'])
    else:
        _logger.error('No creation time found')
        return 0


def get_last_launch_time(activity):
    if 'launch-times' in activity.metadata:
        launch_times = activity.metadata['launch-times'].split(',')
        try:
            return int(launch_times[-1])
        except Exception as e:
            _logger.error('Malformed launch times found: %s' % e)
            return 0
    else:
        # _logger.error('No launch times found')
        return 0


def get_launch_count(activity):
    if 'launch-times' in activity.metadata:
        return len(activity.metadata['launch-times'].split(','))
    else:
        return 0


def get_colors():


    settings = Gio.Settings('org.sugarlabs.user') 
    return XoColor(settings.get_string('color'))


def get_nick():
    return profile.get_nick_name()


def get_favorites():
    favorites_path = env.get_profile_path('favorite_activities')
    if os.path.exists(favorites_path):
        favorites_data = json.load(open(favorites_path))
        favorites_list = favorites_data['favorites']
    return favorites_list


def get_activity(bundle_id):
    dsobjects, nobjects = datastore.find({'activity': [bundle_id]})
    return dsobjects


def get_most_recent_instance(bundle_id):
    dsobjects, nobjects = datastore.find({'activity': [bundle_id]})
    most_recent_time = -1
    most_recent_instance = None
    for activity in dsobjects:
        last_launch_time = get_last_launch_time(activity)
        if last_launch_time > most_recent_time:
            most_recent_time = get_last_launch_time(activity)
            most_recent_instance = activity
    return most_recent_instance


def get_audio():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['audio/ogg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_image():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['image/png',
                                                        'image/jpeg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_png():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['image/png']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_jpg():
    paths = []
    dsobjects, nobjects = datastore.find({'mime_type': ['image/jpeg']})
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_rtf():
    dsobjects, nobjects = datastore.find({'mime_type': ['text/rtf',
                                                        'application/rtf']})
    paths = []
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_pdf():
    dsobjects, nobjects = datastore.find({'mime_type': ['application/pdf']})
    paths = []
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_odt():
    dsobjects, nobjects = datastore.find(
        {'mime_type':
         ['application/vnd.oasis.opendocument.text']})
    paths = []
    for dsobject in dsobjects:
        paths.append(dsobject.file_path)
    return paths


def get_speak_settings(activity):
    file_path = activity.file_path
    try:
        configuration = json.loads(file(file_path, 'r').read())
        status = json.loads(configuration['status'])
    except Exception:
        # Ignore: Speak activity has not yet written out its data.
        return None
    return status


def uitree_dump():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
    try:
        return json.loads(dbus.Interface(proxy, _DBUS_SERVICE).Dump())
    except Exception as e:
        print(('ERROR calling Dump: %s' % e))
        # _logger.error('ERROR calling Dump: %s' % e)
    return ''


def get_uitree_node(name):
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
    try:
        return dbus.Interface(proxy, _DBUS_SERVICE).FindChild(name)
    except Exception as e:
        _logger.error('ERROR calling FindChild: %s' % e)
    return False


def click_uitree_node(name):
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)
    try:
        return dbus.Interface(proxy, _DBUS_SERVICE).Click(name)
    except Exception as e:
        _logger.error('ERROR calling Click: %s' % e)
    return False


def select_list_view():
    # FIXME: hangs interface
    # click_uitree_node('List view')
    _logger.warning('select_list_view is broken')


def select_favorites_view():
    # FIXME: hangs interface
    # click_uitree_node('Favorites view')
    _logger.warning('select_favorites_view is broken')


def find_string(path, string):
    try:
        fd = open(path, 'r')
    except Exception as e:
        # _logger.error('Could not open file at %s: %s' % (path, e))
        return False
    for line in fd:
        if string in line:
            return True
    return False


class DeviceModel(GObject.GObject):
    __gproperties__ = {
        'level': (int, None, None, 0, 100, 0, GObject.PARAM_READABLE),
        'time-remaining': (int, None, None, 0, GLib.MAXINT32, 0,
                           GObject.PARAM_READABLE),  # unit: seconds
        'charging': (bool, None, None, False, GObject.PARAM_READABLE),
        'discharging': (bool, None, None, False, GObject.PARAM_READABLE),
        'present': (bool, None, None, False, GObject.PARAM_READABLE),
    }

    __gsignals__ = {
        'updated': (GObject.SignalFlags.RUN_FIRST, None, ([])),
    }

    def __init__(self, battery):
        GObject.GObject.__init__(self)
        self._battery = battery
        self._battery_props_iface = dbus.Interface(self._battery,
                                                   dbus.PROPERTIES_IFACE)
        self._battery.connect_to_signal('Changed',
                                        self.__battery_properties_changed_cb,
                                        dbus_interface=_UP_DEVICE_IFACE)
        self._fetch_properties_from_upower()

    def _fetch_properties_from_upower(self):
        """Get current values from UPower."""
        # pylint: disable=W0201
        try:
            dbus_props = self._battery_props_iface.GetAll(_UP_DEVICE_IFACE)
        except dbus.DBusException:
            logging.error('Cannot access battery properties')
            dbus_props = {}

        self._level = dbus_props.get('Percentage', 0)
        self._state = dbus_props.get('State', _UP_STATE_UNKNOWN)
        self._present = dbus_props.get('IsPresent', False)
        self._time_to_empty = dbus_props.get('TimeToEmpty', 0)
        self._time_to_full = dbus_props.get('TimeToFull', 0)

    def do_get_property(self, pspec):
        """Return current value of given GObject property."""
        if pspec.name == 'level':
            return self._level
        if pspec.name == 'charging':
            return self._state == _UP_STATE_CHARGING
        if pspec.name == 'discharging':
            return self._state == _UP_STATE_DISCHARGING
        if pspec.name == 'present':
            return self._present
        if pspec.name == 'time-remaining':
            if self._state == _UP_STATE_CHARGING:
                return self._time_to_full
            if self._state == _UP_STATE_DISCHARGING:
                return self._time_to_empty
            return 0

    def get_type(self):
        return 'battery'

    def __battery_properties_changed_cb(self):
        old_level = self._level
        old_state = self._state
        old_present = self._present
        old_time = self.props.time_remaining
        self._fetch_properties_from_upower()
        if self._level != old_level:
            self.notify('level')
        if self._state != old_state:
            self.notify('charging')
            self.notify('discharging')
        if self._present != old_present:
            self.notify('present')
        if self.props.time_remaining != old_time:
            self.notify('time-remaining')

        self.emit('updated')


def nm_status():
    global proxy
    if proxy is None:
        bus = dbus.SessionBus()
        proxy = bus.get_object(_DBUS_SERVICE, _DBUS_PATH)

    try:
        status = dbus.Interface(proxy, _DBUS_SERVICE).NMStatus()
        logging.debug(status)
    except Exception as e:
        _logger.error('ERROR getting NM Status: %s' % e)
        return None

    if status in ['network-wireless-connected',
                  'network-wireless-disconnected',
                  'network-adhoc-1-connected',
                  'network-adhoc-1-disconnected',
                  'network-adhoc-6-connected',
                  'network-adhoc-6-disconnected',
                  'network-adhoc-11-connected',
                  'network-adhoc-11-disconnected']:
        return status
    else:
        return 'unknown'


class Completer(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                if s and s.lower().startswith(text.lower())]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        try:
            return self.matches
        except IndexError:
            return None
