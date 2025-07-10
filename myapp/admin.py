from django.contrib import admin
from .models import Product, Category, User, Brand, Order, Review, ProductImage
from django.utils.html import format_html

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_preview']
    fields = ['image', 'alt_text', 'image_preview']  # 順序與欄位名稱

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px;">', obj.image.url)
        return "❌ 尚無圖片"

    image_preview.short_description = "圖片預覽"

class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_name', 'sku', 'price', 'stock_quantity', 
        'category', 'weight', 'dimensions', 'suitable_season', 'is_active'
    )
    list_editable = (
        'price', 'stock_quantity', 'category', 
        'weight', 'dimensions', 'suitable_season', 'is_active'
    )
    inlines = [ProductImageInline]
    list_filter = ('category', 'brand')
    search_fields = ('product_name', 'sku')
    ordering = ('product_id',)


class BrandAdmin(admin.ModelAdmin):
    list_display = ('brand_id','brand_name','description')
    list_editable = ( 'brand_name','description', )
    search_fields = ('brand_name',)
    list_filter = ('brand_name',)

class CategoryAdim(admin.ModelAdmin):
    list_display = ('category_id', 'category_name', 'description', 'parent_category')
    list_editable = ( 'category_name', 'description', )
    search_fields = ('category_name',)
    list_filter = ('category_name',)

class OrderAdim(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'order_date', 'total_amount','order_status')
    search_fields = ('order_id',)
    list_filter = ('order_id','user','order_date',)

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'address', 'is_staff', 'is_active')
    list_editable = ( 'is_staff', )
class ReviewAdim(admin.ModelAdmin):
    list_display = ('user','product','rating','comment','review_date')

admin.site.register(Product, ProductAdmin)
admin.site.register(Category,CategoryAdim)
admin.site.register(Brand,BrandAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Order,OrderAdim)
admin.site.register(Review,ReviewAdim)


#.............銷售數量統計....................
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F, ExpressionWrapper, IntegerField
import matplotlib
import matplotlib.pyplot as plt
import io, base64

# 設定中文字體
matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'
matplotlib.rcParams['axes.unicode_minus'] = False

@staff_member_required
def sales_stats_view(request):
    products = (
        Product.objects.annotate(
            total_quantity=Sum('orderitem__quantity'),
            total_revenue=Sum(
                ExpressionWrapper(F('orderitem__quantity') * F('orderitem__price_at_purchase'),
                                 output_field=IntegerField())
            )
        )
        .filter(total_quantity__isnull=False)
        .order_by('-total_quantity')[:10]
    )

    labels = [p.product_name for p in products]
    quantities = [p.total_quantity for p in products]
    revenues = [p.total_revenue or 0 for p in products]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(labels, quantities, color='mediumseagreen', label='銷售數量')
    ax2 = ax1.twinx()
    ax2.plot(labels, revenues, color='darkorange', marker='o', label='銷售金額')

    ax1.set_ylabel("銷售數量")
    ax2.set_ylabel("銷售金額")
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title("銷售前 10 名商品統計圖")

    buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()

    return TemplateResponse(request, "admin/sales_stats.html", {
        "image_base64": image_base64,
        #"title": "商品銷售統計圖"
    })

# 正確做法：不遞迴

original_get_urls = admin.site.get_urls

def get_extra_urls():
    return [
        path('sales-stats/', admin.site.admin_view(sales_stats_view), name='sales-stats'),
    ]

def custom_get_urls():
    return get_extra_urls() + original_get_urls()

admin.site.get_urls = custom_get_urls

