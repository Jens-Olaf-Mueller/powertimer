#!/usr/bin/env python3

import subprocess
from pathlib import Path

# Application modules always live beside this file.  In a source checkout the
# resources and documentation are local too; an installed application uses the
# shared Debian locations instead.
APP_DIR = Path(__file__).resolve().parent

# Prefer source-tree resources so local development does not accidentally use
# the assets of an installed PowerTimer package.
if (APP_DIR / "ui" / "powertimer.ui").is_file():
    DATA_DIR = APP_DIR
    DOC_DIR = APP_DIR
else:
    DATA_DIR = Path("/usr/share/powertimer")
    DOC_DIR = Path("/usr/share/doc/powertimer")

UI_FILE = DATA_DIR / "ui" / "powertimer.ui"
STYLESHEET_FILE = DATA_DIR / "ui" / "style.css"
IDLE_ICON = DATA_DIR / "icons" / "idle.svg"
ACTIVE_ICON = DATA_DIR / "icons" / "active.svg"

class AppInfo:
    """Provides centralized metadata and project information for the application."""
    def __init__(self):
        self.name = "PowerTimer"
        self.author = "Jens-Olaf Mueller"

        self.major = 1
        self.minor = 1
        self.revision = 0

        self.description = (
            "Simple shutdown timer for Linux Mint Cinnamon,\nwritten in Python with GTK."
        )

        self.created = "2026-08-07"

        # Used when no Git repository is available,
        # for example in an installed release version.
        self.release_date = "2026-08-12"


        # Project website / GitHub repository
        self.website = "https://github.com/Jens-Olaf-Mueller/powertimer"

        self.icon = IDLE_ICON


    @property
    def version(self):
        """Returns the full version of the app"""
        return f"{self.major}.{self.minor}.{self.revision}"


    @property
    def readme(self):
        """
        Return the content of the project's README.md file.

        Returns:
            str: README content, or an empty string if the file is unavailable.
        """
        return self._read_text_file(DOC_DIR / "README.md")


    @property
    def license(self):
        return self._read_text_file(DOC_DIR / "LICENSE")


    @property
    def last_changed(self):
        """
            Returns the date of the most recent Git commit.

            If the application is running outside a Git repository or Git is not available,
            the configured release date is returned as a fallback.
        """
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cs"],
                cwd=APP_DIR,
                capture_output=True,
                text=True,
                check=True
            )

            date = result.stdout.strip()
            if date:
                return date

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return self.release_date

    def _read_text_file(self, path):
        """
            Read a UTF-8 text file.

            Args:
                path (Path): Path to the text file.

            Returns:
                str | "": File content, or empty string if the file cannot be read.

            Raises:
                FileNotFoundError: If the file does not exist.
        """
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return ""


APP_INFO = AppInfo()
