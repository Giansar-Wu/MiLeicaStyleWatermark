import watermark

def main(path: str | list[str], output_dir: str="", artist: str='', out_format: str='jpg', out_quality: int=80) -> None:
    """main funciton.

    Args:
        path (str | list[str]): A image's path or the directory of images or the list of image's paths and directories of images. 
        output_dir (str, optional): The directory where you want to save images with watermark. Defaults to "$HOME/Desktop/Output".
        artist (str, optional): The nickname that you want to cover image author with in watermark. Defaults to ''.
        out_format (str, optional): The format of images you want to save. Defaults to 'jpg'.
        out_quality (int, optional): The quality of images you want to save. Only useful when the out_format is 'jpg'. Defaults to 80.
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
    # please set the input
    input = ""
    output_dir = ""
    main(input, output_dir)