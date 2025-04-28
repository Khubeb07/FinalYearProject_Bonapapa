# ------------------------------------
#               IMPORTS
# ------------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .forms import *
from .models import *

# Get the custom user model
User = get_user_model()


# ------------------------------------
#         HELPER FUNCTIONS
# ------------------------------------
def is_admin(user):
    return user.is_superuser or user.is_staff


# ------------------------------------
#         PUBLIC VIEWS
# ------------------------------------
def home_view(request):
    new_products = Product.objects.order_by('-created_at')[:6]  # Latest 6 products
    return render(request, 'mytemplates/home.html', {'new_products': new_products})


from django.db.models import Q

def product(request):
    query = request.GET.get('q')
    admin_products = Product.objects.filter(user__is_superuser=True)

    if query:
        admin_products = admin_products.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        )

    return render(request, 'mytemplates/product.html', {'products': admin_products})



def productpage(request):
    return render(request, 'mytemplates/productpage.html')


def contactus(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact')
        message = request.POST.get('message')

        if full_name and email and contact_number and message:
            ContactMessage.objects.create(
                full_name=full_name,
                email=email,
                contact=contact_number,
                message=message
            )
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contactus')
        else:
            messages.error(request, "Please fill out all the fields.")

    return render(request, 'mytemplates/contactus.html')


def aboutus(request):
    return render(request, 'mytemplates/aboutus.html')


def parenting(request):
    return render(request, 'mytemplates/parenting.html')


# ------------------------------------
#         AUTHENTICATION
# ------------------------------------
def login_view(request):
    form = LoginForm(request.POST or None)

    # Display message based on next URL
    if request.method == 'GET' and 'next' in request.GET:
        next_url = request.GET.get('next')
        if '/wishlist' in next_url:
            messages.info(request, "Please log in to view your wishlist.")
        elif '/cart' in next_url:
            messages.info(request, "Please log in to view your cart.")

    if request.method == 'POST':
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                auth_login(request, user)
                next_url = request.GET.get('next')
                return redirect(next_url or ('admin_dashboard' if is_admin(user) else 'home'))
            messages.error(request, "Invalid username or password.")

    return render(request, 'mytemplates/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        messages.error(request, "Please fix the errors below.")
    else:
        form = CustomUserRegistrationForm()
    return render(request, 'mytemplates/register.html', {'form': form})


def forgotpassword(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email)
            if users.exists():
                for user in users:
                    subject = "Password Reset - Bonapapa"
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    reset_url = request.build_absolute_uri(
                        reverse_lazy('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                    )
                    message = f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_url}"
                    send_mail(subject, message, 'noreply@bonapapa.com', [user.email])
                messages.success(request, "Password reset link sent! Please check your email.")
            else:
                messages.error(request, "No user found with that email.")
    else:
        form = PasswordResetForm()
    return render(request, 'mytemplates/forgotpassword.html', {'form': form})


def custom_reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = DjangoUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, DjangoUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        return render(request, 'mytemplates/password_reset_form.html', {'form': form})
    else:
        messages.error(request, 'The reset link is invalid or has expired.')
        return redirect('forgotpassword')


# ------------------------------------
#        CUSTOMER - WISHLIST
# ------------------------------------
@login_required
def wishlist_view(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'mytemplates/wishlist.html', {'wishlist_items': wishlist_items})


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Product, WishlistItem
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    exists = WishlistItem.objects.filter(user=request.user, product=product).exists()

    if exists:
        return JsonResponse({
            'status': 'exists',
            'message': f"{product.product_name} is already in your wishlist."
        })
    else:
        WishlistItem.objects.create(user=request.user, product=product)
        return JsonResponse({
            'status': 'added',
            'message': f"{product.product_name} added to your wishlist!"
        })


@login_required
def remove_wishlist_item(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    item.delete()
    return redirect('wishlist')


# ------------------------------------
#        CUSTOMER - CART
# ------------------------------------
@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'mytemplates/cart.html', {'cart_items': cart_items, 'total_price': total_price})


@require_POST
@login_required
def update_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        quantity = request.POST.get(f'quantity_{item.id}')
        size = request.POST.get(f'size_{item.id}')
        if quantity and int(quantity) > 0 and size:
            item.quantity = int(quantity)
            item.product.size = size
            item.product.save()
            item.save()
        else:
            messages.error(request, f"Invalid input for {item.product.product_name}.")
            return redirect('cart')
    messages.success(request, "Cart updated successfully.")
    return redirect('cart')


@require_POST
@login_required
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')


# ------------------------------------
#        CUSTOMER - ORDERS
# ------------------------------------

@login_required
def buy_now_checkout(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity'))
            size = request.POST.get('size')
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            payment_method = request.POST.get('payment_method')  # ✅ captured

            # Limit quantity to 5
            if quantity > 5:
                messages.error(request, "You cannot order more than 5 units of a product.")
                return redirect('product')

            product = get_object_or_404(Product, id=product_id)

            if quantity < 1:
                messages.error(request, "Quantity must be at least 1.")
                return redirect('product')

            # Ensure there's enough stock
            if product.quantity >= quantity:
                product.quantity -= quantity
                product.save()
            else:
                messages.error(request, f"Not enough stock for {product.product_name}.")
                return redirect('product')

            total_price = product.price * quantity

            # ✅ Create the order and SAVE payment method also
            Order.objects.create(
                user=request.user,
                product=product,
                quantity=quantity,
                total_price=total_price,
                status='pending',
                payment_method=payment_method,  # ✅ added here
            )

            messages.success(request, "Order placed successfully!")
            return redirect('user_orders')

        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('product')

    return redirect('product')


@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'mytemplates/orders.html', {'orders': orders})


# ------------------------------------
#          ADD TO CART
# ------------------------------------
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.warning(request, f"Added another {product.product_name} to your cart!")
    else:
        messages.success(request, f"{product.product_name} added to cart!")

    return redirect('product')  # o


# ------------------------------------
#         CUSTOMER - CHECKOUT
# ------------------------------------
@login_required
def checkout(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        payment_method = request.POST.get("payment_method")  # ✅ captured

        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        for item in cart_items:
            quantity = request.POST.get(f"quantity_{item.id}")
            if quantity is None or quantity == '':
                quantity = 1
            else:
                try:
                    quantity = int(quantity)
                    if quantity < 1:
                        raise ValueError("Quantity must be at least 1.")
                    if quantity > 5:
                        messages.error(request, f"You cannot order more than 5 units of {item.product.product_name}.")
                        return redirect('cart')
                except ValueError:
                    messages.error(request, f"Invalid quantity for {item.product.product_name}")
                    return redirect('cart')

            # ✅ Create the order and SAVE payment method also
            Order.objects.create(
                user=request.user,
                product=item.product,
                quantity=quantity,
                total_price=item.product.price * quantity,
                status='pending',
                payment_method=payment_method,  # ✅ added here
            )

            # Decrease the product's quantity after purchase
            product = item.product
            if product.quantity >= quantity:
                product.quantity -= quantity
                product.save()
            else:
                messages.error(request, f"Not enough stock for {product.product_name}.")
                return redirect('cart')

        cart_items.delete()
        messages.success(request, "Your order has been placed successfully!")
        return redirect('user_orders')

    return redirect('cart')



from django.db.models import Count
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Product, Order


# ------------------------------------
#             ADMIN VIEWS
# ------------------------------------
@user_passes_test(is_admin)
def admin_dashboard(request):
    user_counts = {
        'admin': User.objects.filter(is_superuser=True).count(),
        'staff': User.objects.filter(is_staff=True, is_superuser=False).count(),
        'customer': User.objects.filter(is_staff=False, is_superuser=False).count(),
    }
    order_status_counts = Order.objects.values('status').annotate(count=Count('status'))
    category_counts = Product.objects.values('category').annotate(count=Count('category'))

    context = {
        'total_users': User.objects.count(),
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'user_counts': user_counts,
        'order_status_counts': order_status_counts,
        'category_counts': category_counts,
    }
    return render(request, 'mytemplates/admin_dashboard.html', context)


@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all()
    context = {
        'users': users,
        'total_users': User.objects.count(),
        'total_products': Product.objects.count(),
        'total_wishlist': WishlistItem.objects.count(),
        'total_cart_items': CartItem.objects.count(),
        'total_orders': Order.objects.count(),
    }
    return render(request, 'mytemplates/admin_users.html', context)


@user_passes_test(is_admin)
def admin_products(request):
    products = Product.objects.filter(user__is_staff=True)
    return render(request, 'mytemplates/admin_products.html', {'products': products})


@user_passes_test(is_admin)
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'mytemplates/create_product.html', {'form': form})


@user_passes_test(is_admin)
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'mytemplates/update_product.html', {'form': form})


@user_passes_test(is_admin)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_products')
    return render(request, 'mytemplates/delete_product.html', {'product': product})


# ------------------------------------
#        ADMIN - ORDER MANAGEMENT
# ------------------------------------
@user_passes_test(is_admin)
def admin_all_orders(request):
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'mytemplates/admin_orders.html', {'orders': orders})


@user_passes_test(is_admin)
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    new_status = request.POST.get("status")

    if new_status in ['pending', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        order.save()
        messages.success(request, "Order status updated successfully.")
    else:
        messages.error(request, "Invalid status selected.")
    return redirect('admin_all_orders')

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ContactMessage

@login_required
def admin_messages_view(request):
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    paginator = Paginator(messages_list, 10)  # Show 5 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'mytemplates/admin_messages.html', {'page_obj': page_obj})

@login_required
def admin_messages_view(request):
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    paginator = Paginator(messages_list, 10)  # Show 5 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'mytemplates/admin_messages.html', {'page_obj': page_obj})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Chat

@login_required
def chat_page(request):
    chats = Chat.objects.order_by('-timestamp')[:50]  # Last 50 messages (optional limit)
    return render(request, 'mytemplates/chat_page.html', {'chats': chats})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import CustomUserForm

User = get_user_model()

# -------------------- LIST USERS --------------------
def user_list_view(request):
    if not request.user.is_superuser:
        return redirect('home')  # Or show permission denied
    users = User.objects.all()
    return render(request, 'mytemplates/admin_users.html', {'users': users})

# -------------------- CREATE USER --------------------
from django.contrib import messages

def user_create_view(request):
    if not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()  # Already sets password in the form
            messages.success(request, "User created successfully.")
            return redirect('admin_users')
        else:
            print(form.errors)  # For debugging
    else:
        form = CustomUserForm()

    return render(request, 'mytemplates/user_form.html', {'form': form})



# -------------------- EDIT USER --------------------
def user_edit_view(request, pk):
    if not request.user.is_superuser:
        return redirect('home')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('admin_users')
    else:
        form = CustomUserForm(instance=user)
    return render(request, 'mytemplates/user_form.html', {'form': form})

# -------------------- DELETE USER --------------------
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('admin_users')

def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    if request.method == 'POST':
        rating_val = request.POST.get('rating')
        review_text = request.POST.get('review')

        if rating_val and review_text:
            Rating.objects.create(
                product=product,
                user=request.user.username,
                rating=int(rating_val),
                review=review_text
            )
            messages.success(request, 'Thank you for your review!')

        return redirect('product_detail', product_id=product.id)

    return render(request, 'mytemplates/product_detail.html', {
        'product': product,
        'related_products': related_products
    })


@login_required
def profile_view(request):
    return render(request, 'mytemplates/profile.html', {'user': request.user})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import CustomUserUpdateForm

User = get_user_model()

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'mytemplates/edit_profile.html', {'form': form})

from django.http import JsonResponse
from .models import Coupon
from datetime import datetime
from django.utils import timezone

def apply_coupon(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code')

        try:
            coupon = Coupon.objects.get(coupon_code__iexact=coupon_code, is_used=False)
            if coupon.expiry_date < timezone.now():
                return JsonResponse({'success': False, 'message': 'Coupon expired.'})

            total_price = 0
            cart_items = CartItem.objects.filter(user=request.user)
            for item in cart_items:
                total_price += item.product.price * item.quantity

            discount_amount = total_price * (coupon.discount_percentage / 100)
            new_total = total_price - discount_amount

            return JsonResponse({
                'success': True,
                'discount': coupon.discount_percentage,
                'new_total': round(new_total, 2)
            })
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid or used coupon.'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})
from .models import Coupon



from .models import Coupon


from django.utils import timezone

@login_required
def admin_coupons(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('home')
    coupons = Coupon.objects.all().order_by('-expiry_date')
    now = timezone.now()
    return render(request, 'mytemplates/admin_coupons.html', {'coupons': coupons, 'now': now})


def add_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        discount_percentage = request.POST.get('discount_percentage')
        expiry_date = request.POST.get('expiry_date')

        # Check if coupon code already exists
        if Coupon.objects.filter(coupon_code__iexact=coupon_code).exists():
            messages.error(request, 'Coupon code already exists! Please use a different one.')
            return redirect('add_coupon')

        # Create new coupon
        coupon = Coupon(
            coupon_code=coupon_code,
            discount_percentage=discount_percentage,
            expiry_date=expiry_date
        )
        coupon.save()

        messages.success(request, 'Coupon added successfully!')
        return redirect('admin_coupons')

    return render(request, 'mytemplates/add_coupon.html')

def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    if request.method == 'POST':
        coupon.coupon_code = request.POST['coupon_code']
        coupon.discount_percentage = request.POST['discount_percentage']
        coupon.expiry_date = request.POST['expiry_date']
        coupon.save()
        messages.success(request, 'Coupon updated successfully!')
        return redirect('admin_coupons')

    return render(request, 'mytemplates/edit_coupon.html', {'coupon': coupon})


def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, coupon_id=coupon_id)
    coupon.delete()
    messages.success(request, 'Coupon deleted successfully!')
    return redirect('admin_coupons')



from django.db.models import Sum
from django.utils import timezone
from django.http import HttpResponse
import csv

from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Order

@login_required
def admin_payment_report(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('home')

    # ✅ Latest orders first (NEW)
    orders = Order.objects.all().order_by('-order_date')

    # Filtering
    selected_method = request.GET.get('method')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if selected_method:
        orders = orders.filter(payment_method=selected_method)
    if start_date:
        orders = orders.filter(order_date__date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__date__lte=end_date)

    esewa_total = orders.filter(payment_method='eSewa').aggregate(Sum('total_price'))['total_price__sum'] or 0
    cod_total = orders.filter(payment_method='COD').aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_amount = esewa_total + cod_total

    return render(request, 'mytemplates/admin_payment_report.html', {
        'orders': orders,
        'esewa_total': esewa_total,
        'cod_total': cod_total,
        'total_amount': total_amount,
        'selected_method': selected_method,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required
def export_admin_payment_report(request):
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('home')

    orders = Order.objects.all()

    # Apply same filtering here too
    selected_method = request.GET.get('method')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if selected_method:
        orders = orders.filter(payment_method=selected_method)
    if start_date:
        orders = orders.filter(order_date__date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__date__lte=end_date)

    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="admin_payment_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Product', 'Customer', 'Amount (Rs)', 'Payment Method', 'Status', 'Order Date'])

    for order in orders:
        writer.writerow([
            order.id,
            order.product.product_name,
            order.user.username,
            order.total_price,
            order.payment_method,
            order.status,
            order.order_date.strftime('%Y-%m-%d'),
        ])

    return response
