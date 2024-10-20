import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

# Sample data 
data = {
    'days': list(range(1, 101)),
    'prices': [i + (i * 0.1) for i in range(1, 101)]  # Sample prices
}
df = pd.DataFrame(data)

X = df[['days']]
y = df['prices']
model = LinearRegression()
model.fit(X, y)

# Save the model
with open('stock_price_model.pkl', 'wb') as f:
    pickle.dump(model, f)