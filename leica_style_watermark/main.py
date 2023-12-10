import watermark
import os

def main(path: str | list[str], output_dir: str="", artist: str='', out_format: str='jpg', out_quality: int=100) -> None:
    """main funciton.

    Args:
        path (str | list[str]): A image's path or the directory of images or the list of image's paths and directories of images. 
        output_dir (str, optional): The directory where you want to save images with watermark. Defaults to "$HOME/Desktop/Output".
        artist (str, optional): The nickname that you want to cover image author with in watermark. Defaults to ''.
        out_format (str, optional): The format of images you want to save. Defaults to 'jpg'.
        out_quality (int, optional): The quality of images you want to save. Only useful when the out_format is 'jpg'. Defaults to 100.
    """    
    cfg = {}
    cfg['path'] = path
    cfg['out_dir'] = output_dir
    cfg['artist'] = artist
    cfg['out_format'] = out_format
    cfg['out_quality'] = out_quality
    agent = watermark.WaterMarkAgent()
    agent.set_cfg(cfg)
    agent.run()

if __name__ == "__main__":
    print(F"Please enter some configuration. (Default values will be used by typing enter.)")

    out_dir = input("The output directory(defaults:{}/Desktop/Output):".format(os.path.expanduser('~').replace('\\','/')))
    if not os.path.isdir(out_dir):
        out_dir = ""
    
    artist = input(F"The artist of photos(default:''):")

    out_format = input(F"The output format({watermark.SUPPORT_OUT_FORMAT} default:'jpg'):")
    if out_format == '':
        out_format = 'jpg'
    elif out_format not in watermark.SUPPORT_OUT_FORMAT:
        print(F"The format '{out_format}' are not supported, and 'jpg' will be used!")
        out_format = 'jpg'
    if out_format == 'jpg':
        out_quality = input(F"The quality of output images(0-95 default:80):")
        try:
            out_quality = int(out_quality)
            if (out_quality < 0) or (out_quality > 100):
                out_quality = 100
        except ValueError:
            out_quality = 100
            
    path = input(F"Input the path of images to be processed(input 'q' to exit):")
    while path != 'q':
        if os.path.isdir(path) or os.path.isfile(path):
            main(path, out_dir, artist, out_format, out_quality)
        else:
            print(F"Path '{path}' can't be identified!")
        path = input(F"Input the path of images to be processed(input 'q' to quit):")
    print(F"Exit!")