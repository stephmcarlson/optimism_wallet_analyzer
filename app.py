from flask import Flask, render_template, jsonify, request
import pandas as pd
from pathlib import Path
import requests
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if request.method == 'POST':
        wallet = request.form['wallet']  # Get the 'wallet' value from the form
        
        # Read in and print CSV for Last 90 Days
        transactions_csv = Path("resources/NFT_transactions_optimism_jan_feb_march.csv")

        transactions = pd.read_csv(transactions_csv)

        # Convert Value to a numeric value
        transactions['Value'] = pd.to_numeric(transactions['Value'], errors='coerce')

        # Add a column with the avg. transaction value for each collection
        collection_avg = transactions.groupby('Collection Contract Address')['Value'].transform('mean')
        transactions['Collection_Avg'] = collection_avg

        # Create df of Collection and Contract
        coll_slug = transactions.groupby('Collection Contract Address')['Collection Slug'].first().reset_index()

        # Read in user input for wallet address and save as variable
        buyer_address = wallet

        # Filter df to wallet address
        filtered_transactions = transactions[transactions['Buyer Address'] == buyer_address]

        # Create transactions df with count of number of transactions by contract
        count_by_contract = filtered_transactions.groupby('Collection Contract Address')['Value'].count()
        count_df = pd.DataFrame(count_by_contract)
        count_df = count_df.rename(columns={'Value': 'Transactions'})

        # Create sum df with sum of value spent by contract
        sum_by_contract = filtered_transactions.groupby('Collection Contract Address')['Value'].sum()
        sum_df = pd.DataFrame(sum_by_contract)
        sum_df = sum_df.rename(columns={'Value': 'Total Spent'})

        # Create avg df with average value of each transaction by contract
        avg_by_contract = filtered_transactions.groupby('Collection Contract Address')['Value'].mean()
        avg_df = pd.DataFrame(avg_by_contract)
        avg_df = avg_df.rename(columns={'Value': 'Avg. Spent'})

        # # Create collection df with average value per transaction by contract
        avg_of_contract = filtered_transactions.groupby('Collection Contract Address')['Collection_Avg'].mean()
        coll_df = pd.DataFrame(avg_of_contract)
        coll_df = coll_df.rename(columns={'Value': 'Collection_Avg'})

        # Combine calculations above into single df
        final_df = count_df.merge(sum_df, how="inner", on="Collection Contract Address").merge(avg_df, how="inner", on="Collection Contract Address").merge(coll_df, how="inner", on="Collection Contract Address")

        # Calculate win/loss per collection and add collection slug
        final_df['Avg. PnL'] = final_df['Collection_Avg'] - final_df['Avg. Spent']
        merge_df = pd.merge(final_df, coll_slug, on='Collection Contract Address', how='left')

        # Clean up df
        sorted_df = merge_df.sort_values(by='Total Spent', ascending=False)
        new_df = sorted_df[['Collection Contract Address', 'Collection Slug', 'Transactions', 'Total Spent', 'Avg. Spent', 'Collection_Avg', 'Avg. PnL']]
        rename_df = new_df.rename(columns={'Collection Contract Address': 'Contract', 'Collection Slug': 'Collection', 'Transactions': 'Transactions', 'Total Spent': 'Total_Spent', 'Avg. Spent': 'Avg_Spent', 'Collection_Avg': 'Collection_Avg', 'Avg. PnL': 'Avg_PnL'})
        
        # Convert to html table
        table = rename_df.to_html()
     
        return table
    
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)