#!/usr/bin/env python3

import gettext
from datetime import datetime, timedelta, timezone

import gi

from about import AboutBox
from appinfo import ACTIVE_ICON, APP_INFO, IDLE_ICON, STYLESHEET_FILE, UI_FILE
from timer_dialog import TimerDialog
from tray_icon import TrayIcon

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gdk, GdkPixbuf, Gio, GLib
from gi.repository import Gtk as GTK

ACTION_PROMPTS = {
    "shutdown": "Computer will shut down in {seconds} seconds.",
    "logout": "You will be logged out in {seconds} seconds.",
}

# "_" = Short alias for gettext: marks Python strings for translation.
_ = gettext.gettext
timer_seconds = 0
g_timer_id = None


builder = GTK.Builder()
builder.add_from_file(str(UI_FILE))

css_provider = GTK.CssProvider()
css_provider.load_from_path(str(STYLESHEET_FILE))

screen = Gdk.Screen.get_default()
GTK.StyleContext.add_provider_for_screen(
    screen,
    css_provider,
    GTK.STYLE_PROVIDER_PRIORITY_APPLICATION
)
WINDOW = builder.get_object("winMain")
DLG_ABOUT = AboutBox(WINDOW, APP_INFO)
DLG_TIMER = TimerDialog(WINDOW)


def msg_box(prompt, title = APP_INFO.name, buttons = GTK.ButtonsType.OK):
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
def toggle_app_state(start = True):
    builder.get_object("btnStart").set_sensitive(not start)
    builder.get_object("btnCancel").set_sensitive(start)

    # Python's ternary operator...
    icon = ACTIVE_ICON if start else IDLE_ICON

    WINDOW.set_icon_from_file(str(icon))
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(icon), 36, 36, True)
    builder.get_object("imgStatus").set_from_pixbuf(pixbuf)


def logout():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.gnome.SessionManager",
        "/org/gnome/SessionManager",
        "org.gnome.SessionManager",
        None
    )

    proxy.call_sync(
        "Logout",
        GLib.Variant("(u)", (1,)),
        Gio.DBusCallFlags.NONE,
        -1,
        None
    )


def execute_action(action):
    if action == "logout":
        logout()
        return

    methods = {
        "suspend": "Suspend",
        "hibernate": "Hibernate",
        "restart": "Reboot",
        "shutdown": "PowerOff",
    }

    if action not in methods:
        print(f'"{action}" not yet implemented!')
        return


    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
        None
    )

    proxy.call_sync(
        methods[action],
        GLib.Variant("(b)", (True,)),
        Gio.DBusCallFlags.NONE,
        -1,
        None
    )


# Python timer construct
def on_timer_tick(action):
    global timer_seconds, g_timer_id

    timer_seconds -= 1
    TRAY.update(action, timer_seconds)

    if action in ACTION_PROMPTS and timer_seconds <= 60 and not DLG_TIMER.shown:
        DLG_TIMER.show(
            "Attention!",
            ACTION_PROMPTS[action],
            timer_seconds
        )

    # Countdown im Dialog aktualisieren
    if DLG_TIMER.shown and DLG_TIMER.response is None:
        DLG_TIMER.update(timer_seconds)

    if DLG_TIMER.response == GTK.ResponseType.CANCEL:
        DLG_TIMER.response = None
        stop_timer()
        return False

    if DLG_TIMER.response == GTK.ResponseType.ACCEPT or timer_seconds <= 0:
        DLG_TIMER.response = None
        g_timer_id = None
        toggle_app_state(False)
        TRAY.hide()
        execute_action(action)
        return False

    print(timer_seconds)
    return True


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


def start_timer(hours, minutes, action):
    global timer_seconds, g_timer_id

    timer_seconds = get_seconds_until(hours, minutes)
    g_timer_id = GLib.timeout_add_seconds(1, on_timer_tick, action)
    DLG_TIMER.reset()
    toggle_app_state()
    TRAY.show(action, timer_seconds)
    WINDOW.hide()
    print(f"Timer set for {hours}:{minutes}")


def stop_timer():
    global g_timer_id

    if g_timer_id is not None:
        GLib.source_remove(g_timer_id)
        g_timer_id = None

    print("Timer stopped!")
    toggle_app_state(False)
    TRAY.hide()

    if not WINDOW.get_visible():
        restore_window()


def on_button_click(button):
    cancel = "Cancel" in GTK.Buildable.get_name(button)

    if cancel:
        stop_timer()
        return False

    # hours, minutes = validate_time()
    hours = int(builder.get_object("inpHours").get_text() or 0)
    minutes = int(builder.get_object("inpMinutes").get_text() or 0)
    action = builder.get_object("cmbAction").get_active_id()
    start_timer(hours, minutes, action)
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

    builder.get_object("mnuAbout").connect("activate", DLG_ABOUT.show)
    builder.get_object("mnuQuit").connect("activate", quit_app)


def can_hibernate():
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
        None
    )

    result = proxy.call_sync(
        "CanHibernate",
        None,
        Gio.DBusCallFlags.NONE,
        -1,
        None
    )

    return result.unpack()[0] in ("yes", "challenge")


def init_ui():
    WINDOW.set_position(GTK.WindowPosition.CENTER)
    WINDOW.set_icon_from_file(str(IDLE_ICON))
    status_icon = builder.get_object("imgStatus")
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(IDLE_ICON), 36, 36, True )
    status_icon.set_from_pixbuf(pixbuf)
    now = datetime.now(timezone.utc).astimezone()
    builder.get_object("inpHours").set_text(f"{now.hour:02d}")
    builder.get_object("inpMinutes").set_text(f"{now.minute:02d}")

    # disable menu item "Hibernate" when not available
    if not can_hibernate():
        actions = builder.get_object("lstActions")
        actions[4][2] = False

    set_event_listeners()
    WINDOW.connect("delete-event", on_window_delete)
    WINDOW.connect("window-state-event", on_window_state)


def restore_window():
    WINDOW.deiconify()
    WINDOW.show()
    WINDOW.present()


def on_window_delete(_window, _event):
    if g_timer_id is not None:
        WINDOW.hide()
        return True

    return quit_app()


def on_window_state(_window, event):
    if (
        g_timer_id is not None
        and event.changed_mask & Gdk.WindowState.ICONIFIED
        and event.new_window_state & Gdk.WindowState.ICONIFIED
    ):
        # GTK/GDK reports minimization as iconified; hide to the active tray
        # instead so the running timer has no normal taskbar window.
        WINDOW.hide()

    return False


def quit_app(*_args):
    if g_timer_id is not None:
        confirmed = msg_box(
            f"A timer is currently running.\nDo you really want to quit {APP_INFO.name}?",
            f"Quit {APP_INFO.name}",
            GTK.ButtonsType.YES_NO
        )

        if not confirmed:
            return True

        stop_timer()

    GTK.main_quit()
    return False


TRAY = TrayIcon(restore_window, quit_app)
init_ui()
WINDOW.show_all()
GTK.main()
