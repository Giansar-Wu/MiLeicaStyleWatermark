import os
import time
import json
import datetime
from multiprocessing.pool import ThreadPool
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont
import exifread

from pillow_heif import register_heif_opener

register_heif_opener()

PATH = os.path.abspath(os.path.dirname(__file__))
USER_PATH = os.path.expanduser('~')
DESKTOP_PATH = os.path.join(USER_PATH, 'Desktop')
ROOT_PATH = os.path.dirname(PATH)
DEFAULT_OUT_DIR = os.path.join(USER_PATH, 'Desktop', 'Output')
RECORDS_PATH = os.path.join(ROOT_PATH, 'resources', 'data', 'records.json')
if not os.path.exists(os.path.dirname(RECORDS_PATH)):
    os.makedirs(os.path.dirname(RECORDS_PATH))
SUPPORT_IN_FORMAT = ['.jpg', '.png', '.JPG', '.PNG']
SUPPORT_OUT_FORMAT = ['jpg', 'png']
OUT_RESOLUTION = {'1080P':1080, '2k':2160, '原图分辨率':0}

class WaterMarkAgent(object):
    def __init__(self) -> None:
        self._init_record()

        # 加水印后 从上到下 margin + img_height + watermark
        # 加水印后 从左到右 margin + img_width + margin
        # 最外侧边距与图片最长边的比例
        self.margin_ratio = 0.0
        # 水印区高度与图片最长边的比例
        self.watermark_ratio = 0.1
        # 第一行字体与水印区高度的比例
        self.font_1_ratio = 0.48
        # 第二行字体与水印区高度的比例
        self.font_2_ratio = 0.36

        self.guideline_logo_margin_ratio = 0.35
    
    def _init_record(self):
        if os.path.exists(RECORDS_PATH):
            with open(RECORDS_PATH, 'r') as f:
                ret = json.load(f)
            self.records = ret
        else:
            self.records = {}
            self.records['Camera_records'] = {}
            self.records['Lens_records'] = []
    
    def _update_record(self, exif_data: dict):
        brand = exif_data['CameraMaker'].split(" ")[0].title()
        if brand != '' and brand not in self.records['Camera_records'].keys():
            self.records['Camera_records'][brand] = []

        model = exif_data['Camera']
        if model != '' and model not in self.records['Camera_records'][brand]:
            self.records['Camera_records'][brand].append(model)

        lenmodel = exif_data.get('LenModel', '')
        if lenmodel != '' and lenmodel not in self.records['Lens_records']:
            self.records['Lens_records'].append(lenmodel)
        
    def _save_record(self):
        with open(RECORDS_PATH, 'w') as f:
            json.dump(self.records, f)

    def run(self, in_dir: str, out_dir: str=DEFAULT_OUT_DIR, out_format: str='jpg', out_quality: int=100, resolution_key: str='原图分辨率') -> tuple[int, list]:
        if in_dir == "":
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 照片文件夹不可为空!")
            return 2, []
        elif not os.path.exists(in_dir):
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 照片文件夹不存在!")
            return 2, []
        else:
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            img_list = self._load_images(in_dir)
            if img_list:
                args = [(img, out_dir, out_format, out_quality, OUT_RESOLUTION[resolution_key]) for img in img_list]
                with ThreadPool(10) as threadpool:
                    pool_ret = threadpool.starmap(self._add_watermark, args)
                self._save_record()
                img_list = np.array(img_list)
                ret = img_list[~np.array(pool_ret)].tolist()
                if ret:
                    return 1, ret
                else:
                    return 0, ret
            else:
                print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未找到照片!")
                return 2, []
    
    def run2(self, files: list, brand: str, model: str, len: str, out_dir: str=DEFAULT_OUT_DIR, out_format: str='jpg', out_quality: int=100, resolution: str='原图分辨率'):
        exif_data = {}
        exif_data['CameraMaker'] = brand
        exif_data['Camera'] = model
        exif_data['LenModel'] = len
        for file in files:
            self._add_watermark2(exif_data, file, out_dir, out_format, out_quality, OUT_RESOLUTION[resolution])

    def _load_images(self, in_path: str) -> list:
        if os.path.isdir(in_path):
            img_list =  self._get_all_imagefiles(in_path)
        else:
            img_list = [in_path]
        return img_list
    
    def _get_all_imagefiles(self, dir: str) -> list:
        files_list = []
        for root, _, files in os.walk(dir):
            for file in files:
                if os.path.splitext(file)[-1] in SUPPORT_IN_FORMAT:
                    new_file = os.path.join(root, file)
                    new_file = new_file.replace('\\', '/')
                    files_list.append(new_file)
        return files_list
        
    def _get_exif(self, image_file: str) -> dict:
        ret = {}
        f = open(image_file, 'rb')
        tags = exifread.process_file(f)

        tmp = str(tags.get("Image Make", ""))
        if tmp == "":
            return {}
        else:
            ret['CameraMaker'] = tmp 

        ret['Camera'] = str(tags.get("Image Model", ""))

        if ret['CameraMaker'].upper() == "XIAOMI":
            ret['Camera'] = str(tags.get("EXIF Tag 0x9A00")).upper()

        ret['LenModel'] = str(tags.get("EXIF LensModel", ""))
        
        tmp = str(tags.get("EXIF DateTimeOriginal", ""))
        tmp = tmp.split(" ")
        date = tmp[0]
        date = date.replace(':', '.')
        time = tmp[1]
        ret['DateTime'] = F"{date} {time}"

        latitude = str(tags.get("GPS GPSLatitude", ""))
        longitude = str(tags.get("GPS GPSLongitude", ""))
        if latitude and longitude:
            latitude = latitude.replace('[', '').replace(']', '').split(',')
            tmp = latitude[2].split('/')
            latitude[2] = int(tmp[0]) / int(tmp[1])
            longitude = longitude.replace('[', '').replace(']', '').split(',')
            tmp = longitude[2].split('/')
            longitude[2] = int(tmp[0]) / int(tmp[1])
            ret['Location'] = F"{int(latitude[0])}°{int(latitude[1])}′{int(latitude[2])}″{str(tags.get('GPS GPSLatitudeRef'))} {int(longitude[0])}°{int(longitude[1])}′{int(longitude[2])}″{str(tags.get('GPS GPSLongitudeRef'))}"
        else:
            ret['Location'] = ""

        ret['ExposureTime'] = str(tags.get("EXIF ExposureTime", ""))
        ret['FNumber'] = str(tags.get("EXIF FNumber", ""))
        if '/' in ret['FNumber']:
            f_num = ret['FNumber'].split('/')
            ret['FNumber'] = int(f_num[0]) / int(f_num[1])
        ret['ISO'] = str(tags.get("EXIF ISOSpeedRatings", ""))
        ret['FocalLength'] = str(tags.get("EXIF FocalLength", ""))
        if '/' in ret['FocalLength']:
            f_num = ret['FocalLength'].split('/')
            ret['FocalLength'] = int(f_num[0]) / int(f_num[1])
        ret['35mmFilm'] = str(tags.get("EXIF FocalLengthIn35mmFilm", ""))
        ret['XResolution'] = int(str(tags.get("Image XResolution", "0")))
        ret['YResolution'] = int(str(tags.get("Image YResolution", "0")))
        ret["Artist"] = str(tags.get("Image Artist", ""))
        return ret

    def _add_watermark(self, image_file: str, out_dir: str, out_format: str, out_quality: int, resolution: int) -> bool:
        image_name = os.path.splitext(os.path.basename(image_file))
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在处理:{image_name[0]}{image_name[1]}\n", end='')

        exif_data = self._get_exif(image_file)

        if not exif_data:
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {image_name[0]}{image_name[1]} 没有exif数据!\n", end='')
            return False

        img = Image.open(image_file)
        img = ImageOps.exif_transpose(img)
        img_width, img_height = img.size
        # if resolution != 0 and img_width <= img_height and img_width != resolution:
        #     img = img.resize((resolution, int(img_height / img_width * resolution)))
        # elif resolution != 0 and img_width >= img_height and img_height != resolution:
        #     img = img.resize((int(img_width / img_height * resolution), resolution))
        # img_width, img_height = img.size

        margin = int(self.margin_ratio * max(img_width, img_height))
        watermark_height = int(self.watermark_ratio * max(img_width, img_height))
        watermark_margin = int(watermark_height * 0.3)
        if watermark_margin < margin:
            watermark_margin = margin
        content_height = watermark_height - watermark_margin * 2
        guideline_logo_margin = int(self.guideline_logo_margin_ratio * content_height)

        new_height = margin + img_height + watermark_height
        new_width = margin + img_width + margin
        background_img = Image.new("RGB", (new_width, new_height), 'white')

        # draw img
        background_img.paste(img, (margin, margin))

        # judge logo
        brand = exif_data['CameraMaker'].split(' ')[0]
        brand = brand.title()
        if brand == 'Xiaomi':
            brand = 'Leica'
        logo_file = os.path.join(ROOT_PATH, 'resources', 'logos', F"{brand}.png")
        if not os.path.exists(logo_file):
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {brand}'s logo doesn't exist.\n", end='')
            return False

        # draw text
        left_text_1 = exif_data['Camera']
        left_text_2 = exif_data['LenModel']

        # 等效焦距
        right_text_1 = F"{exif_data['35mmFilm']}mm f/{exif_data['FNumber']} {exif_data['ExposureTime']}s ISO{exif_data['ISO']}"
        right_text_2 = exif_data['DateTime']

        draw = ImageDraw.Draw(background_img)

        font_file_1 = os.path.join(ROOT_PATH, 'resources', 'fonts', 'MiSans-Demibold.ttf')
        font_pt_1 = int(content_height * self.font_1_ratio)
        font_1 = ImageFont.truetype(font_file_1, font_pt_1)

        font_file_2 = os.path.join(ROOT_PATH, 'resources', 'fonts', 'MiSans-Regular.ttf')
        font_pt_2 = int(content_height * self.font_2_ratio)
        font_2 = ImageFont.truetype(font_file_2, font_pt_2)
        
        text_1_top = new_height - watermark_height + watermark_margin
        text_2_baseline = new_height - watermark_margin
        draw.text((watermark_margin, text_1_top), left_text_1, fill='black', anchor="lt", font=font_1)
        draw.text((watermark_margin, text_2_baseline), left_text_2, fill='#888888', anchor="ls", font=font_2)

        draw.text((new_width - watermark_margin, text_1_top), right_text_1, fill='black', anchor="rt", font=font_1)
        r_text_1_width = int(font_1.getlength(right_text_1))
        draw.text((new_width - watermark_margin - r_text_1_width, text_2_baseline), right_text_2, fill='#888888', anchor="ls", font=font_2)

        # draw guideline
        guideline_width = int(0.0012 * max(img_width, img_height))
        guideline = Image.new("RGB", (guideline_width, content_height), "#D0D0D0")
        guideline_left = new_width - watermark_margin - r_text_1_width - guideline_logo_margin
        guideline_top = text_1_top
        background_img.paste(guideline, (guideline_left, guideline_top))

        # draw logo
        logo_img = Image.open(logo_file)
        logo_img = logo_img.convert("RGBA")
        logo_img = logo_img.resize((content_height, content_height), Image.LANCZOS)

        logo_left = new_width - watermark_margin - r_text_1_width - 2 * guideline_logo_margin - content_height
        logo_top = text_1_top
        r, g, b, a = logo_img.split()
        background_img.paste(logo_img, (logo_left, logo_top), mask=a)

        img_width, img_height = background_img.size
        if resolution != 0 and img_width <= img_height and img_width != resolution:
            background_img = background_img.resize((resolution, int(img_height / img_width * resolution)))
        elif resolution != 0 and img_width >= img_height and img_height != resolution:
            background_img = background_img.resize((int(img_width / img_height * resolution), resolution))

        # 保存修改后的图片
        out_filename = os.path.join(out_dir, F"Mark_{image_name[0]}.{out_format}")
        background_img.save(out_filename, dpi=(300, 300), quality=out_quality)
        self._update_record(exif_data)
        return True

    def _add_watermark2(self, exif_data: dict, image_file: str, out_dir: str, out_format: str, out_quality: int, resolution: str) -> None:
        image_name = os.path.splitext(os.path.basename(image_file))
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在处理:{image_name[0]}{image_name[1]}")

        img = Image.open(image_file)
        img = ImageOps.exif_transpose(img) 
        img_width, img_height = img.size
        # if resolution != 0 and img_width <= img_height and img_width != resolution:
        #     img = img.resize((resolution, int(img_height / img_width * resolution)))
        # elif resolution != 0 and img_width >= img_height and img_height != resolution:
        #     img = img.resize((int(img_width / img_height * resolution), resolution))
        # img_width, img_height = img.size

        margin = int(self.margin_ratio * max(img_width, img_height))
        watermark_height = int(self.watermark_ratio * max(img_width, img_height))
        watermark_margin = int(watermark_height * 0.3)
        if watermark_margin < margin:
            watermark_margin = margin
        content_height = watermark_height - watermark_margin * 2
        guideline_logo_margin = int(self.guideline_logo_margin_ratio * content_height)

        new_height = margin + img_height + watermark_height
        new_width = margin + img_width + margin
        background_img = Image.new("RGB", (new_width, new_height), 'white')

        # draw img
        background_img.paste(img, (margin, margin))

        # judge logo
        brand = exif_data['CameraMaker'].split(' ')[0]
        brand = brand.title()
        if brand == 'Xiaomi':
            brand = 'Leica'
        logo_file = os.path.join(ROOT_PATH, 'resources', 'logos', F"{brand}.png")
        if not os.path.exists(logo_file):
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {brand}'s logo doesn't exist.\n", end='')
            return False

        # draw guideline
        guideline_width = int(0.0012 * max(img_width, img_height))
        guideline_length = watermark_height - 2 * watermark_margin
        guideline = Image.new("RGB", (guideline_width, guideline_length), "#D0D0D0")
        guideline_left = int(new_width / 2)
        guideline_top = new_height - watermark_height + watermark_margin
        background_img.paste(guideline, (guideline_left, guideline_top))

        # draw logo
        logo_img = Image.open(logo_file)
        logo_img = logo_img.convert("RGBA")
        logo_img = logo_img.resize((content_height, content_height), Image.LANCZOS)

        logo_left = guideline_left - guideline_logo_margin - content_height
        logo_top = guideline_top
        r, g, b, a = logo_img.split()
        background_img.paste(logo_img, (logo_left, logo_top), mask=a)

        # draw text
        right_text_1 = exif_data['Camera']
        right_text_2 = exif_data['LenModel']
        if not right_text_2:
            right_text_2 = time.strftime("%Y.%m.%d", time.localtime()) 

        draw = ImageDraw.Draw(background_img)

        font_file_1 = os.path.join(ROOT_PATH, 'resources', 'fonts', 'MiSans-DemiBold.ttf')
        font_pt_1 = int(content_height * self.font_1_ratio)
        font_1 = ImageFont.truetype(font_file_1, font_pt_1)

        font_file_2 = os.path.join(ROOT_PATH, 'resources', 'fonts', 'MiSans-Regular.ttf')
        font_pt_2 = int(content_height * self.font_2_ratio)
        font_2 = ImageFont.truetype(font_file_2, font_pt_2)
        
        text_1_left = guideline_left + guideline_logo_margin
        text_1_top = guideline_top
        text_2_baseline = new_height - watermark_margin
        draw.text((text_1_left, text_1_top), right_text_1, fill='black', anchor="lt", font=font_1)
        draw.text((text_1_left, text_2_baseline), right_text_2, fill='#888888', anchor="ls", font=font_2)

        img_width, img_height = background_img.size
        if resolution != 0 and img_width <= img_height and img_width != resolution:
            background_img = background_img.resize((resolution, int(img_height / img_width * resolution)))
        elif resolution != 0 and img_width >= img_height and img_height != resolution:
            background_img = background_img.resize((int(img_width / img_height * resolution), resolution))

        # 保存修改后的图片
        out_filename = os.path.join(out_dir, F"Mark_{image_name[0]}.{out_format}")
        background_img.save(out_filename, dpi=(300, 300), quality=out_quality)