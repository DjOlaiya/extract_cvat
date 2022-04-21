# extract_cvat
script to extract cvat annotation and create mask files.


## Running Script
- Create virutal environment `py -m venv venv`
- activate it `.\venv\Scripts\activate` for windows OS
- install packages `pip install -r .\requirements.txt`
- example call to run script: `py .\cvat_img.py --image-dir \test_images\images\ --cvat-xml test_images\annotations.xml --output-dir masked_images`

