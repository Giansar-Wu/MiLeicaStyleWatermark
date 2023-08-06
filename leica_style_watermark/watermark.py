import os
import math
from PIL import Image, ImageDraw, ImageFont, ExifTags
import exifread

from pillow_heif import register_heif_opener

register_heif_opener()

PATH = os.path.abspath(os.path.dirname(__file__))
USER_PATH = os.path.expanduser('~')
ROOT_PATH = os.path.dirname(PATH)
DEFAULT_OUT_DIR = os.path.join(USER_PATH, 'Desktop', 'Output')
SUPPORT_IN_FORMAT = ['.jpg', '.png', '.heic']
SUPPORT_OUT_FORMAT = ['jpg', 'png']
PHONE = {'2112123AC':'Xiaomi 12X'}

class LogoDontExistError(Exception):
    pass

class WaterMarkAgent(object):
    def __init__(self) -> None:
        self._logos = self._get_logo()
        self._img_list = []
        self._artist = ''
        self._path = ''
        self._out_dir = DEFAULT_OUT_DIR
        self._out_format = 'jpg'
        self._out_quality = 100
        
    def set_cfg(self, cfg: dict) -> None:
        self._path = cfg['path']
        if os.path.isdir(cfg['out_dir']):
            self._out_dir = cfg['out_dir']
        self._artist = cfg['artist']
        if cfg['out_format'] in SUPPORT_OUT_FORMAT:
            self._out_format = cfg['out_format']
        if cfg['out_quality'] > 100:
            self._out_quality = 100
        elif cfg['out_quality'] < 0:
            self._out_quality = 0
        else:
            self._out_quality = cfg['out_quality']

    def run(self) -> None:
        print(F"Out dir:{self._out_dir}")
        print(F"Out format:{self._out_format}")
        if self._out_format == 'jpg':
            print(F"Out quality:{self._out_quality}")
        self._load_images()
        for img in self._img_list:
            self._add_watermark(img)

    def _load_images(self) -> None:
        if isinstance(self._path, str):
            if os.path.isdir(self._path):
                img_list =  self._get_all_images(self._path)
            else:
                img_list = [self._path]
        else:
            img_list = []
            for path in self._path:
                if os.path.isdir(path):
                    tmp = self._get_all_images(path)
                    img_list.extend(tmp)
                else:
                    img_list.append(path)
        self._img_list = img_list
    
    def _get_all_images(self, dir: str) -> list:
        files_list = []
        for root, _, files in os.walk(dir):
            for file in files:
                if os.path.splitext(file)[-1] in SUPPORT_IN_FORMAT:
                    files_list.append(os.path.join(root, file))
        return files_list
        
    def _get_exif(self, image_file: str) -> dict:
        ret = {}
        f = open(image_file, 'rb')
        tags = exifread.process_file(f)
        # for tag in tags.keys():
        #     if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
        #         print(F"{tag}:{tags[tag]}")
        ret['CameraMaker'] = str(tags.get("Image Make", ""))
        if ret['CameraMaker'] == "":
            return ret
        ret['Camera'] = str(tags.get("Image Model", ""))
        if ret['Camera'] in PHONE.keys():
            ret['Camera'] = PHONE[ret['Camera']]
        ret['LenModel'] = str(tags.get("EXIF LensModel", ""))
        ret['DateTime'] = str(tags.get("EXIF DateTimeOriginal", ""))
        datetime = ret['DateTime'].split(" ")
        date = datetime[0]
        date = "/".join(date.split(":"))
        time = datetime[1]
        ret['DateTime'] = F"{date} {time}"
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

    def _get_logo(self) -> list:
        path = os.path.join(ROOT_PATH, 'resources', 'logos')
        logos_list = []
        for root, _, files in os.walk(path):
            for file in files:
                logos_list.append(os.path.join(root, file))
        return logos_list

    def _add_watermark(self, image_file: str) -> None:
        image_name = os.path.splitext(os.path.basename(image_file))
        print(F"正在处理:{image_name[0]}{image_name[1]}")
        if not os.path.exists(self._out_dir):
            os.makedirs(self._out_dir)
        exif_data = self._get_exif(image_file)

        if exif_data['CameraMaker'] == "":
            print(F"{image_name} doesn's has exif data!")
            return 0
        img = Image.open(image_file)
        exif=dict(img.getexif().items())
        # angles = [Image.ROTATE_90, Image.ROTATE_180, Image.ROTATE_270]
        for key in exif.keys():
            if key in ExifTags.TAGS.keys() and ExifTags.TAGS[key] == "Orientation":
                orientation = exif[key]
                if orientation == 3 : 
                    img = img.rotate(180, expand = True)
                elif orientation == 6 : 
                    img = img.rotate(270, expand = True)
                elif orientation== 8 : 
                    img = img.rotate(90, expand = True)
        img_width, img_height = img.size
        
        # 加水印后的图片从上到下的构成  margin + img_height + margin + margin_2 + watermark_height + margin_2 + margin
        # 第一行字体与水印区高度的比例
        font_1_ratio = 0.42
        # 第二行字体与水印区高度的比例
        font_2_ratio = 0.32
        # 最外侧边距与图片最长边的比例
        margin_ratio = 1/100 
        # 水印区高度与图片最长边的比例
        watermark_height_ratio = 1/24 
        # 水印区内边距与最外侧边距的比例
        margin_2_ratio = 0

        margin = int(margin_ratio * max(img_width, img_height))
        watermark_height = int(watermark_height_ratio * max(img_width, img_height))
        margin_2 = int(margin_2_ratio * margin)
        bottom = watermark_height + margin * 2 + margin_2 * 2

        # logo与水印区全高度的比例 0~1
        # logo_ratio = watermark_height / bottom
        logo_ratio = 0.8

        new_height = img_height + watermark_height + 3 * margin + 2 * margin_2
        new_width = img_width + 2 * margin
        background_img = Image.new("RGB", (new_width, new_height), 'white')

        # draw img
        background_img.paste(img, (margin, margin))

        # judge logo
        brand = exif_data['CameraMaker'].split(" ")[0]
        brand = brand.title()
        # brand = 'Sony'
        has_not_logo = True
        for logo in self._logos:
            if brand in os.path.basename(logo):
                logo_file = logo
                has_not_logo = False
        if has_not_logo:
            print(F"{brand}'s logo doesn't exist.")
            raise LogoDontExistError

        # draw text
        left_text_1 = F"{exif_data['Camera']}"
        left_text_2 = F"{exif_data['LenModel']}"
        # if exif_data['FocalLength'] != exif_data['35mmFilm']:
        #     right_text_1 = F"{exif_data['FocalLength']}mm({exif_data['35mmFilm']}mm)  f/{exif_data['FNumber']}  {exif_data['ExposureTime']}s  ISO-{exif_data['ISO']}"
        # else:
        #     right_text_1 = F"{exif_data['FocalLength']}mm  f/{exif_data['FNumber']}  {exif_data['ExposureTime']}s  ISO-{exif_data['ISO']}"
        right_text_1 = F"{exif_data['FocalLength']}mm  f/{exif_data['FNumber']}  {exif_data['ExposureTime']}s  ISO-{exif_data['ISO']}"
        right_text_2 = F"{exif_data['DateTime']}"
        if self._artist != '':
            right_text_3 = F"PHOTO BY {self._artist}"
        else:
            if exif_data['Artist'] != "":
                right_text_3 = F"PHOTO BY {exif_data['Artist']}"
            else:
                right_text_3 = ""

        draw = ImageDraw.Draw(background_img)

        font_file_1 = os.path.join(ROOT_PATH, 'resources', 'fonts', 'MiSans-Bold.ttf')
        font_pt_1 = int(watermark_height * font_1_ratio)
        font_1 = ImageFont.truetype(font_file_1, font_pt_1)

        font_file_2 = os.path.join(ROOT_PATH, 'resources', 'fonts', 'MiSans-Regular.ttf')
        font_pt_2 = int(watermark_height * font_2_ratio)
        font_2 = ImageFont.truetype(font_file_2, font_pt_2)
        
        text_1_top = new_height - margin - margin_2 - watermark_height
        text_2_baseline = new_height - margin - margin_2
        draw.text((margin, text_1_top), left_text_1, fill='black', anchor="lt", font=font_1)
        draw.text((margin, text_2_baseline), left_text_2, fill='gray', anchor="ls", font=font_2)

        draw.text((new_width - margin, text_1_top), right_text_1, fill='black', anchor="rt", font=font_1)
        r_text_1_width = int(font_1.getlength(right_text_1))
        draw.text((new_width - margin - r_text_1_width, text_2_baseline), right_text_2, fill='gray', anchor="ls", font=font_2)
        draw.text((new_width - margin, text_2_baseline), right_text_3, fill='gray', anchor="rs", font=font_2)

        # draw guideline
        guideline_length = watermark_height + 2 * margin_2 + margin
        guideline = Image.new("RGB", (5, guideline_length), "gray")
        guideline_left = new_width - margin - r_text_1_width - int(0.5 * margin)
        guideline_top = new_height - margin - 2 * margin_2 - watermark_height - int(margin / 2)
        background_img.paste(guideline, (guideline_left, guideline_top))

        # draw logo
        logo_img = Image.open(logo_file)
        logo_img = logo_img.convert("RGBA")
        logo_width, logo_height = logo_img.size
        h = bottom * logo_ratio
        logo_area_ratio = math.sqrt(h ** 2 / (logo_width * logo_height))
        logo_new_width = int(logo_width * logo_area_ratio)
        logo_new_height = int(logo_height * logo_area_ratio)
        logo_img = logo_img.resize((logo_new_width, logo_new_height), Image.LANCZOS)

        logo_left = new_width - 2 * margin - r_text_1_width - logo_new_width
        logo_top = int(new_height - bottom / 2 -  logo_new_height / 2)
        r, g, b, a = logo_img.split()
        background_img.paste(logo_img, (logo_left, logo_top), mask=a)

        # 保存修改后的图片
        out_filename = os.path.join(self._out_dir, F"Mark_{image_name[0]}.{self._out_format}")
        xy_resolution= (exif_data['XResolution'] if exif_data['XResolution'] < 300 else 300, exif_data['YResolution'] if exif_data['YResolution'] < 300 else 300)
        background_img.save(out_filename, dpi=xy_resolution, quality=self._out_quality)
