"""
ManagerAlert.py
Manages alert state and audible buzzer signals for store managers.
Author: buonma98
"""

from Log import Log


class ManagerAlert:
    """
    ManagerAlert encapsulates the management notification subsystem.
    When triggered, it activates an audible alarm on a PassiveBuzzer.
    The alert can subsequently be silenced or cleared.
    """

    def __init__(self, buzzer=None, tone: int = 880):
        """
        Initialize the ManagerAlert.

        Parameters:
        -----------
        buzzer : PassiveBuzzer, optional
            The buzzer used to sound alarms.
        tone : int, optional
            Frequency in Hz for the alert sound (default is 880 Hz / A5 tone).
        """
        self._buzzer = buzzer
        self._tone: int = tone
        self._active: bool = False
        self._silenced: bool = False
        Log.i("ManagerAlert initialized")

    @property
    def active(self) -> bool:
        """Return True if an alert is currently active."""
        return self._active

    @property
    def silenced(self) -> bool:
        """Return True if the active alert has been silenced."""
        return self._silenced

    def start(self) -> None:
        """
        Activate the manager alert and sound the buzzer.
        """
        self._active = True
        self._silenced = False
        if self._buzzer:
            # PassiveBuzzer has play() / playTone()
            if hasattr(self._buzzer, 'playTone'):
                self._buzzer.playTone(self._tone)
            elif hasattr(self._buzzer, 'play'):
                self._buzzer.play(self._tone)
        Log.w("ManagerAlert: Alert STARTED. Buzzer sounding.")

    def silence(self) -> None:
        """
        Silence the audible buzzer while keeping alert active status noted.
        """
        self._silenced = True
        if self._buzzer:
            self._buzzer.stop()
        Log.i("ManagerAlert: Alert SILENCED.")

    def clear(self) -> None:
        """
        Clear the alert completely and ensure buzzer is turned off.
        """
        self._active = False
        self._silenced = False
        if self._buzzer:
            self._buzzer.stop()
        Log.i("ManagerAlert: Alert CLEARED.")
