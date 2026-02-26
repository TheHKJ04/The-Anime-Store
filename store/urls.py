from django.urls import path
from . import views

urlpatterns = [
    path('api/product/', views.product_list_api, name='product_list_api'),
    path('cart_count', views.cart_count, name='cart_count'),
    path('products/', views.product, name='product'),
    path('api/categories/', views.category_list_api, name='category_list_api'),
    path('', views.home, name='home'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/', views.product_detail1, name='product_detail'),
    path('accounts/', views.account_view, name='account'),
    path('api/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('cart/', views.cart_view, name='cart'),
    path("subscribe/", views.subscribe_newsletter, name="subscribe_newsletter"),
    path("refund_policy/", views.refund_policy, name="refund_policy"),
    path("privacy_policy/", views.privacy_policy, name="privacy_policy"),
    path("terms_service/", views.terms_service, name="terms_service"),
    path("shipping_policy/", views.shipping_policy, name="shipping_policy"),
    path("contact/", views.contact, name="contact"),
    path('cart/', views.cart_view, name='cart'), 
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'), 
    path('decrease-item/<int:product_id>/', views.decrease_item, name='decrease_item'), 
    path('remove-item/<int:product_id>/', views.remove_item, name='remove_item'),
    path('set-currency/', views.set_currency, name='set_currency'),
    path('orders/<str:order_number>/', views.track_order, name='track_order'),
    path('payment/', views.payment, name='payment'),


]