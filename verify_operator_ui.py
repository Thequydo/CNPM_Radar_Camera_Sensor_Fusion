import sys
import os
import time

sys.path.insert(0, r"C:\CNPM_Project")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QImage, QColor
import numpy as np

from main import MainWindow
from radar_parser import RadarTarget

def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = MainWindow()

    # 1. Login as operator
    window.login_user.setText("operator")
    window.login_pwd.setText("operator123")
    window._do_login()

    # Process events
    app.processEvents()

    # Check tab counts and visibility for Operator
    visible_tabs = [window.tabs.tabText(i) for i in range(window.tabs.count()) if window.tabs.isTabVisible(i)]
    print(f"Operator Visible Tabs: {visible_tabs}")

    # Set window size to 1366x768 and capture
    window.resize(1366, 768)
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    window.grab().save(r"C:\CNPM_Project\captures\operator_1366_idle.png")

    # Set window size to 1920x1080 and capture
    window.resize(1920, 1080)
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    window.grab().save(r"C:\CNPM_Project\captures\operator_1920_idle.png")

    # Now simulate active targets and alert state
    t1 = RadarTarget(target_id=1, x_m=0.89, y_m=1.41, speed_kmh=15.2, valid=True, closing_speed_mps=4.22, ttc_sec=0.40)
    t2 = RadarTarget(target_id=2, x_m=-1.10, y_m=3.20, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None)
    t3 = RadarTarget(target_id=3, x_m=1.50, y_m=4.80, speed_kmh=-8.5, valid=True, closing_speed_mps=-2.36, ttc_sec=None)

    # Click toggle monitoring to start
    window.btn_monitor_toggle.click()
    app.processEvents()

    window._on_radar_targets_ready([t1, t2, t3])
    app.processEvents()

    # Capture alert state at 1366 and 1920
    window.resize(1366, 768)
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    window.grab().save(r"C:\CNPM_Project\captures\operator_1366_alert.png")

    window.resize(1920, 1080)
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()
    window.grab().save(r"C:\CNPM_Project\captures\operator_1920_alert.png")

    # Test Simulation banner
    window.check_sim.setChecked(True)
    app.processEvents()
    window.grab().save(r"C:\CNPM_Project\captures\operator_sim_banner.png")
    window.check_sim.setChecked(False)
    app.processEvents()

    # Logout and login as admin to capture Admin tabs
    window.user_session = None
    window.login_user.setText("admin")
    window.login_pwd.setText("admin123")
    window._do_login()
    app.processEvents()

    admin_visible_tabs = [window.tabs.tabText(i) for i in range(window.tabs.count()) if window.tabs.isTabVisible(i)]
    print(f"Admin Visible Tabs: {admin_visible_tabs}")

    # Capture each admin tab
    for idx, name in enumerate(["monitor", "audit", "device", "diagnostics", "simulation", "settings"]):
        window.tabs.setCurrentIndex(idx)
        app.processEvents()
        time.sleep(0.05)
        app.processEvents()
        window.grab().save(rf"C:\CNPM_Project\captures\admin_tab_{name}.png")

    print("ALL CAPTURES COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    os.makedirs(r"C:\CNPM_Project\captures", exist_ok=True)
    main()
