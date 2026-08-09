#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk as GTK

DLG_WIDTH = 512
DLG_HEIGHT = 144


class TimerDialog:
    def __init__(self, parent):
        self.parent = parent
        self.seconds = 0
        self.duration = 0
        self.shown = False
        self.response = None

        self.dialog = GTK.Dialog(
            transient_for=self.parent,
            modal=True
        )

        self.dialog.set_default_size(DLG_WIDTH, DLG_HEIGHT)
        self.dialog.set_resizable(False)
        self.dialog.set_deletable(False)

        content = self.dialog.get_content_area()
        content.get_style_context().add_class("timer-dialog-content")

        self.label = GTK.Label()
        self.label.get_style_context().add_class("timer-dialog-label")
        content.add(self.label)

        self.progress = GTK.ProgressBar()
        self.progress.get_style_context().add_class("timer-dialog-progress")
        content.add(self.progress)

        self.btn_cancel = self.dialog.add_button(
            "Cancel",
            GTK.ResponseType.CANCEL
        )

        self.btn_execute = self.dialog.add_button(
            "Execute",
            GTK.ResponseType.ACCEPT
        )

        self.dialog.connect("response", self.on_response)

    def show(self, title, prompt, seconds):
        self.title = title
        self.prompt = prompt
        self.seconds = seconds
        self.duration = seconds
        self.shown = True
        self.response = None

        self.dialog.set_title(self.title)
        # self.label.set_text(self.prompt)
        self.label.set_text(self.prompt.format(seconds = self.seconds))
        self.progress.set_fraction(1.0)

        self.dialog.show_all()

    def update(self, seconds):
        self.seconds = seconds
        self.label.set_text(self.prompt.format(seconds=self.seconds))

        if self.duration > 0:
            self.progress.set_fraction(self.seconds / self.duration)

    def on_response(self, dialog, response):
        self.response = response
        self.dialog.hide()

    def reset(self):
        self.shown = False
        self.response = None