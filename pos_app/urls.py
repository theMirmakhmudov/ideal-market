from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('cashier-dashboard/', views.cashier_dashboard, name='cashier_dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('categories/add/', views.add_category, name='add_category'),
    path('process-sale/', views.process_sale, name='process_sale'),
    path('statistics/', views.statistics, name='statistics'),

    # API endpoints
    path('api/products/', views.get_products_api, name='get_products_api'),
    path('api/search-barcode/', views.search_product_by_barcode, name='search_product_by_barcode'),
    path('api/search-sale/', views.search_sale_by_number, name='search_sale_by_number'),
    path('api/process-return/', views.process_return, name='process_return'),

    # Standalone POS
    path('pos/', views.standalone_pos, name='standalone_pos'),
]