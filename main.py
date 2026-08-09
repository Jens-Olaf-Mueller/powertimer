#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")


from gi.repository import Gdk, GdkPixbuf, GLib
from gi.repository import Gtk as GTK

APP_NAME = "PowerTimer"
timer_seconds = 0
g_timer_id = None

builder = GTK.Builder()
builder.add_from_file("ui/powertimer.ui")

css_provider = GTK.CssProvider()
css_provider.load_from_path("ui/style.css")

screen = Gdk.Screen.get_default()
GTK.StyleContext.add_provider_for_screen(
    screen,
    css_provider,
    GTK.STYLE_PROVIDER_PRIORITY_APPLICATION
)
WINDOW = builder.get_object("winMain")

def msg_box(prompt, title = APP_NAME, buttons = GTK.ButtonsType.OK):
    dialog = GTK.MessageDialog(
        transient_for = WINDOW,
        modal = True,
        message_type = GTK.MessageType.QUESTION,
        title = title,
        buttons = buttons,
        text = prompt
    )

    response = dialog.run()
    dialog.destroy()

    return response in (
        GTK.ResponseType.YES,
        GTK.ResponseType.OK,
        GTK.ResponseType.ACCEPT
    )


# here we gonna toggle the app's icon state and buttons
def toggle_app_state(start=True):
    builder.get_object("btnStart").set_sensitive(not start)
    builder.get_object("btnCancel").set_sensitive(start)

    # Python's ternary operator...
    icon = "icons/active.svg" if start else "icons/idle.svg"

    WINDOW.set_icon_from_file(icon)
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(icon, 36, 36, True)
    builder.get_object("imgStatus").set_from_pixbuf(pixbuf)


# Python timer construct
def on_timer_tick():
    global timer_seconds, timer_id

    timer_seconds -= 1
    print(timer_seconds)

    if timer_seconds <= 0:
        timer_id = None
        toggle_app_state(False)

        print("Timer abgelaufen!")   # TODO: gewählte Aktion ausführen
        return False

    return True # important! → 'True' recalls the method, 'False' stops the timer!


def get_seconds_until(hours, minutes):
    now = datetime.now(timezone.utc).astimezone()

    target = now.replace(
        hour=int(hours),
        minute=int(minutes),
        second=0,
        microsecond=0
    )

    if target <= now:
        target += timedelta(days=1)

    return int((target - now).total_seconds())

def format_time(entry, _event):
    value = int(entry.get_text() or 0)
    entry.set_text(f"{value:02d}")

def validate_time(entry):
    text = entry.get_text()

    if text == "":
        return

    if not text.isdigit():
        entry.set_text("00")
        return

    value = int(text)
    entry_id = GTK.Buildable.get_name(entry)
    maximum = 23 if "Hours" in entry_id else 59

    if value > maximum:
        entry.set_text(str(maximum))
        entry.set_position(-1)


def start_timer(hours, minutes):
    print(f"Timer gestartet für {hours}:{minutes} ...")

    global timer_seconds, g_timer_id
    timer_seconds = get_seconds_until(hours, minutes)
    g_timer_id = GLib.timeout_add_seconds(1, on_timer_tick)
    toggle_app_state()


def stop_timer():
    global g_timer_id

    if g_timer_id is not None:
        GLib.source_remove(g_timer_id)
        g_timer_id = None

    print("Timer abgebrochen!")
    toggle_app_state(False)


def on_button_click(button):
    cancel = "Cancel" in GTK.Buildable.get_name(button)

    if cancel:
        stop_timer()
        return False

    hours, minutes = validate_time()
    start_timer(hours, minutes)

    return True


def on_spin_click(button):
    BTN_ID = GTK.Buildable.get_name(button) # get the button's ID!

    # Python's ternary operator...
    step = 1 if "Up" in BTN_ID else -1

    if "Hours" in BTN_ID:
        txtHours = builder.get_object("inpHours")
        hours = int(txtHours.get_text()) + step
        if hours > 23:
            hours = 0
        elif hours < 0:
            hours = 23
        txtHours.set_text(f"{hours:02d}")

    elif "Minutes" in BTN_ID:
        txtMinutes = builder.get_object("inpMinutes")
        mins = int(txtMinutes.get_text()) + step
        if mins > 59:
            mins = 0
        elif mins < 0:
            mins = 59
        txtMinutes.set_text(f"{mins:02d}")


def set_event_listeners():
    builder.get_object("btnStart").connect("clicked", on_button_click)
    builder.get_object("btnCancel").connect("clicked", on_button_click)

    builder.get_object("btnHoursUp").connect("clicked", on_spin_click)
    builder.get_object("btnHoursDown").connect("clicked", on_spin_click)
    builder.get_object("btnMinutesUp").connect("clicked", on_spin_click)
    builder.get_object("btnMinutesDown").connect("clicked", on_spin_click)
    builder.get_object("inpHours").connect("changed", validate_time)
    builder.get_object("inpMinutes").connect("changed", validate_time)
    builder.get_object("inpHours").connect("focus-out-event", format_time)
    builder.get_object("inpMinutes").connect("focus-out-event", format_time)

    builder.get_object("mnuQuit").connect("activate", quit_app)


def init_ui():
    WINDOW.set_position(GTK.WindowPosition.CENTER)
    WINDOW.set_icon_from_file("icons/idle.svg")
    status_icon = builder.get_object("imgStatus")
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("icons/idle.svg", 36, 36, True )
    status_icon.set_from_pixbuf(pixbuf)
    now = datetime.now(timezone.utc).astimezone()
    builder.get_object("inpHours").set_text(f"{now.hour:02d}")
    builder.get_object("inpMinutes").set_text(f"{now.minute:02d}")

    set_event_listeners()
    WINDOW.connect("delete-event", quit_app)


def quit_app(*_args):
    if g_timer_id is not None:
        confirmed = msg_box(
            "A timer is currently running.\nDo you really want to quit PowerTimer?",
            "Quit PowerTimer",
            GTK.ButtonsType.YES_NO
        )

        if not confirmed:
            return True

        stop_timer()

    GTK.main_quit()
    return False


init_ui()
WINDOW.show_all()
GTK.main()