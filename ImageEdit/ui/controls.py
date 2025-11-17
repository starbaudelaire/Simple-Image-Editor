from PyQt5 import QtWidgets, QtCore
import functools


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        layout = QtWidgets.QGridLayout(self)

        self.sliders = {}
        self.labels = {}

        # Format: (Nama Label, Min Value, Max Value, Default Value)
        names = [
            ("Brightness", -100, 100, 0),
            ("Contrast", -99, 99, 0),
            ("Highlights", -100, 100, 0),
            ("Shadows", -100, 100, 0),
            ("Saturation", -100, 100, 0),
            ("Tint", -100, 100, 0),
            ("Temperature", -100, 100, 0),
            ("Sharpness", -100, 100, 0),
            # --- NEW CONTROLS ---
            ("Denoise", 0, 9, 0),   # Median Blur strength
            ("Invert", 0, 1, 0),    # Toggle Negative (0/1)
            ("Edge", 0, 1, 0)       # Toggle Edge Detection (0/1)
        ]

        row = 0
        for name, mn, mx, init in names:
            lbl = QtWidgets.QLabel(f"{name}: {init}")
            s = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            s.setMinimum(int(mn))
            s.setMaximum(int(mx))
            s.setValue(int(init))
            s.valueChanged.connect(functools.partial(self.on_change, name, lbl))

            layout.addWidget(lbl, row, 0)
            layout.addWidget(s, row, 1)

            self.sliders[name] = s
            self.labels[name] = lbl
            row += 1

        # debounce timer
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.fire_callback)

    def on_change(self, name, label, value):
        label.setText(f"{name}: {value}")
        self.timer.start()

    def fire_callback(self):
        # Panggil callback pas slider digeser (buat mode edit foto biasa)
        params = self.get_params()
        self.callback(params)

    def get_params(self):
        # --- INI FUNGSI YANG HILANG TADI ---
        # Fungsi ini dipanggil sama loop kamera buat ngambil settingan secara realtime
        return {k.lower(): float(v.value()) for k, v in self.sliders.items()}

    def reset(self):
        for k, s in self.sliders.items():
            s.blockSignals(True)
            s.setValue(0)
            s.blockSignals(False)