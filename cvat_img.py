import os
from pathlib import Path
from typing import Dict, List
import cv2
import argparse
import numpy as np
from lxml import etree

def parse_annotations_file(cvat_xml: str, image_name: str) -> Dict[str,str]:
    """ parses the annotations file and matches it to image. 
        cvat_xml: annotations.xml file,
        image_name = image filename
        Returns: dict
    """
    print(f"annotation file: {cvat_xml},image file: {image_name}")
    root = etree.parse(cvat_xml).getroot()
    anno = []
    image_name_attr = ".//image[@name='{}']".format(image_name)
    location_attr = ".//attribute[@name='{}']".format("Location")
    for image_tag in root.iterfind(image_name_attr):
        image = {}
        for key, value in image_tag.items():
            image[key] = value
        image['shapes'] = []
        # this is for the pupil centre instead of box
        # for points_tag in image_tag.iter('points'):
        #     pts = {'type': 'points'}
        #     loc = points_tag.find(location_attr)
        #     pts[loc.attrib.get('name')] = loc.text
        #     for key, value in points_tag.items():
        #         pts[key] = value
        #     image['shapes'].append(pts)

        for box_tag in image_tag.iter('box'):
            box = {'type': 'box'}
            loc = box_tag.find(location_attr)
            box[loc.attrib.get('name')] = loc.text
            for key, value in box_tag.items():
                box[key] = value
            box['points'] = "{0},{1};{2},{1};{2},{3};{0},{3}".format(
                box['xtl'], box['ytl'], box['xbr'], box['ybr'])
            image['shapes'].append(box)
        image['shapes'].sort(key=lambda x: int(x.get('z_order', 0)))
        anno.append(image)
        print(image)
    return anno

def create_mask(width:int, height:int, bitness:int, background:float, shapes:Dict[str,str], scale_factor:float) ->List[List[List[int]]]:
    """ creates the mask file that is overlaid on actual image.
        width,height: taken from image.shape
        bitness: used to create array shape
        background: original image
        shapes: annotations dictionary
        scale_factor: (shouldn't need to change this unless we compress images)
        
        """
    mask = np.full((height, width, bitness ), background, dtype=np.uint8)
    for shape in shapes:
        points = [tuple(map(float, p.split(','))) for p in shape['points'].split(';')]
        points = np.array([(int(p[0]), int(p[1])) for p in points])
        points = points*scale_factor
        points = points.astype(int)
        mask = cv2.drawContours(mask, [points], -1, color=(0, 255, 255), thickness=1)
    return mask

def main():
    args = parse_args()
    img_list = [f for f in os.listdir(args.image_dir) if os.path.isfile(os.path.join(args.image_dir, f))]
    mask_bitness = 3
    Path(args.output_dir).mkdir(parents=True,exist_ok=True)
    for img in img_list:
        img_path = os.path.join(args.image_dir, img)
        anno = parse_annotations_file(args.cvat_xml, img)
        background = []
        is_first_image = True
        for image in anno:
            if is_first_image:
                current_image = cv2.imread(img_path)
                height, width, _ = current_image.shape
                background = np.zeros((height, width, 3), np.uint8)
                is_first_image = False
            output_path = os.path.join(args.output_dir, img.split('.')[0] + '.png')
            background = create_mask(width,
                                          height,
                                          mask_bitness,
                                          current_image,
                                          image['shapes'],
                                          args.scale_factor)
        cv2.imwrite(output_path, background)

def parse_args():
    """argument parser"""
    parser = argparse.ArgumentParser(
        fromfile_prefix_chars='@',
        description='Convert CVAT XML annotations to contours'
    )
    parser.add_argument(
        '--image-dir', metavar='DIRECTORY', required=True,
        help='directory with input images'
    )
    parser.add_argument(
        '--cvat-xml', metavar='FILE', required=True,
        help='input file with CVAT annotation in xml format'
    )
    parser.add_argument(
        '--output-dir', metavar='DIRECTORY', required=True,
        help='directory for output masks'
    )
    parser.add_argument(
        '--scale-factor', type=float, default=1.0,
        help='choose scale factor for images'
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
