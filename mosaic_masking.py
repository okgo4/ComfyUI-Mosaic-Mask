import numpy as np
import cv2
import torch

import os
file_path = os.path.dirname(os.path.abspath(__file__))

class MosaicMask:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
               "image": ("IMAGE",),
               "top_n": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
               "kernel_size": ("INT", {"default": 3, "min": 0, "max": 100, "step": 1}),
            }
        }

    RETURN_TYPES = ("MASK", )
    RETURN_NAMES = ("mosaic_mask", )
    FUNCTION = "get_mask"
    #OUTPUT_NODE = False
    CATEGORY = "Mosaic Masking"
    
    def get_mask(self, image, top_n, kernel_size):
       
        image_np = image.squeeze(0).numpy()
        image_np = (image_np*255).astype(np.uint8)
        img_rgb = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        img_gray = cv2.Canny(img_gray, 10, 20)
        img_gray = 255 - img_gray
        img_gray = cv2.GaussianBlur(img_gray, (3, 3), 0)
        mask = np.zeros_like(img_gray, dtype=np.uint8)
        
        for i in range(10, 20 + 1):
            pattern_filename = f"{file_path}/grids/pattern{i}x{i}.png"
            template = cv2.imread(pattern_filename, 0)
            w, h = template.shape[::-1]
            img_kensyutu_kekka = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.3
            loc = np.where(img_kensyutu_kekka >= threshold)
            for pt in zip(*loc[::-1]):
                cv2.rectangle(mask, pt, (pt[0] + w, pt[1] + h), (255), -1)
        
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        expanded_mask = cv2.dilate(mask, kernel, iterations=1)
        largest_mask = self.keep_largest_component(expanded_mask, top_n)
        expanded_mask_tensor = torch.from_numpy(largest_mask).unsqueeze(0).to(torch.float32)

        return expanded_mask_tensor
    

    def keep_largest_component(self, mask, top_n=1):
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        if num_labels <= 1:
            return mask
        
        areas = stats[1:, cv2.CC_STAT_AREA]
        
        top_n_indices = np.argsort(areas)[-top_n:]

        top_n_mask = np.zeros_like(mask)
        for idx in top_n_indices:
            top_n_mask[labels == (idx + 1)] = 255
        
        return top_n_mask
    
NODE_CLASS_MAPPINGS = {
    "MosaicMask": MosaicMask,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MosaicMask": "MosaicMask",
    
}
