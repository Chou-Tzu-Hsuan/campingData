import os
import django
import cloudinary.uploader
from glob import glob

# 初始化 Django 環境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CampingData.settings")
django.setup()

from myapp.models import ProductImage

# 本機圖片資料夾
LOCAL_IMAGE_DIR = r"C:\Users\Usser\Pictures\product_images"

# 支援的副檔名
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.peg']

# 處理每個 ProductImage
for pi in ProductImage.objects.all():
    original_ref = str(pi.image)  # e.g. cloudinary ID 或 product_images/xxx
    basename = os.path.basename(original_ref)  # e.g. M-1328-01.PNG or coleman-table01

    name_no_ext = os.path.splitext(basename)[0]  # e.g. M-1328-01
    matched_path = None

    # 在本機資料夾中找匹配的檔案
    for ext in IMAGE_EXTENSIONS:
        candidate = os.path.join(LOCAL_IMAGE_DIR, name_no_ext + ext)
        if os.path.exists(candidate):
            matched_path = candidate
            break

    if matched_path:
        try:
            print(f"🚀 上傳中：{matched_path}")
            result = cloudinary.uploader.upload(matched_path)

            pi.image = result['public_id']  # 更新 CloudinaryField
            pi.save()

            print(f"✅ 成功更新：{basename}")
        except Exception as e:
            print(f"⚠️ 上傳錯誤 {basename}: {e}")
    else:
        print(f"❌ 找不到本機圖片：{name_no_ext}.*，跳過")

