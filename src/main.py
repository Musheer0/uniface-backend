import os
from src.lib.blur_image import blur_image, blur_image_with_filter
from src.types.blur_types import BlurMethod
from src.lib.blur_video import blur_video, blur_video_filtered
from src.lib.blur_video_with_timestamps import blur_video_filtered_timestamp, blur_video_timestamps
def setup():
    os.makedirs("temp/outputs/videos")
    os.makedirs("temp/outputs/images")
    os.makedirs("temp/inputs/videos")
    os.makedirs("temp/inputs/images")







if __name__=="main":
    setup()
    
                                                                                                     