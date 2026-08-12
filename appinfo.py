#!/usr/bin/env python3

import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

class AppInfo:
    """Provides centralized metadata and project information for the application."""
    def __init__(self):
        self.name = "PowerTimer"

        self.major = 1
        self.minor = 0
        self.revision = 5

        self.description = (
            "Simple shutdown timer for Linux Mint Cinnamon,\nwritten in Python with GTK."
        )

        self.created = "2026-08-07"

        # Used when no Git repository is available,
        # for example in an installed release version.
        self.release_date = "2026-08-12"


        # Project website / GitHub repository
        self.website = "https://github.com/Jens-Olaf-Mueller/powertimer"

        self.icon = PROJECT_DIR / "icons/idle.svg"


    @property
    def version(self):
        """Returns the full version of the app"""
        return f"{self.major}.{self.minor}.{self.revision}"


    @property
    def readme(self):
        """
        Return the content of the project's README.md file.

        Returns:
            str | None: README content, or None if the file is unavailable.
        """
        return self._read_text_file(PROJECT_DIR / "README.md")


    @property
    def license(self):
        return self._read_text_file(PROJECT_DIR / "LICENSE")


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
                cwd=PROJECT_DIR,
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