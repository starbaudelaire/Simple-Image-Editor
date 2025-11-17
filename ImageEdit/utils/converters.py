import cv2
from PyQt5 import QtGui

def cv2_to_qpixmap(cv2_img):
    # Convert BGR (OpenCV) to RGB (Qt)
    if cv2_img is None:
        return QtGui.QPixmap()
    rgb_image = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
    return QtGui.QPixmap.fromImage(convert_to_qt_format)

def scaled_size_for_label(label, image_width, image_height):
    """
    Menghitung ukuran gambar yang diskalakan agar pas di dalam QLabel
    tanpa merusak aspek rasio (biar ga gepeng).
    """
    label_width = label.width()
    label_height = label.height()

    if label_width <= 0 or label_height <= 0:
        return image_width, image_height 

    # Hitung rasio label dan rasio gambar
    label_aspect_ratio = label_width / label_height
    image_aspect_ratio = image_width / image_height

    if image_aspect_ratio > label_aspect_ratio:
        # Gambar lebih lebar dari label, paskan width
        scaled_width = label_width
        scaled_height = int(label_width / image_aspect_ratio)
    else:
        # Gambar lebih tinggi dari label, paskan height
        scaled_height = label_height
        scaled_width = int(label_height * image_aspect_ratio)
    
    return scaled_width, scaled_height