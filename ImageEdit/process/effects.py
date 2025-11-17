import cv2
import numpy as np

def clamp_arr(a: np.ndarray):
    """Helper: Memastikan nilai ada di 0-255 sebelum convert ke uint8 agar tidak wrapping/aneh"""
    return np.clip(a, 0, 255).astype(np.uint8)

def apply_effects_cv2(cv2_img,
                      brightness=0.0,
                      contrast=0.0,
                      highlights=0.0,
                      shadows=0.0,
                      saturation=0.0,
                      tint=0.0,
                      temperature=0.0,
                      sharpness=0.0):
    
    if cv2_img is None:
        return None

    # Gunakan float32 untuk kalkulasi agar tidak ada overflow negatif/positif
    arr = cv2_img.astype(np.float32)

    # 1. BRIGHTNESS
    bright_offset = (brightness/100.0)*255.0
    if abs(bright_offset) > 1e-6:
        arr += bright_offset

    # 2. CONTRAST
    c = np.clip(contrast, -99.0, 99.0)
    if abs(c) > 1e-6:
        factor = (259.0*(c+255.0))/(255.0*(259.0-c))
        arr = factor*(arr-128.0)+128.0

    # PENTING: Clamp di sini sebelum convert ke HSV
    # Kalau tidak, nilai -50 akan jadi 206 (wrapping), bikin warna rusak
    arr = np.clip(arr, 0, 255)

    # 3. HIGHLIGHTS & SHADOWS
    hl = highlights/100.0
    sh = shadows/100.0
    if abs(hl) > 1e-6 or abs(sh) > 1e-6:
        # Convert ke HSV butuh input uint8 yang valid
        hsv = cv2.cvtColor(clamp_arr(arr), cv2.COLOR_BGR2HSV).astype(np.float32)
        
        lum = hsv[:,:,2] # V channel
        mask_hi = lum > 128.0
        mask_lo = ~mask_hi
        
        # Logika Highlight/Shadow
        hsv[mask_hi, 2] = hsv[mask_hi, 2] + (hsv[mask_hi, 2] - 128.0) * -hl * 0.5
        hsv[mask_lo, 2] = hsv[mask_lo, 2] + (128.0 - hsv[mask_lo, 2]) * sh * 0.5
        
        arr = cv2.cvtColor(clamp_arr(hsv), cv2.COLOR_HSV2BGR).astype(np.float32)

    # 4. TEMPERATURE (Blue vs Red)
    temp = temperature/100.0
    if abs(temp) > 1e-6:
        t_adj = temp * 40.0
        arr[:,:,2] += t_adj  # Red naik
        arr[:,:,0] -= t_adj  # Blue turun

    # 5. TINT (Green vs Magenta)
    tint_val = tint/100.0
    if abs(tint_val) > 1e-6:
        t_adj = tint_val * 40.0
        arr[:,:,1] += t_adj        # Green naik
        arr[:,:,0] -= t_adj * 0.5  # Blue turun dikit
        arr[:,:,2] -= t_adj * 0.5  # Red turun dikit

    # Clamp lagi sebelum saturasi
    arr = np.clip(arr, 0, 255)

    # 6. SATURATION
    sat_factor = 1.0 + saturation/100.0
    if abs(sat_factor - 1.0) > 1e-6:
        hsv = cv2.cvtColor(clamp_arr(arr), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:,:,1] *= sat_factor
        arr = cv2.cvtColor(clamp_arr(hsv), cv2.COLOR_HSV2BGR).astype(np.float32)

    # 7. SHARPNESS
    if abs(sharpness) > 1e-6:
        src_uint = clamp_arr(arr)
        s = sharpness / 100.0
        sigma = 1.0 + abs(s) * 2.0
        blurred = cv2.GaussianBlur(src_uint, (0, 0), sigma).astype(np.float32)
        
        amount = s * 1.5
        arr = arr + (arr - blurred) * amount

    # Final clamp sebelum return
    return clamp_arr(arr)