#!/usr/bin/env python3
"""Cinnamon/XApp panel icon support for a running PowerTimer timer."""

import gettext

import gi

from appinfo import ACTIVE_ICON, APP_INFO

gi.require_version("Gtk", "3.0")
gi.require_version("XApp", "1.0")

from gi.repository import Gtk as GTK
from gi.repository import XApp

# Short alias for gettext: marks Python strings for translation.
_ = gettext.gettext

class TrayIcon:
    """Own the Cinnamon panel icon without exposing XApp details to main.py."""

    def __init__(self, restore_callback, quit_callback):
        # XApp is Linux Mint's cross-desktop library.  Its StatusIcon is the
        # Cinnamon-aware replacement for GTK 3's deprecated Gtk.StatusIcon:
        # it publishes the icon to Cinnamon's XApp Status Applet and lets the
        # panel render it.  XApp can provide a Gtk.StatusIcon fallback itself
        # when no XApp panel handler is available, so the application never has
        # to use the deprecated GTK API directly.
        #
        # A StatusIcon is not a widget inside our main window.  It represents
        # this application in the desktop panel and stays alive while this
        # object has a reference to it.  It starts hidden because PowerTimer
        # only has a panel presence while its timer is running.
        self.status_icon = XApp.StatusIcon.new_with_name("powertimer")
        self.status_icon.set_icon_name(str(ACTIVE_ICON))
        self.status_icon.set_visible(False)

        self.restore_callback = restore_callback
        self.quit_callback = quit_callback

        self.menu = GTK.Menu()
        restore_item = GTK.MenuItem.new_with_label(_("Restore window"))
        quit_item = GTK.MenuItem.new_with_label(_("Quit"))

        # GtkMenuItem emits its "activate" signal after the user selects it.
        # These callbacks deliberately call back into main.py: that keeps the
        # normal window and quit behaviour in one place rather than duplicating
        # it in Cinnamon-specific code.
        restore_item.connect("activate", self._on_restore)
        quit_item.connect("activate", self._on_quit)
        self.menu.append(restore_item)
        self.menu.append(quit_item)
        self.menu.show_all()

        # XApp manages panel clicks for us.  Assigning the menu as the primary
        # menu makes a normal (left) click on the panel icon open this GtkMenu
        # at the correct panel position.  The same menu is supplied for a
        # secondary click so every panel click presents the same two actions.
        self.status_icon.set_primary_menu(self.menu)
        self.status_icon.set_secondary_menu(self.menu)

    def show(self, action, seconds):
        """Show the active icon and its initial remaining-time tooltip."""
        self.update(action, seconds)
        self.status_icon.set_visible(True)


    def update(self, action, seconds):
        """Update the tooltip from main.py's existing countdown value."""
        hours, remaining_seconds = divmod(max(seconds, 0), 3600)
        minutes, seconds = divmod(remaining_seconds, 60)

        action_name = {
            "shutdown": _("Shutdown"),
            "restart": _("Restart"),
            "logout": _("Logout"),
            "suspend": _("Suspend"),
            "hibernate": _("Hibernate"),
        }.get(action, action)

        # The tooltip belongs to the XApp StatusIcon, rather than the main
        # window. main.py calls this once per existing timer tick, so this
        # display follows that single timer and does not calculate time itself.
        tooltip = _("{appname} - {action} in {hh:02d}:{nn:02d}:{ss:02d}").format(
            appname= APP_INFO.name,
            action=action_name,
            hh=hours,
            nn=minutes,
            ss=seconds
        )

        self.status_icon.set_tooltip_text(tooltip)


    def hide(self):
        # Hiding tells Cinnamon's XApp Status Applet to remove the panel icon.
        # The Python object is retained so a later timer can reuse it and its
        # already-connected menu callbacks safely.
        self.status_icon.set_visible(False)

    def _on_restore(self, _menu_item):
        self.restore_callback()

    def _on_quit(self, _menu_item):
        self.quit_callback()
