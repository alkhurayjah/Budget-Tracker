import pandas as pd
import os

# Create file if it doesn't exist
if not os.path.isfile('expenses.csv'):
    df = pd.DataFrame(columns=['Date', 'Category', 'Amount', 'User'])
    df.to_csv('expenses.csv', index=False)
