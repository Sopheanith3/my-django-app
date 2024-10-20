import requests
import pandas as pd 
import pickle
import matplotlib.pyplot as plt
import os
from django.shortcuts import render
from .models import StockData
from django.conf import settings
from django.http import JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse

# Create your views here.

ALPHA_VANTAGE_API_KEY = 'your_alpha_vantage_api_key' 

def update_stock_data(request, symbol):
    print(f"Fetching data for: {symbol}")
    fetch_stock_data(symbol)
    return JsonResponse({"status": "success", "symbol": symbol})

with open('stock_price_model.pkl', 'rb') as f:
    stock_price_model = pickle.load(f)

def report_view(request):
    # Sample backtest results and actual prices for testing
    backtest_results = {"profit_or_loss": "33.35"}
    predicted_prices = [100 + (i * 0.1) for i in range(30)]  # Sample predicted prices
    actual_prices = [100 + (i * 0.08) for i in range(30)]  # Sample actual prices

    pdf_buffer = generate_report(backtest_results, predicted_prices, actual_prices)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stock_price_report.pdf"'
    return response

def generate_report(backtest_results, predicted_prices, actual_prices):
    # Create a figure for the price comparison
    plt.figure(figsize=(10, 5))
    plt.plot(actual_prices, label='Actual Prices', color='blue')
    plt.plot(predicted_prices, label='Predicted Prices', color='red')
    plt.title('Actual vs Predicted Stock Prices')
    plt.xlabel('Days')
    plt.ylabel('Price')
    plt.legend()
    
    img_path = 'price_comparison.png'
    plt.savefig(img_path)
    plt.close()

    # Create a PDF report
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Stock Price Report")
    c.drawString(100, 730, f"Backtest Results: {backtest_results}")
    
    # Add the image
    c.drawImage(img_path, 100, 400, width=400, height=300)
    
    c.save()
    buffer.seek(0)

    # Remove the image file after saving
    os.remove(img_path)
    
    return buffer

def predict_stock_prices(symbol):
    stock_data = StockData.objects.filter(symbol=symbol).order_by('date')
    df = pd.DataFrame(list(stock_data.values('date', 'close_price')))
    
    # Assuming we're predicting the next 30 days
    last_day = len(df)
    future_days = pd.DataFrame({'days': range(last_day + 1, last_day + 31)})

    # Use the model to predict future prices
    predicted_prices = stock_price_model.predict(future_days)

    return predicted_prices

def predict_prices_view(request, symbol):
    predictions = predict_stock_prices(symbol)
    return JsonResponse({'predicted_prices': predictions.tolist()})

def calculate_moving_averages(symbol):
    stock_data = StockData.objects.filter(symbol=symbol).order_by('date')
    df = pd.DataFrame(list(stock_data.values('date', 'close_price')))
    df['short_mavg'] = df['close_price'].rolling(window=50, min_periods=1).mean()  # 50-day moving average
    df['long_mavg'] = df['close_price'].rolling(window=200, min_periods=1).mean()  # 200-day moving average
    return df

def run_backtest(request, symbol, initial_investment):
    profit_or_loss = backtest_strategy(symbol, initial_investment)
    return JsonResponse({'profit_or_loss': profit_or_loss})

def backtest_strategy(symbol, initial_investment):
    df = calculate_moving_averages(symbol)

    position = 0  
    buy_price = 0
    cash = initial_investment

    for i in range(1, len(df)):
        # Buy condition
        if position == 0 and df['close_price'][i] < df['short_mavg'][i]:
            position = 1
            buy_price = df['close_price'][i]

        # Sell condition
        elif position == 1 and df['close_price'][i] > df['long_mavg'][i]:
            position = 0
            cash += df['close_price'][i] - buy_price  

    if position == 1:
        cash += df['close_price'].iloc[-1] - buy_price

    return cash - initial_investment  


def fetch_stock_data(symbol):
    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    if 'Time Series (Daily)' in data:
        time_series = data['Time Series (Daily)']
        for date, daily_data in time_series.items():
            StockData.objects.update_or_create(
                symbol=symbol,
                date=date,
                defaults={
                    'open_price': daily_data['1. open'],
                    'high_price': daily_data['2. high'],
                    'low_price': daily_data['3. low'],
                    'close_price': daily_data['4. close'],
                    'volume': daily_data['5. volume'],
                }
            )