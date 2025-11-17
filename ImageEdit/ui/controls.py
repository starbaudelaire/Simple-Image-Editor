from PyQt5 import QtWidgets, QtCore
import functools

class ControlPanel(QtWidgets.QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        layout = QtWidgets.QGridLayout(self)

        self.sliders = {}
        self.labels = {}

        names = [
            ("Brightness", -100, 100, 0),
            ("Contrast", -99, 99, 0),
            ("Highlights", -100, 100, 0),
            ("Shadows", -100, 100, 0),
            ("Saturation", -100, 100, 0),
            ("Tint", -100, 100, 0),
            ("Temperature", -100, 100, 0),
            ("Sharpness", -100, 100, 0)
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

        # Timer untuk mencegah lag saat slider digeser cepat
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(100) # 100ms delay
        self.timer.timeout.connect(self.fire_callback)

    def on_change(self, name, label, value):
        label.setText(f"{name}: {value}")
        self.timer.start()

    def fire_callback(self):
        params = self.get_params()
        self.callback(params)

    def reset(self):
        for k, s in self.sliders.items():
            s.blockSignals(True)
            s.setValue(0)
            s.blockSignals(False)
            # Update label text manual
            # Cari nama asli dari key lowercase
            original_name = k.capitalize()
            if original_name in self.labels:
                 self.labels[original_name].setText(f"{original_name}: 0")
            elif k in self.labels:
                 self.labels[k].setText(f"{k}: 0")

    def get_params(self):
        """Mengambil nilai slider saat ini"""
        return {k.lower(): float(v.value()) for k, v in self.sliders.items()}

    def set_params(self, params):
        """Mengatur posisi slider dari luar (untuk Undo/Redo)"""
        if not params: return
        for k, v in params.items():
            # key di params lower, tapi key di self.sliders mungkin Title Case
            # Kita cari yang cocok
            target_key = None
            for sk in self.sliders.keys():
                if sk.lower() == k.lower():
                    target_key = sk
                    break
            
            if target_key:
                slider = self.sliders[target_key]
                label = self.labels[target_key]
                val = int(v)
                
                slider.blockSignals(True) # Jangan trigger callback
                slider.setValue(val)
                slider.blockSignals(False)
                label.setText(f"{target_key}: {val}")