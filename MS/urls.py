from django.urls import path
from .views import *
from MS import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path("", views.home_view, name="home"),

    path("login", views.login_view,name="login"),
    path('logout/', views.logout_view, name='logout'),
    path("register", views.register, name="register"),
    path("forgotpassword", views.forgotpassword, name="forgotpassword"),

    # required for reset to work after email
    path('reset/<uidb64>/<token>/', views.custom_reset_password_confirm, name='password_reset_confirm'),

    path("product/",views.product,name="product"),
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),

    path("productpage",views.productpage,name="productpage"),
    path("contactus", views.contactus,name="contactus"),
    path("aboutus", views.aboutus,name="aboutus"),
    path("parenting", views.parenting,name="parenting"),

# Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-wishlist/<int:item_id>/', views.remove_wishlist_item, name='remove_wishlist_item'),

# Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

# Buy Now
    # path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('buy-now-checkout/', views.buy_now_checkout, name='buy_now_checkout'),
    path('orders/', views.user_orders, name='user_orders'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    # ✅ Admin URLs for managing products
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/orders/', views.admin_all_orders, name='admin_all_orders'),
    path('dashboard/orders/update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('dashboard/messages/', views.admin_messages_view, name='admin_messages'),




    path('dashboard/products/', views.admin_products, name='admin_products'),
    path('dashboard/products/create/', views.create_product, name='create_product'),
    path('dashboard/products/update/<int:pk>/', views.update_product, name='update_product'),
    path('dashboard/products/delete/<int:pk>/', views.delete_product, name='delete_product'),

    path('dashboard/users/', views.user_list_view, name='admin_users'),
    path('dashboard/users/create/', views.user_create_view, name='create_user'),
    path('dashboard/users/edit/<int:pk>/', views.user_edit_view, name='edit_user'),
    path('dashboard/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('dashboard/coupons/', views.admin_coupons, name='admin_coupons'),
    path('dashboard/coupons/add/', views.add_coupon, name='add_coupon'),
    path('dashboard/coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('dashboard/coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    path('dashboard/payment-report/', views.admin_payment_report, name='admin_payment_report'),
    path('dashboard/payment-report/export/', views.export_admin_payment_report, name='export_admin_payment_report'),


]








