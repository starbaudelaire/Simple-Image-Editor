import cv2
import os

class Editor:
    def __init__(self):
        self.original = None
        self.edited = None
        self.history = []
        self.future = []
        
    def load_image(self, file_path):
        self.original = cv2.imread(file_path)
        if self.original is not None:
            self.edited = self.original.copy()
            # History menyimpan State lengkap: Gambar, Parameter Slider, Rotasi
            initial_state = {
                'original': self.original.copy(), # Base image (penting jika dicrop)
                'edited': self.edited.copy(),     # Hasil jadi
                'params': {},                     # Slider kosong
                'rotation': 0                     # Rotasi 0
            }
            self.history = [initial_state]
            self.future = []

    def save_image(self, file_path):
        if self.edited is not None:
            cv2.imwrite(file_path, self.edited)
            return True
        return False

    def push_history(self, current_original, current_edited, params, rotation):
        """Menyimpan snapshot lengkap keadaan editor"""
        if current_edited is None: return
        
        state = {
            'original': current_original.copy(),
            'edited': current_edited.copy(),
            'params': params.copy() if params else {},
            'rotation': rotation
        }
        
        # Hindari duplikat history kalau state sama persis (opsional, biar hemat memori)
        if self.history:
            last = self.history[-1]
            # Simple check, kalau mau strict bisa cek konten array
            # Tapi untuk performa, kita push aja kalau ada aksi user.
            pass

        self.history.append(state)
        self.future = [] # Clear redo stack jika ada perubahan baru

    def undo(self):
        if len(self.history) > 1:
            self.future.append(self.history.pop())
            return self.history[-1] # Return state sebelumnya
        return None

    def redo(self):
        if self.future:
            state = self.future.pop()
            self.history.append(state)
            return state
        return None

    def crop(self, box):
        # Crop mengubah 'original' base image
        if self.edited is not None:
            x1, y1, x2, y2 = box
            # Crop dari edited image yang sedang tampil
            self.edited = self.edited[y1:y2, x1:x2]
            # Update original juga agar efek slider selanjutnya di-apply ke hasil crop
            self.original = self.edited.copy() 

    def reset_to_original(self):
        # Kita perlu reload dari file atau simpan true_original terpisah.
        # Untuk simplicitas di struktur ini, kita asumsikan history[0] adalah true original
        if self.history:
            first_state = self.history[0]
            self.original = first_state['original'].copy()
            self.edited = first_state['edited'].copy()
            
            # Reset history ke awal
            self.history = [first_state]
            self.future = []