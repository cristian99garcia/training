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

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import WebKit2 

from sugar3.graphics import style
from sugar3.graphics.icon import Icon
from sugar3.graphics.toolbutton import ToolButton

import logging
_logger = logging.getLogger('training-activity-graphics')

# Repeated font sizes at the end to enable web graphics to continue to scale
FONT_SIZES = ['xx-small', 'x-small', 'small', 'medium', 'large', 'large',
              'x-large', 'x-large', 'x-large', 'xx-large', 'xx-large',
              'xx-large']

ZOOM_ORIGINAL = style.zoom(100*100 / 72) / 100.0
class Graphics(Gtk.Alignment):
    ''' An aligned grid in a scrolling window '''

    def __init__(self, width=None, height=None):
        Gtk.Alignment.__init__(self)

        if width is None:
            width = Gdk.Screen.width() - style.GRID_CELL_SIZE
        if height is None:
            height = Gdk.Screen.height() - style.GRID_CELL_SIZE * 3
        self.set_size_request(width, height)

        self.set(0.5, 0, 0, 0)

        self._grid = Gtk.Grid()
        self._grid.set_row_spacing(style.DEFAULT_SPACING)
        self._grid.set_column_spacing(style.DEFAULT_SPACING)
        self._grid.set_border_width(style.DEFAULT_SPACING * 2)
        self.add(self._grid)
        self._grid.show()

        self._row = 0
        self._web_view = None

    def _attach(self, widget):
        self._grid.attach(widget, 0, self._row, 5, 1)
        self._row += 1

    def _attach_two(self, widget1, widget2):
        alignment = Gtk.Alignment.new(0, 0.5, 0, 0)
        alignment.add(widget1)
        self._grid.attach(alignment, 0, self._row, 2, 1)
        alignment.show()
        self._grid.attach(widget2, 3, self._row, 2, 1)
        self._row += 1

    def _attach_three(self, widget1, widget2, widget3):
        alignment = Gtk.Alignment.new(0, 0.5, 0, 0)
        alignment.add(widget1)
        self._grid.attach(alignment, 0, self._row, 3, 1)
        alignment.show()
        self._grid.attach(widget2, 3, self._row, 1, 1)
        self._grid.attach(widget3, 4, self._row, 1, 1)
        self._row += 1

    def _attach_four(self, widget1, widget2, widget3, widget4):
        alignment = Gtk.Alignment.new(0, 0.5, 0, 0)
        alignment.add(widget1)
        self._grid.attach(alignment, 1, self._row, 1, 1)
        alignment.show()
        alignment = Gtk.Alignment.new(0, 0.5, 0, 0)
        alignment.add(widget2)
        self._grid.attach(alignment, 3, self._row, 1, 1)
        alignment.show()

        self._row += 1
        self._grid.attach(widget3, 1, self._row, 1, 1)
        self._grid.attach(widget4, 3, self._row, 1, 1)
        self._row += 1

    def _attach_center(self, widget):
        self._grid.attach(widget, 2, self._row, 1, 1)
        self._row += 1

    def add_icon(self, icon_name, stroke=style.COLOR_BUTTON_GREY.get_svg(),
                 fill=style.COLOR_TRANSPARENT.get_svg(),
                 icon_size=style.XLARGE_ICON_SIZE):
        icon = Icon(pixel_size=icon_size, icon_name=icon_name,
                    stroke_color=stroke, fill_color=fill)
        self._attach(icon)
        icon.show()

    def add_text(self, text, color=style.COLOR_BLACK.get_html(),
                 size='large', bold=False, justify=Gtk.Justification.LEFT):
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(justify)
        if bold:
            text = '<b>' + text + '</b>'
        span = '<span foreground="%s" size="%s">' % (color, size)
        label.set_markup(span + text + '</span>')
        self._attach(label)
        label.show()

    def add_text_and_icon(self, text, icon_name, size='large', bold=False,
                          color=style.COLOR_BLACK.get_html(),
                          justify=Gtk.Justification.LEFT,
                          stroke=style.COLOR_BUTTON_GREY.get_svg(),
                          fill=style.COLOR_TRANSPARENT.get_svg(),
                          icon_size=style.XLARGE_ICON_SIZE):
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(justify)
        if bold:
            text = '<b>' + text + '</b>'
        span = '<span foreground="%s" size="%s">' % (color, size)
        label.set_markup(span + text + '</span>')

        icon = Icon(pixel_size=icon_size, icon_name=icon_name,
                    stroke_color=stroke, fill_color=fill)

        self._attach_two(label, icon)
        label.show()
        icon.show()

    def add_text_icon_and_button(self, text, icon_name,
                                 button_icon=None,
                                 button_label=None,
                                 size='large', bold=False,
                                 color=style.COLOR_BLACK.get_html(),
                                 justify=Gtk.Justification.LEFT,
                                 stroke=style.COLOR_BUTTON_GREY.get_svg(),
                                 fill=style.COLOR_TRANSPARENT.get_svg(),
                                 icon_size=style.XLARGE_ICON_SIZE):
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_justify(justify)
        if bold:
            text = '<b>' + text + '</b>'
        span = '<span foreground="%s" size="%s">' % (color, size)
        label.set_markup(span + text + '</span>')

        icon = Icon(pixel_size=icon_size, icon_name=icon_name,
                    stroke_color=stroke, fill_color=fill)

        if button_icon is not None:
            button = ToolButton(button_icon)
        else:
            button = Gtk.Button()
            button.set_label(button_label)
        self._attach_three(label, icon, button)
        label.show()
        icon.show()
        button.show()
        return button

    def add_uri(self, uri, height=610):
        self._web_view = WebKit2.WebView()
        width = Gdk.Screen.width() - style.GRID_CELL_SIZE
        height = int(height * Gdk.Screen.height() / 900.)
        self._web_view.set_size_request(width, height)
        self._web_view.set_zoom_level(ZOOM_ORIGINAL)
        self._web_view.load_uri(uri)
        self._attach(self._web_view)
        self._web_view.show()
        return self._web_view

    def set_zoom_level(self, zoom_level):
        if self._web_view is not None:
            self._web_view.set_zoom_level(zoom_level)

    def add_entry(self, text=''):
        entry = Gtk.Entry()
        offset = style.GRID_CELL_SIZE
        entry.set_size_request(offset * 8, -1)
        entry.set_text(text)
        self._attach_center(entry)
        entry.show()
        return entry

    def add_two_entries(self, labeltext1='', text1='', labeltext2='', text2=''):
        offset = style.GRID_CELL_SIZE
        size = 'large'
        color = style.COLOR_BLACK.get_html()
        justify = Gtk.Justification.LEFT

        label1 = Gtk.Label()
        label1.set_use_markup(True)
        label1.set_justify(justify)
        span = '<span foreground="%s" size="%s">' % (color, size)
        label1.set_markup(span + labeltext1 + '</span>')

        entry1 = Gtk.Entry()
        entry1.set_size_request(offset * 4, -1)
        entry1.set_text(text1)

        label2 = Gtk.Label()
        label2.set_use_markup(True)
        label2.set_justify(justify)
        span = '<span foreground="%s" size="%s">' % (color, size)
        label2.set_markup(span + labeltext2 + '</span>')

        entry2 = Gtk.Entry()
        entry2.set_size_request(offset * 4, -1)
        entry2.set_text(text2)

        self._attach_four(label1, label2, entry1, entry2)

        label1.show()
        label2.show()
        entry1.show()
        entry2.show()
        return entry1, entry2

    def add_image(self, image):
        image = Gtk.Image.new_from_file(image)
        self._attach(image)
        image.show()

    def add_two_images(self, left_image, right_image):
        alignments = [Gtk.Alignment.new(0, 0, 0, 0),
                      Gtk.Alignment.new(1.0, 0, 0, 0)]
        left = Gtk.Image.new_from_file(left_image)
        right = Gtk.Image.new_from_file(right_image)
        alignments[0].add(left)
        left.show()
        alignments[1].add(right)
        right.show()
        self._grid.attach(alignments[0], 0, self._row, 2, 1)
        alignments[0].show()
        self._grid.attach(alignments[1], 3, self._row, 2, 1)
        alignments[1].show()
        self._row += 1
        return alignments

    def add_button(self, button_label, callback, arg=None, button_icon=None):
        if button_icon is not None:
            button = ToolButton(button_icon)
        else:
            button = Gtk.Button()
            button.set_label(button_label)
        self._attach_center(button)
        if callback is not None:
            if arg is None:
                button.connect('clicked', callback)
            else:
                button.connect('clicked', callback, arg)
        button.show()
        return button

    def add_yes_no_buttons(self, callback):
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(style.DEFAULT_SPACING * 2)
        grid.set_column_homogeneous(True)
        yesbutton = Gtk.Button()
        yesbutton.set_label(_('Yes'))
        nobutton = Gtk.Button()
        nobutton.set_label(_('No'))
        grid.attach(yesbutton, 0, 0, 1, 1)
        yesbutton.connect('clicked', callback, 'yes')
        yesbutton.show()
        grid.attach(nobutton, 1, 0, 1, 1)
        nobutton.connect('clicked', callback, 'no')
        nobutton.show()
        self._attach_center(grid)
        grid.show()
        return [yesbutton, nobutton]

    def add_radio_buttons(self, button_icons, colors=None):
        # Psuedo-radio buttons
        alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(style.DEFAULT_SPACING * 2)
        buttons = []
        for i, button_icon in enumerate(button_icons):
            if colors is not None:
                icon = Icon(pixel_size=style.STANDARD_ICON_SIZE,
                            icon_name=button_icon,
                            stroke_color=colors.get_stroke_color(),
                            fill_color=colors.get_fill_color())
            else:
                icon = Icon(pixel_size=style.STANDARD_ICON_SIZE,
                            icon_name=button_icon)

            buttons.append(Gtk.Button())
            buttons[i].set_image(icon)
            icon.show()
            grid.attach(buttons[i], i, 0, 1, 1)
            buttons[i].show()

        alignment.add(grid)
        grid.show()
        self._attach(alignment)
        alignment.show()

        return buttons

    def add_list_buttons(self, button_names):
        # Psuedo-selection-list buttons
        alignment = Gtk.Alignment.new(0.5, 0.5, 0, 0)
        grid = Gtk.Grid()
        grid.set_row_spacing(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_border_width(style.DEFAULT_SPACING * 2)

        buttons = []
        x = 0
        y = 0
        # for i, button_name in enumerate(button_names[0:-1]):
        for i, button_name in enumerate(button_names):
            buttons.append(Gtk.Button(button_name, name='select-button'))
            grid.attach(buttons[i], x, y, 1, 1)
            x += 1
            if x == 2:
                x = 0
                y += 1
            buttons[i].show()
        '''
        buttons.append(Gtk.Button(button_names[-1], name='select-button'))
        grid.attach(buttons[-1], 0, y + 1, 2, 1)
        buttons[-1].show()
        '''

        alignment.add(grid)
        grid.show()
        self._attach(alignment)
        alignment.show()

        return buttons
