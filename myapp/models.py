from django.db import models
from django.contrib.auth.models import AbstractUser
#from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from cloudinary.models import CloudinaryField

class User(AbstractUser):
    phone = models.CharField(max_length=20, default='未提供電話')
    address = models.CharField(max_length=255, default='未提供地址')

    def __str__(self):
        return self.username

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.category_name

class Brand(models.Model):
    brand_id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.brand_name

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.IntegerField()                    #<<modify>>
    stock_quantity = models.IntegerField()
    #image = models.ImageField(upload_to='product_images/', blank=True, null=True)   #暫時別刪
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL)
    weight = models.CharField(max_length=100, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True)
    material = models.CharField(max_length=100, blank=True)
    suitable_season = models.CharField(max_length=50, blank=True)
    capacity = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

#--------------------產品圖片獨立出來------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('image')  #cloudinary setting
    #image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image for {self.product.product_name}"

#--------------------產品圖片獨立出來-------------------------


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('待處理', '待處理'),
        ('已確認', '已確認'),
        ('已發貨', '已發貨'),
        ('已完成', '已完成'),
        ('已取消', '已取消'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('未支付', '未支付'),
        ('已支付', '已支付'),
        ('退款中', '退款中'),
        ('已退款', '已退款'),
    ]

    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.IntegerField()                       #<<modify>>
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS_CHOICES, default='待處理')
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=50)
    shipping_state_province = models.CharField(max_length=50, blank=True)
    shipping_zip_code = models.CharField(max_length=10, blank=True)
    shipping_country = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='未支付')
    tracking_number = models.CharField(max_length=100, blank=True)
    merchant_trade_no = models.CharField(max_length=20, unique=True, blank=True, null=True)   #add
    # def __str__(self):
    #     return self.user 
    
    def __str__(self):
        return f"訂單 #{self.order_id} - {self.user.username}"  #大師建議更改
      

class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_purchase = models.IntegerField()                  #<<modify>>

class ShoppingCart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    review_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(rating__gte=1, rating__lte=5), name='rating_range')
        ]

#加入我的最愛
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # 每個人只能收藏一次同個商品

    def __str__(self):
        return self.product


    
