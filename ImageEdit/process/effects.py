import cv2
import numpy as np

# Implementation mirrors single-file version but modularized

def clamp_arr(a: np.ndarray):
    np.clip(a, 0, 255, out=a)
    return a.astype(np.uint8)

def apply_effects_cv2(cv2_img,
                      brightness=0.0,
                      contrast=0.0,
                      highlights=0.0,
                      shadows=0.0,
                      saturation=0.0,
                      tint=0.0,
                      temperature=0.0,
                      sharpness=0.0,
                      # --- FITUR BARU DI SINI ---
                      denoise=0.0,   # Salt & Pepper Restoration
                      invert=0.0,    # Negative Image
                      edge=0.0):     # Edge Detection
    
    # cv2_img is BGR
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

    # 3. HIGHLIGHTS & SHADOWS
    hl = highlights/100.0
    sh = shadows/100.0
    if abs(hl) > 1e-6 or abs(sh) > 1e-6:
        # Convert to HSV for luminance
        hsv = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        lum = hsv[:,:,2]
        mask_hi = lum > 128.0
        mask_lo = ~mask_hi
        hsv[mask_hi, 2] = hsv[mask_hi, 2] + (hsv[mask_hi, 2] - 128.0)*hl
        hsv[mask_lo, 2] = hsv[mask_lo, 2] + (128.0 - hsv[mask_lo, 2]) * sh * -1.0
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    # 4. SALT & PEPPER RESTORATION (DENOISE) - NEW!
    # Pake Median Blur, efektif buat noise bintik-bintik
    if denoise > 0.0:
        k = int(denoise)
        # Kernel median blur harus ganjil (misal 3, 5, 7)
        if k % 2 == 0: k += 1
        # MedianBlur butuh input uint8
        temp_uint8 = np.clip(arr, 0, 255).astype(np.uint8)
        arr = cv2.medianBlur(temp_uint8, k).astype(np.float32)

    # 5. TEMPERATURE
    temp = temperature/100.0
    t_adj = temp * 30.0
    arr[:,:,2] += t_adj  # R channel
    arr[:,:,0] -= t_adj  # B channel

    # 6. TINT
    tint_adj = tint/100.0
    arr[:,:,1] += tint_adj*20.0  # G
    arr[:,:,2] -= tint_adj*6.0   # R
    arr[:,:,0] -= tint_adj*6.0   # B

    # 7. SATURATION
    sat_factor = 1.0 + saturation/100.0
    if abs(sat_factor - 1.0) > 1e-6:
        hsv = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:,:,1] *= sat_factor
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    # 8. INVERT (NEGATIVE) - NEW!
    if invert > 0.5: # Anggep toggle (0 atau 1)
        arr = 255.0 - arr

    # Clamp values (biar ga over 255 atau under 0)
    arr = clamp_arr(arr.astype(np.float32))

    # 9. SHARPNESS
    if abs(sharpness) > 1e-6:
        s = max(-1.0, min(2.0, sharpness/100.0))
        radius = 1.0 + abs(s)*2.0
        amount = s * 1.5
        blurred = cv2.GaussianBlur(arr.astype(np.uint8), (0, 0), radius)
        blurred = blurred.astype(np.float32)
        result = arr + (arr - blurred) * amount
        result = clamp_arr(result)
        arr = result

    # 10. EDGE DETECTION - NEW!
    # Ditaro paling akhir biar dia nge-detect edge dari hasil visual final
    if edge > 0.5: # Toggle
        temp_uint8 = arr.astype(np.uint8)
        gray = cv2.cvtColor(temp_uint8, cv2.COLOR_BGR2GRAY)
        # Canny Edge Detection
        edges = cv2.Canny(gray, 100, 200)
        # Convert balik ke BGR biar formatnya konsisten
        arr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR).astype(np.float32)

    return arr.astype(np.uint8)

def apply_effects(cv2_img, effects_list):
    """Apply a list of effects to an image."""
    result = cv2_img.copy()
    for effect in effects_list:
        if isinstance(effect, dict):
            result = apply_effects_cv2(result, **effect)
        else:
            # Fallback if params not dict (should not happen in this app)
            result = apply_effects_cv2(result)
    return result