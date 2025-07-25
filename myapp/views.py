from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Product, Category, Brand, Wishlist, User, Order, OrderItem
from django.db.models import Q
from myapp.models import Category

from datetime import timedelta
from django.utils import timezone
from .forms import RegistrationForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import *
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
User = get_user_model()
from django.forms.models import model_to_dict

#.generic包含了ListView顯示資料清單/DetailView顯示單一資料詳情/CreateView表單建立資料/UpdateView表單更新資料/DeleteView刪除資料並轉跳

# 首頁視圖：顯示所有啟用的商品（對應 home.html）
def home(request):
    
    categories = [
        ('帳篷類Tent', 1),
        ('寢具類Bed', 2),
        ('廚具類KitchenWare', 3),
        ('爐具類Pot', 4),
        ('桌椅類Tables/Chairs', 5),
        ('燈具類Lamp', 6),
        ('保冷類Cooling', 7),
        ('保暖類Warming', 8),
        ('收納類Containers', 9),
        ('其他小物Others', 10),
    ]
    category_products = {}
    for name, cat_id in categories:
        category_products[cat_id] = Product.objects.filter(category_id=cat_id)

    return render(request, 'home.html', {
        'categories': categories,
        'category_products': category_products,
        
    })




def new_products(request):
    recent_days = 90  # 可調整為 7、14、30 天
    new_products = Product.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=recent_days)
    ).order_by('-created_at')

    return render(request, 'products/new_products.html', {
        'new_products': new_products,
        'recent_days': recent_days,
    })


# 商品列表（支援分類、品牌、關鍵字搜尋）
class ProductListView(ListView):
    model = Product # 這個 ListView 使用的模型是 Product
    template_name = 'products/product_list.html'  # 對應的 HTML 模板檔案
    context_object_name = 'products'  # 在模板中可用變數名稱為 products
    paginate_by = 12  # 每頁顯示 12 個產品

    def get_queryset(self): # 覆寫 get_queryset 方法：決定要顯示哪些商品
        # 初始只取出啟用中的商品
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')

        # 篩選參數 從網址參數中取得使用者輸入的篩選條件
        category_id = self.request.GET.get('category')
        brand_id = self.request.GET.get('brand')
        keyword = self.request.GET.get('q') #對應到product_list name='q'

        # 若有選擇分類，則篩選對應分類的商品
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
        # 若有輸入關鍵字，則從產品名稱中模糊搜尋
        if keyword:
            queryset = queryset.filter(product_name__icontains=keyword)

        return queryset.order_by('product_name')

    # 加入額外變數提供給模板使用（例如：分類清單、品牌清單等）
    def get_context_data(self, **kwargs):
        # 先取得預設 context（包含分頁資訊等)
        context = super().get_context_data(**kwargs)
        # 加入自訂變數到 context 中
        context['all_categories'] = Category.objects.all()
        context['all_brands'] = Brand.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_brand'] = self.request.GET.get('brand', '')
        context['keyword'] = self.request.GET.get('q', '')

        return context
    
    


# # 商品詳情頁：顯示單一商品的詳細資訊
class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()  # 取得當前商品

        if self.request.user.is_authenticated:
            user = self.request.user
            # 直接使用 request.user 判斷是否已加入最愛
            context['is_favorited'] = Wishlist.objects.filter(user=user, product=product).exists()
        else:
            context['is_favorited'] = False

        return context



#露營活動
def activity(request):
    return render(request, 'activity.html') 

#連絡資訊
def shoppingNotice(request):
    return render(request, 'shoppingNotice.html')  
#公司地點
def locations(request):
    return render(request, 'locations.html')   
#退貨規定公告
def returnNotice(request):
    return render(request, 'returnNotice.html') 

#-----------------------------------------------------------------
#會員區設定

#登入
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings

def userlogin(request):
    next_url = request.GET.get('next', '/home/')  # 沒有 next 就回首頁

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        print(f"DEBUG: authenticate 回傳 user = {user}")

        if user is not None:
            login(request, user)

            # 防止 open redirect 攻擊，確保 next_url 合法
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            else:
                return redirect('/home/')
        else:
            messages.error(request, '❌登入失敗，帳號或密碼錯誤！')
            return render(request, 'userlogin.html', {'next': next_url})

    return render(request, 'userlogin.html', {'next': next_url})

#註冊=#增加使用者useradd
def register(request): 
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        repassword = request.POST.get("repassword")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")  #補address
        print(f"username={username},password={password},repassword={repassword},email={email},phone={phone},address={address}")
        #User = get_user_model()
        #檢查帳號是否存在
        if User.objects.filter(username=username).exists():
            messages.error(request, "帳號己被使用,請重新填寫")
            return render(request, "register.html")
         #檢查密碼否一致
        if password != repassword:
            messages.error(request, "密碼輸入不同,請重新輸入")
            return render(request, "register.html")

        #驗證成功
        user = User.objects.create_user(username=username,password=password,email=email)
        user.is_staff=False
        user.is_active=True
        user.phone = phone
        user.address = address
        user.save()
        messages.success(request,"註冊成功,請登入,將為您導向登入頁面")
        return redirect("userlogin")

    else:
        return render(request, "register.html")

def user_edit(request,id=None):
    print(f"id={id}")
    user = request.user
    if request.method == "POST":
        username = request.POST["username"]
        email =request.POST["email"]
        phone =request.POST["phone"]
        address =request.POST["address"]   #以上是post收到資料,再次定義給變數
        print(f"cName={username},cEmail={email},cPhone={phone},cAddr={address}")
        #ORM
        update = User.objects.get(id=id)   #以下是更新至資料庫的動作
        update.username = username
        update.email = email
        update.phone = phone
        update.address = address
        update.save()
        return redirect("/user_info/") #更新完回首頁
        #return HttpResponse(f"HeLlo{cName}己更新完成")
    else:
        obj_data = User.objects.get(id=id)
        print(model_to_dict(obj_data))
        return render(request, "user_edit.html",locals())

#登出
def logout_user(request):
    logout(request)              #會清除 session，登出目前的使用者
    return redirect('home')

#使用者介面
@login_required
def user_info(request):
    user = request.user  # 已是自訂的 User 實例（含 phone、address）

    # 最愛商品
    favorites = Wishlist.objects.filter(user=user)

    # 訂單及關聯商品
    orders = Order.objects.filter(user=user).prefetch_related('orderitem_set', 'orderitem_set__product')

    return render(request, 'user_info.html', {
        'user': user,
        'orders': orders,
        'favorites': favorites,
    })



#使用者介面修改密碼
@login_required
def custom_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # 保持登入狀態
            messages.success(request, '✅ 密碼已成功更新！')
            return redirect('user_info')  # 修改為你要導向的頁面
        else:
            messages.error(request, '❌ 發生錯誤，請確認欄位是否正確填寫。')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'reset/my_password_change_form.html', {
        'form': form
    })



#購物車--------------------------------------------------------------------
def add_to_cart(request, product_id):
    cart = request.session.get("cart", {})
    product = get_object_or_404(Product, pk=product_id)

    # 取得第一張圖片
    first_image = product.images.first()
    image_url = first_image.image.url if first_image else ""

    if str(product_id) not in cart:
        cart[str(product_id)] = {
            "quantity": 1,
            "product_name": product.product_name,
            "price": int(product.price),
            "image": image_url,  # ✅ 儲存圖片 URL
        }
    else:
        cart[str(product_id)]["quantity"] += 1

    request.session["cart"] = cart
    request.session.modified = True
    return redirect('view_cart')


def view_cart(request):
    session_cart = request.session.get('cart', {})
    cart_items = {}
    total = 0

    for product_id, item in session_cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            price = int(item.get('price', product.price) or 0)
            quantity = int(item.get('quantity', 0) or 0)
            subtotal = price * quantity

            # 重新抓取圖片
            first_image = product.images.first()
            image_url = first_image.image.url if first_image else (product.image.url if product.image else "")

            cart_items[product_id] = {
                'product_name': product.product_name,
                'price': price,
                'quantity': quantity,
                'subtotal': subtotal,
                'image': image_url,
            }

            total += subtotal

        except Product.DoesNotExist:
            continue  # 商品已刪除的情況略過
        except Exception as e:
            print(f"[ERROR] 載入商品 {product_id} 發生錯誤: {e}")

    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'cart.html', context)


def clear_cart(request):
    if request.method == "POST":
        request.session["cart"] = {}
        request.session.modified = True
        request.session['flash_message'] = "🧹 購物車已成功清空。"
        request.session['flash_level'] = "success"
    else:
        request.session['flash_message'] = "❌ 無效的請求方法。"
        request.session['flash_level'] = "error"
    return redirect('view_cart')


def update_cart(request):
    if request.method == "POST":
        cart = request.session.get("cart", {})

        for key, value in request.POST.items():
            if key.startswith("quantity_"):
                product_id = key.split("_", 1)[1]
                try:
                    quantity = int(value)
                    if quantity > 0 and product_id in cart:
                        cart[product_id]["quantity"] = quantity
                        cart[product_id]["subtotal"] = cart[product_id]["price"] * quantity  # 更新小計
                except ValueError:
                    continue

        request.session["cart"] = cart
        request.session.modified = True
        request.session["cart_count_item"] = sum(item["quantity"] for item in cart.values())

        if request.POST.get('go_to_checkout') == '1':
            return redirect('checkout')

    return redirect('view_cart')


def remove_from_cart(request, product_id):
    print(f"[DEBUG] method: {request.method}, product_id: {product_id}")
    if request.method == "POST":
        cart = request.session.get("cart", {})
        product_id_str = str(product_id)
        if product_id_str in cart:
            del cart[product_id_str]
            request.session["cart"] = cart
            request.session.modified = True
            print(f"Cart after deletion: {cart}")
            request.session['flash_message'] = "✅ 已成功移除商品。"
            request.session['flash_level'] = "success"
        else:
            request.session['flash_message'] = "⚠️ 找不到指定的商品，無法移除。"
            request.session['flash_level'] = "warning"
    else:
        request.session['flash_message'] = "❌ 無效的請求方法。"
        request.session['flash_level'] = "error"
    return redirect('view_cart')


def checkout(request):
    session_cart = request.session.get('cart', {})
    cart_items = {}
    total = 0
    for product_id, item in session_cart.items():
        price = int(item.get('price', 0) or 0)  #modify
        quantity = int(item.get('quantity', 0) or 0)
        subtotal = price * quantity
        cart_items[product_id] = {
            'product_name': item.get('product_name', '❌ 未知商品'),
            'price': price,
            'quantity': quantity,
            'subtotal': subtotal
        }
        total += subtotal
#-----------新增會員資料帶入-------------
    user_info = {}
    if request.user.is_authenticated:
        user_info = {
            'username': request.user.username,
            'phone': request.user.phone,
            'address': request.user.address,
        }
#-----------新增會員資料帶入-------------
    context = {
        'cart_items': cart_items,
        'total': total,
        'flash_message': request.session.pop('flash_message', None),
        'flash_level': request.session.pop('flash_level', 'info'),
    }
    return render(request, 'checkout.html', context)

#-----訂單---------------------------------------------------

from decimal import Decimal
from datetime import datetime
from uuid import uuid4

@login_required(login_url='userlogin')
def submit_order(request):
    if request.method == 'POST':
        user = request.user
        cart = request.session.get('cart', {})

        total_amount = Decimal('0.00')
        for product_id, item_info in cart.items():
            quantity = item_info.get('quantity', 0)
            product = Product.objects.get(pk=product_id)
            total_amount += product.price * quantity

        total_int = int(total_amount)

        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_address=request.POST.get('shipping_address'),
            shipping_city=request.POST.get('shipping_city', ''),
            shipping_state_province=request.POST.get('shipping_state_province', ''),
            shipping_zip_code=request.POST.get('shipping_zip_code', ''),
            shipping_country=request.POST.get('shipping_country', ''),
            payment_method=request.POST.get('payment_method', ''),
            order_status='待處理',
            payment_status='未支付',
        )
        order.save() 

        for product_id, item_info in cart.items():
            quantity = item_info.get('quantity', 0)
            product = Product.objects.get(pk=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price,
            )

        # 清空購物車
        request.session['cart'] = {}

        # 處理信用卡或 LINE Pay 金流
        if order.payment_method in ['信用卡', 'Line Pay']:
            # 選擇金流方式
            choose_payment = 'Credit' if order.payment_method == '信用卡' else 'LINEPay'

            # 產生交易代碼
            merchant_trade_no = generate_merchant_trade_no(order.order_id)
            order.merchant_trade_no = merchant_trade_no
            order.save()

            # 商品名稱字串
            item_name_str = '#'.join([
                f"{item.product.product_name} x {item.quantity} (${item.price_at_purchase})"
                for item in order.orderitem_set.all()
            ])

            # 綠界 API 參數
            data = {
                'MerchantID': settings.ECPAY_MERCHANT_ID,
                'MerchantTradeNo': merchant_trade_no,
                'MerchantTradeDate': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                'PaymentType': 'aio',
                'TotalAmount': str(total_int),
                'TradeDesc': '派森露營商城訂單',
                'ItemName': item_name_str,
                'ReturnURL': settings.ECPAY_RETURN_URL,
                'ChoosePayment': choose_payment,
                'ClientBackURL': f'{settings.SITE_URL}/order/success/{order.order_id}/',
            }

            # 產生 CheckMacValue
            data['CheckMacValue'] = generate_check_mac_value(
                data, settings.ECPAY_HASH_KEY, settings.ECPAY_HASH_IV
            )

            # 自動送出的 HTML 表單
            form_html = "<form id='ecpay-form' method='post' action='https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'>"
            for k, v in data.items():
                form_html += f"<input type='hidden' name='{k}' value='{v}' />"
            form_html += "</form>"

            return render(request, 'payment.html', {'form_html': form_html})

        else:
            # 非金流付款（貨到付款）
            order.order_status = '已確認'
            order.payment_status = '已支付'
            order.save()
            return redirect('order_success', order_id=order.order_id)

    return redirect('checkout')


def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


def order_list(request):
    if request.user.is_authenticated:
        # 確保 request.user 是有效的 User 實例
        try:
            user = User.objects.get(username=request.user.username)  # 確保是有效的 User
            orders = Order.objects.filter(user=user)
        except User.DoesNotExist:
            orders = Order.objects.none()
    else:
        orders = Order.objects.none()  # 如果未登入，返回空訂單
    
    return render(request, "order_list.html", {"orders": orders})

#-------------------加入收藏功能---------------------------------

from django.contrib.auth import REDIRECT_FIELD_NAME
def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        login_url = f"/userlogin/?{REDIRECT_FIELD_NAME}=/user_info/#wishlist"
        return JsonResponse({'redirect': login_url}, status=401)

    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)
        user = request.user  # ← 直接使用登入者
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)

        if not created:
            wishlist_item.delete()
            status = 'removed'
        else:
            status = 'added'

        return JsonResponse({'status': status})

    return JsonResponse({'error': 'Invalid request'}, status=400)


#--------------------------------------------------------
from django.views.decorators.csrf import csrf_exempt
import hashlib
import urllib.parse

#金流
@csrf_exempt
def ecpay_return(request):
    if request.method == 'POST':
        data = request.POST.dict()
        print("🌿 收到綠界回傳資料：", data)

        rtn_code = data.get('RtnCode')
        merchant_trade_no = data.get('MerchantTradeNo')

        if not merchant_trade_no:
            return HttpResponse('0|No MerchantTradeNo')

        try:
            order = Order.objects.get(merchant_trade_no=merchant_trade_no)
        except Order.DoesNotExist:
            print("⚠️ 找不到對應的訂單")
            return HttpResponse('0|Order Not Found')

        if rtn_code == '1':  # 綠界付款成功
            order.payment_status = '已支付'
            order.order_status = '已確認'
            order.save()
            print(f"✅ 成功更新訂單 {order.order_id} 為已支付")

        return HttpResponse('1|OK')


def generate_check_mac_value(params, hash_key, hash_iv):
    sorted_params = sorted((k, v) for k, v in params.items() if k != 'CheckMacValue')
    param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    raw = f"HashKey={hash_key}&{param_str}&HashIV={hash_iv}"
    encoded = urllib.parse.quote_plus(raw, safe='').lower()

    replacements = {
        '%2d': '-', '%5f': '_', '%2e': '.', '%21': '!',
        '%2a': '*', '%28': '(', '%29': ')'
    }
    for key, val in replacements.items():
        encoded = encoded.replace(key, val)

    return hashlib.md5(encoded.encode('utf-8')).hexdigest().upper()


@login_required
def check_order_status(request, order_id):
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        return JsonResponse({
            'success': True,
            'payment_status': order.payment_status,
            'order_status': order.order_status
        })
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': '訂單不存在'})
    

def generate_merchant_trade_no(order_id):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"O{order_id}{timestamp}"[:20]


@csrf_exempt
def ecpay_notify(request):
    if request.method == 'POST':
        merchant_trade_no = request.POST.get('MerchantTradeNo')
        rtn_code = request.POST.get('RtnCode')  # 1 = 成功

        if rtn_code == '1':
            try:
                order = Order.objects.get(merchant_trade_no=merchant_trade_no)
                print(f"✅ 綠界付款成功，更新訂單 {order.order_id}")
                order.payment_status = '已支付'
                order.order_status = '已確認'
                order.save()
            except Order.DoesNotExist:
                print(f"⚠️ 綠界回傳失敗：RtnCode={rtn_code}")

        return HttpResponse('1|OK')
    

#小圓圈
@csrf_exempt
def update_cart_quantity(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        if product_id in cart:
            cart[product_id]['quantity'] = quantity
            request.session['cart'] = cart
        return JsonResponse({'status': 'ok', 'quantity': quantity})
    return JsonResponse({'status': 'error'}, status=400)

