from botocore.docs.paginator import os
from fastapi import APIRouter,Depends,HTTPException

from src.lib.blur_image import blur_image, blur_image_with_filter
from src.lib.constants import base_api_path
from src.lib.download_file import download_file
from src.lib.upload_file import upload_file
from src.main import INPUT_IMAGES_DIR, OUTPUT_IMAGES_DIR
from src.middlewares.auth_middleware import InternalAuthorization
from src.schemas.blur_photo_schemas import BlurEveryoneFilteredRequest, BlurEveryoneRequest
from src.types.base_response import BaseResponse


router = APIRouter(
    prefix=base_api_path+"/blur-photo",
    dependencies=[Depends(InternalAuthorization)]
)

@router.post("/everyone")
def blur_everyone(Body:BlurEveryoneRequest)->BaseResponse:
    output_path = os.path.join(OUTPUT_IMAGES_DIR, Body.output_key)
    input_path = os.path.join(INPUT_IMAGES_DIR, Body.img_key)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    image = download_file(file_key=Body.img_key,file_path=input_path)
    blur_image(blur_type=Body.blur_method, img=image,output_path=output_path)
    upload_file(file_key=Body.output_key, file_path=output_path)
    os.remove(input_path)
    return BaseResponse(success=True)
@router.post("/everyone/filtered")
def blur_everyone_filtered(Body:BlurEveryoneFilteredRequest)->BaseResponse:
    output_path = os.path.join(OUTPUT_IMAGES_DIR, Body.output_key)
    input_path = os.path.join(INPUT_IMAGES_DIR, Body.img_key)
    face_path =  os.path.join(INPUT_IMAGES_DIR, Body.face_key)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    os.makedirs(os.path.dirname(face_path), exist_ok=True)
    image = download_file(file_key=Body.img_key,file_path=input_path)
    face = download_file(file_key=Body.face_key,file_path=face_path)
    blur_image_with_filter(blur_type=Body.blur_method, img=image,output_path=output_path,face_id=face)
    upload_file(file_key=Body.output_key, file_path=output_path)
    os.remove(input_path)
    return BaseResponse(success=True)
