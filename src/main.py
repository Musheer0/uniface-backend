
from src.lib.blur_image import blur_image, blur_image_with_filter
from src.types.blur_types import BlurMethod
from src.lib.blur_video import blur_video, blur_video_filtered
from src.lib.blur_video_with_timestamps import blur_video_filtered_timestamp, blur_video_timestamps


blur_video_filtered(blur_type=BlurMethod.MEDIAN,output_path="demof.mp4",video_path="/home/muchi/Projects/blurfield/backend/test.mp4",faceId="/home/muchi/Projects/blurfield/backend/b.webp")