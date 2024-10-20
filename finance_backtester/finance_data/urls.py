from django.urls import path
from .views import update_stock_data
from django.urls import include
from .views import run_backtest
from .views import predict_prices_view
from .views import report_view

urlpatterns = [
    path('finance/', include('finance_data.urls')),
]
urlpatterns = [
    path('update-stock/<str:symbol>/', update_stock_data, name='update_stock_data'),
]
urlpatterns += [
    path('backtest/<str:symbol>/<int:initial_investment>/', run_backtest, name='run_backtest'),
]
urlpatterns += [
    path('predict/<str:symbol>/', predict_prices_view, name='predict_prices'),
]
urlpatterns += [
    path('report/', report_view, name='generate_report'),
]