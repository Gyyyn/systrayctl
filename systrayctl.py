import sys
import subprocess
from PyQt6 import QtWidgets, QtGui, QtCore
import notify2

# Define services you want to manage
UNITS = {
    "Ollama": "ollama.service",
    "Stable Diffusion": "stable-diffusion-webui.service",
}

REFRESH_INTERVAL_MS = 5000
TRAY_ICON_PATH = "view-multiple-objects"

class ServiceTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__()

        icon = QtGui.QIcon(TRAY_ICON_PATH)
        self.setIcon(icon)
        self.setToolTip("Initializing...")

        self.menu = QtWidgets.QMenu()
        self.unit_actions = {}

        notify2.init("Systrayctl")

        self.build_menu()
        self.setContextMenu(self.menu)
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(REFRESH_INTERVAL_MS)
        self.refresh_status()

    def build_menu(self):
        for label, unit in UNITS.items():
            submenu = QtWidgets.QMenu(label)

            start_action = QtGui.QAction("Start")
            start_action.triggered.connect(lambda _, u=unit: self.control_unit(u, "start"))
            submenu.addAction(start_action)

            stop_action = QtGui.QAction("Stop")
            stop_action.triggered.connect(lambda _, u=unit: self.control_unit(u, "stop"))
            submenu.addAction(stop_action)

            self.menu.addMenu(submenu)

            self.unit_actions[unit] = {
                "menu": submenu,
                "start": start_action,
                "stop": stop_action
            }

        self.menu.addSeparator()

        quit_action = QtGui.QAction("Quit")
        quit_action.triggered.connect(QtWidgets.QApplication.quit)
        self.menu.addAction(quit_action)

    def refresh_status(self):
        tooltip_lines = []
        for label, unit in UNITS.items():
            is_active = self.is_unit_active(unit)
            actions = self.unit_actions[unit]

            emoji = "▶️" if is_active else "⛔"
            actions["menu"].setTitle(f"{emoji} {label}")
            actions["start"].setEnabled(not is_active)
            actions["stop"].setEnabled(is_active)

            tooltip_lines.append(f"{label}: {'Active' if is_active else 'Inactive'}")

        self.setToolTip("Service Status:\n" + "\n".join(tooltip_lines))

    def is_unit_active(self, unit):
        try:
            result = subprocess.run(
                ["systemctl", "is-active", unit],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False

    def control_unit(self, unit, action):
        try:
            subprocess.run(["systemctl", action, unit], check=True)
            self.notify(f"{unit} {action}ed successfully")
        except subprocess.CalledProcessError:
            self.notify(f"Failed to {action} {unit}")
        self.refresh_status()

    def notify(self, message):
        n = notify2.Notification("Systemctl Tray", message)
        n.set_timeout(2000)
        n.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    tray = ServiceTrayApp()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
