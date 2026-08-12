#!/usr/bin/env python3

import gettext

import gi

gi.require_version("Gtk", "3.0")

gi.require_version("GdkPixbuf", "2.0")

from gi.repository import GdkPixbuf
from gi.repository import Gtk as GTK

# Short alias for gettext: marks Python strings for translation.
_ = gettext.gettext


class AboutBox:
    """
    Displays application information using GTK's standard AboutDialog.

    The GTK dialog is created when show() is called and destroyed again
    after it is closed.
    """

    def __init__(self, parent, app_info):
        self.parent = parent
        self.app_info = app_info


    def show(self, *_args):
        """Create, display and destroy the GTK AboutDialog."""

        dialog = GTK.AboutDialog(
            transient_for=self.parent,
            modal=True
        )

        dialog.set_title(_("About"))
        dialog.set_program_name(self.app_info.name)
        dialog.set_version(f"V{self.app_info.version}")
        dialog.set_comments(self.app_info.description)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(self.app_info.icon),
            96,
            96,
            True
        )

        dialog.set_logo(pixbuf)

        if self.app_info.website:
            dialog.set_website(self.app_info.website)

        if self.app_info.license:
            dialog.set_license(self.app_info.license)
            dialog.set_wrap_license(True)

        dialog.run()
        dialog.destroy()