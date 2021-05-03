import io
import random
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from flask import Response
from flask_wtf import Form
from datetime import timedelta
from matplotlib.figure import Figure
from pandas_datareader import data as pdr
from wtforms.fields.html5 import DateField
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging

app = Flask(__name__)

# Index
@app.route('/')
def index():
    stocks = get_top_stocks()
    return render_template('dashboard.html', stocks=stocks)
    
# Index
@app.route('/search', methods=['GET', 'POST'])
def search_stocks():
    if request.method == 'POST':
        ticker_list = []
        
        # Get Data from Form
        ticker = request.form.get('query')
        ticker_list.append(ticker)

        all_data = fetch_tickers_data(ticker_list)
        
        # Prepare data for output
        stocks = all_data.loc[(ticker)].reset_index().T.to_dict().values()
        
        return render_template('search.html', ticker=ticker, stocks=stocks)
    else:
        return render_template('search.html', ticker="")
    
@app.route('/plot.png')
def plot_png():
    ticker_list = []
    ticker = request.args.get('my_var', None)
    ticker_list.append(ticker)
    fig = create_figure(ticker_list)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_figure(ticker_list):
    all_data = fetch_tickers_data(ticker_list)
    
    # reset the index to make everything columns
    just_closing_prices = all_data[['Adj Close']].reset_index()

    daily_close_px = just_closing_prices.pivot('Date', 'Ticker','Adj Close')
    
    fig = plt.figure();
    _ = daily_close_px[ticker_list[0]].plot(figsize=(12,8));
    return fig

def fetch_tickers_data(ticker_list):
    # Generate Dates to fetch stock data
    start_date= date.today() - timedelta(days = 5)
    end_date=date.today()

    # Fetch data from Twitter API
    return get(ticker_list, start_date, end_date)

def get_top_stocks():
    # Tickers list
    # We can add and delete any ticker from the list to get desired ticker live data
    ticker_list=['DJIA', 'DOW', 'LB', 'EXPE', 'PXD', 'MCHP', 'CRM', 'NRG', 'HFC', 'NOW']
    today = date.today()

    # We can get data by our choice by giving days bracket
    start_date= "2021-04-25"
    end_date="2021-05-01"

    # Fetch data from Twitter API
    all_data = get(ticker_list, start_date, today)

    # reset the index to make everything columns
    just_closing_prices = all_data[['Adj Close']].reset_index()

    daily_close_px = just_closing_prices.pivot('Date', 'Ticker','Adj Close')

    # Pick the first and last row to calculate price difference
    res = pd.concat([daily_close_px.head(1), daily_close_px.tail(1)])
    res = res.diff().T
    rslt = pd.DataFrame(np.zeros((0,3)), columns=['top1','top2','top3'])
    for i in res.columns:
        df1row = pd.DataFrame(res.nlargest(3, i).index.tolist(), index=['top1','top2','top3']).T
        rslt = pd.concat([rslt, df1row], axis=0)

    list_of_stocks = prepare_output_data(rslt, all_data, today)
    return list_of_stocks

def prepare_output_data(rslt, all_data, today):
    list_of_stocks = []
    for row in rslt.itertuples():
        stock_data = {}
        stock_data['StockName'] = row.top1
        stock_data.update(all_data.loc[(row.top1, (today-timedelta(days = 3)).strftime('%Y-%m-%d'))].to_dict())
        list_of_stocks.append(stock_data)
        stock_data = {}
        stock_data['StockName'] = row.top2
        stock_data.update(all_data.loc[(row.top2, (today-timedelta(days = 3)).strftime('%Y-%m-%d'))].to_dict())
        list_of_stocks.append(stock_data)
        stock_data = {}
        stock_data['StockName'] = row.top3
        stock_data.update(all_data.loc[(row.top3, (today-timedelta(days = 3)).strftime('%Y-%m-%d'))].to_dict())
        list_of_stocks.append(stock_data)
    return list_of_stocks

def get(tickers, start, end):
	def data(ticker):
		return pdr.get_data_yahoo(ticker, start=start, end=end)
	datas = map(data, tickers)
	return pd.concat(datas, keys=tickers, names=['Ticker','Date'])

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
