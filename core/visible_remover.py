import cv2
import numpy as np
from typing import Optional, Tuple, List

class VisibleWatermarkRemover:
    @staticmethod
    def remove_corner_sparkle(img_bgr: np.ndarray, corner: str = "bottom-right", margin_pct: float = 0.15) -> np.ndarray:
        """
        Detects and removes visible corner watermarks (such as the Google Gemini sparkle ✦).
        """
        h, w = img_bgr.shape[:2]
        output = img_bgr.copy()

        # Define corner region of interest (ROI)
        roi_h = int(h * margin_pct)
        roi_w = int(w * margin_pct)

        if corner == "bottom-right":
            x1, y1, x2, y2 = w - roi_w, h - roi_h, w, h
        elif corner == "bottom-left":
            x1, y1, x2, y2 = 0, h - roi_h, roi_w, h
        elif corner == "top-right":
            x1, y1, x2, y2 = w - roi_w, 0, w, roi_h
        else:
            x1, y1, x2, y2 = 0, 0, roi_w, roi_h

        roi = output[y1:y2, x1:x2]

        # Convert to grayscale to locate bright/white watermark features
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Threshold to isolate high-luminance watermark pixels
        _, mask = cv2.threshold(gray_roi, 210, 255, cv2.THRESH_BINARY)
        
        # Dilate mask slightly to cover watermark anti-aliased borders
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_dilated = cv2.dilate(mask, kernel, iterations=2)

        # Inpaint ROI if any watermark features were found
        if np.count_nonzero(mask_dilated) > 20:
            cleaned_roi = cv2.inpaint(roi, mask_dilated, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            output[y1:y2, x1:x2] = cleaned_roi

        return output

    @staticmethod
    def inpaint_box(img_bgr: np.ndarray, box: Tuple[int, int, int, int], method: str = "telea") -> np.ndarray:
        """
        Inpaints an arbitrary bounding box: (x1, y1, x2, y2)
        """
        h, w = img_bgr.shape[:2]
        x1, y1, x2, y2 = box
        x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
        y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))

        mask = np.zeros((h, w), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255

        inpaint_flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
        return cv2.inpaint(img_bgr, mask, inpaintRadius=5, flags=inpaint_flag)

    @staticmethod
    def inpaint_mask(img_bgr: np.ndarray, mask: np.ndarray, method: str = "telea") -> np.ndarray:
        """
        Inpaints an arbitrary binary mask (255 where watermark is).
        """
        inpaint_flag = cv2.INPAINT_TELEA if method.lower() == "telea" else cv2.INPAINT_NS
        return cv2.inpaint(img_bgr, mask, inpaintRadius=5, flags=inpaint_flag)
