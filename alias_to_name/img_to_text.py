import os
from pathlib import Path

import pytesseract
from PIL import Image

file_path = os.path.abspath(__file__)
dir_path = os.path.dirname(file_path)
img_path = Path(os.path.join(dir_path, "data/img/molecules.jpg"))
img = Image.open(img_path)

extracted_text = pytesseract.image_to_string(
    img,
    lang="eng",
    config="--psm 4",
)

print(extracted_text.strip())
