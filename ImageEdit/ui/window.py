import cv2
from PyQt5 import QtWidgets, QtCore, QtGui
from ui.controls import ControlPanel
from ui.crop_widget import CropLabel
from process.editor import Editor
from process.workers import ApplyWorker
from utils.converters import cv2_to_qpixmap, scaled_size_for_label
from process.histogram import histogram_image_from_cv2
from process.effects import apply_effects_cv2

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Editor - Final Fix")
        self.resize(1200, 760)
        
        self.editor = Editor()

        # --- TOMBOL ---
        top_buttons = QtWidgets.QHBoxLayout()
        self.open_btn = QtWidgets.QPushButton("Open Image")
        self.camera_btn = QtWidgets.QPushButton("Start Camera")
        self.save_btn = QtWidgets.QPushButton("Save Edited")
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.undo_btn = QtWidgets.QPushButton("Undo")
        self.redo_btn = QtWidgets.QPushButton("Redo")
        self.rotate_left_btn = QtWidgets.QPushButton("⟲")
        self.rotate_right_btn = QtWidgets.QPushButton("⟳")

        for btn in [self.open_btn, self.camera_btn, self.save_btn, self.reset_btn, 
                   self.undo_btn, self.redo_btn, self.rotate_left_btn, self.rotate_right_btn]:
            top_buttons.addWidget(btn)
        top_buttons.addStretch()

        self.open_btn.clicked.connect(self.open_image)
        self.camera_btn.clicked.connect(self.toggle_camera)
        self.save_btn.clicked.connect(self.save_image)
        self.reset_btn.clicked.connect(self.reset)
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_image(-90))
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_image(90))

        # --- VIEWS ---
        self.before_label = QtWidgets.QLabel("Before")
        self.before_view = QtWidgets.QLabel()
        self.before_view.setAlignment(QtCore.Qt.AlignCenter)
        self.before_view.setMinimumSize(360, 300)
        self.before_view.setStyleSheet("background:#111; border: 1px solid #444;")

        self.after_label = QtWidgets.QLabel("After (drag to crop)")
        self.after_view = CropLabel()
        self.after_view.setAlignment(QtCore.Qt.AlignCenter)
        self.after_view.setMinimumSize(360, 300)
        self.after_view.setStyleSheet("background:#111; border: 1px solid #444;")

        self.after_view.mouse_pressed.connect(self.on_crop_press)
        self.after_view.mouse_moved.connect(self.on_crop_move)
        self.after_view.mouse_released.connect(self.on_crop_release)

        images_layout = QtWidgets.QHBoxLayout()
        left_v = QtWidgets.QVBoxLayout()
        left_v.addWidget(self.before_label)
        left_v.addWidget(self.before_view)
        right_v = QtWidgets.QVBoxLayout()
        right_v.addWidget(self.after_label)
        right_v.addWidget(self.after_view)

        # Histogram
        hist_v = QtWidgets.QVBoxLayout()
        hist_label = QtWidgets.QLabel("Histogram (RGB)")
        hist_label.setAlignment(QtCore.Qt.AlignCenter)
        self.hist_view = QtWidgets.QLabel()
        self.hist_view.setMinimumHeight(120)
        self.hist_view.setStyleSheet("background:#222; border: 1px solid #444;")
        hist_v.addWidget(hist_label)
        hist_v.addWidget(self.hist_view)

        images_layout.addLayout(left_v)
        images_layout.addLayout(right_v)
        images_layout.addLayout(hist_v)

        # Controls
        self.controls = ControlPanel(self.apply_params_changed)

        main_v = QtWidgets.QVBoxLayout(self)
        main_v.addLayout(top_buttons)
        main_v.addLayout(images_layout)
        main_v.addWidget(self.controls)

        self.threadpool = QtCore.QThreadPool()

        # Crop vars
        self._crop_start = None
        self._crop_end = None
        self._cropping = False

        # State vars
        self.camera = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_camera_frame)
        self.is_camera_active = False
        self.current_rotation = 0 

    # ==========================
    #       HELPERS
    # ==========================
    def get_rotated_frame(self, img):
        """Helper: Merotasi gambar sesuai self.current_rotation"""
        if img is None or self.current_rotation == 0:
            return img
        
        angle = self.current_rotation % 360
        if angle == 90:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(img, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return img
    
    def manual_push_history(self):
        """Simpan state sekarang ke history"""
        params = self.controls.get_params()
        self.editor.push_history(
            self.editor.original, 
            self.editor.edited, 
            params, 
            self.current_rotation
        )

    # ==========================
    #       CAMERA
    # ==========================
    def toggle_camera(self):
        if self.is_camera_active:
            self.timer.stop()
            if self.camera:
                self.camera.release()
            self.camera = None
            self.is_camera_active = False
            self.camera_btn.setText("Start Camera")
            
            self.open_btn.setEnabled(True)
            self.rotate_left_btn.setEnabled(True)
            self.rotate_right_btn.setEnabled(True)
            self.undo_btn.setEnabled(True)
            self.redo_btn.setEnabled(True)
        else:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QtWidgets.QMessageBox.warning(self, "Error", "Camera not found.")
                return
            
            self.is_camera_active = True
            self.camera_btn.setText("Stop Camera")
            
            self.open_btn.setEnabled(False)
            self.current_rotation = 0 
            self.rotate_left_btn.setEnabled(False)
            self.rotate_right_btn.setEnabled(False)
            self.undo_btn.setEnabled(False)
            self.redo_btn.setEnabled(False)
            
            self.timer.start(30)

    def update_camera_frame(self):
        if self.camera and self.is_camera_active:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.flip(frame, 1) # Mirror effect
                self.editor.original = frame # Update base
                
                try:
                    # 1. Apply slider effects
                    params = self.controls.get_params()
                    processed = apply_effects_cv2(self.editor.original, **params)
                    
                    # 2. Set result
                    self.editor.edited = processed
                    self.update_views()
                except Exception as e:
                    print(f"Cam error: {e}")

    # ==========================
    #      FILE & EDITING
    # ==========================
    def open_image(self):
        if self.is_camera_active: self.toggle_camera()
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path: return

        self.editor.load_image(path)
        self.current_rotation = 0
        self.controls.reset()
        self.update_views()
        # History awal sudah di-init di dalam load_image

    def save_image(self):
        if self.editor.edited is None: return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save", "", "PNG (*.png);;JPEG (*.jpg)")
        if not path: return
        self.editor.save_image(path)
        QtWidgets.QMessageBox.information(self, "Saved", "Image Saved")

    def reset(self):
        self.editor.reset_to_original()
        self.controls.reset()
        self.current_rotation = 0
        self.update_views()
        
        # Reset tidak push history baru, tapi me-reset stack (sesuai implementasi editor.py)
        # atau kita bisa push state 'reset' sebagai history baru.
        # Implementasi editor.reset_to_original saat ini mereset stack.

    # ==========================
    #      UNDO / REDO (THE FIX)
    # ==========================
    def undo(self):
        if self.is_camera_active: return
        
        state = self.editor.undo()
        if state:
            self.restore_state(state)

    def redo(self):
        if self.is_camera_active: return
        
        state = self.editor.redo()
        if state:
            self.restore_state(state)

    def restore_state(self, state):
        """Mengembalikan tampilan UI dan Editor sesuai state history"""
        # 1. Restore Editor Data
        self.editor.original = state['original'].copy()
        self.editor.edited = state['edited'].copy()
        
        # 2. Restore Rotation
        self.current_rotation = state['rotation']
        
        # 3. Restore Sliders (PENTING: Biar slider mundur juga)
        self.controls.set_params(state['params'])
        
        # 4. Update View
        self.update_views()

    # ==========================
    #      ROTATION & SLIDERS
    # ==========================
    def rotate_image(self, angle):
        self.current_rotation = (self.current_rotation + angle) % 360
        
        # Jalankan ulang pipeline efek agar rotasi diterapkan
        params = self.controls.get_params()
        self.apply_params_changed(params)

    def apply_params_changed(self, params):
        if self.is_camera_active: return
        
        worker = ApplyWorker(self.editor.original, params)
        worker.signals.result.connect(self.on_worker_result)
        self.threadpool.start(worker)

    def on_worker_result(self, img_with_effects):
        # Apply rotation at the end of pipeline
        final_img = self.get_rotated_frame(img_with_effects)
        
        self.editor.edited = final_img
        self.update_views()
        
        # Push history setiap kali edit selesai (untuk slider lepas/klik tombol)
        # Di Controls.py kita pakai Timer debounce, jadi ini tidak spamming history.
        self.manual_push_history()

    def update_views(self):
        # Scaling yang benar
        if self.editor.original is not None:
            img_h, img_w = self.editor.original.shape[:2]
            scaled_w, scaled_h = scaled_size_for_label(self.before_view, img_w, img_h)
            scaled = cv2.resize(self.editor.original, (scaled_w, scaled_h))
            self.before_view.setPixmap(cv2_to_qpixmap(scaled))
        else:
            self.before_view.clear()

        if self.editor.edited is not None:
            img_h, img_w = self.editor.edited.shape[:2]
            scaled_w, scaled_h = scaled_size_for_label(self.after_view, img_w, img_h)
            scaled = cv2.resize(self.editor.edited, (scaled_w, scaled_h))
            self.after_view.setPixmap(cv2_to_qpixmap(scaled))
            
            hist = histogram_image_from_cv2(self.editor.edited, width=512, height=120)
            self.hist_view.setPixmap(cv2_to_qpixmap(hist))
        else:
            self.after_view.clear()
            self.hist_view.clear()

    # ==========================
    #       CROP HANDLERS
    # ==========================
    def on_crop_press(self, e):
        if self.editor.edited is None: return
        self._cropping = True
        self._crop_start = (e.x(), e.y())
        self._crop_end = (e.x(), e.y())

    def on_crop_move(self, e):
        if not self._cropping: return
        self._crop_end = (e.x(), e.y())
        self.after_view.setCropRect(self._crop_start, self._crop_end)

    def on_crop_release(self, e):
        if not self._cropping: return
        self._crop_end = (e.x(), e.y())
        self._cropping = False
        self.after_view.clearCropRect()
        
        disp_w = self.after_view.width()
        disp_h = self.after_view.height()
        if disp_w == 0 or disp_h == 0: return
        
        img_h, img_w = self.editor.edited.shape[:2]
        ui_w, ui_h = scaled_size_for_label(self.after_view, img_w, img_h)
        
        offset_x = (disp_w - ui_w) / 2
        offset_y = (disp_h - ui_h) / 2
        
        sx = img_w / ui_w
        sy = img_h / ui_h
        
        x1_raw = min(self._crop_start[0], self._crop_end[0]) - offset_x
        y1_raw = min(self._crop_start[1], self._crop_end[1]) - offset_y
        x2_raw = max(self._crop_start[0], self._crop_end[0]) - offset_x
        y2_raw = max(self._crop_start[1], self._crop_end[1]) - offset_y

        x1 = int(max(0, x1_raw) * sx)
        y1 = int(max(0, y1_raw) * sy)
        x2 = int(min(img_w, x2_raw) * sx)
        y2 = int(min(img_h, y2_raw) * sy)

        if x2-x1 > 10 and y2-y1 > 10:
            self.editor.crop((x1, y1, x2, y2))
            
            # Reset rotation karena gambar sudah di-bake crop-nya
            self.current_rotation = 0 
            self.update_views()
            self.manual_push_history()