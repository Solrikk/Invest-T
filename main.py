import time
import os
import json
import numpy as np
import pandas as pd
from tinkoff.invest import Client, CandleInterval
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import font

TOKEN = "t._key"
filename = "portfolio_start_value.json"


def save_start_of_day_value(value):
  with open(filename, 'w') as f:
    json.dump(
        {
            "start_of_day_value": value,
            "date": datetime.now().strftime('%Y-%m-%d')
        }, f)


def load_start_of_day_value():
  if os.path.exists(filename):
    with open(filename, 'r') as f:
      data = json.load(f)
      if data["date"] == datetime.now().strftime('%Y-%m-%d'):
        return data["start_of_day_value"]
  return None


def fetch_historic_data(figi, from_date, to_date, interval):
  with Client(TOKEN) as client:
    response = client.market_data.get_candles(figi=figi,
                                              from_=from_date,
                                              to=to_date,
                                              interval=interval)
    return pd.DataFrame([{
        'time': candle.time,
        'open': candle.open.units + candle.open.nano / 1e9,
        'high': candle.high.units + candle.high.nano / 1e9,
        'low': candle.low.units + candle.low.nano / 1e9,
        'close': candle.close.units + candle.close.nano / 1e9,
        'volume': candle.volume
    } for candle in response.candles])


def simple_moving_average(data, window):
  return data['close'].rolling(window=window).mean()


def analyze_and_trade():
  text_widget.config(state=tk.NORMAL)
  text_widget.insert(tk.END, f"AI анализирует и выполняет торговлю...\n")

  df = fetch_historic_data("BBG004RVFFC0",
                           datetime.now() - timedelta(days=30), datetime.now(),
                           CandleInterval.CANDLE_INTERVAL_HOUR)

  if not df.empty:
    df['SMA_20'] = simple_moving_average(df, 20)
    df['SMA_50'] = simple_moving_average(df, 50)

    if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1]:
      text_widget.insert(tk.END,
                         f"Сигнал на покупку: Цена {df['close'].iloc[-1]}\n")
      # Execute buy order logic here
    else:
      text_widget.insert(tk.END,
                         f"Сигнал на продажу: Цена {df['close'].iloc[-1]}\n")
      # Execute sell order logic here
  else:
    text_widget.insert(tk.END, "Недостаточно данных для анализа.\n")

  text_widget.config(state=tk.DISABLED)


def update_portfolio_summary():
  with Client(TOKEN) as client:
    accounts = client.users.get_accounts().accounts
    start_of_day_value = load_start_of_day_value()
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)

    for account in accounts:
      portfolio = client.operations.get_portfolio(account_id=account.id)
      total_sum = 0
      positions_details = []

      for position in portfolio.positions:
        quantity = position.quantity.units + position.quantity.nano / 1e9
        price = position.current_price.units + position.current_price.nano / 1e9
        value = quantity * price
        total_sum += value
        positions_details.append((position, quantity, price, value))

      if start_of_day_value is None:
        save_start_of_day_value(total_sum)
        start_of_day_value = total_sum

      change = total_sum - start_of_day_value
      change_percent = (change / start_of_day_value *
                        100) if start_of_day_value != 0 else 0
      change_display = f"+{change:.2f} ₽ ({change_percent:.2f}%)" if change >= 0 else f"{change:.2f} ₽ ({change_percent:.2f}%)"
      day_change = total_sum - start_of_day_value

      text_widget.insert(
          tk.END,
          f"ID счета: {account.id}\nНазвание: {account.name}\nОбщая сумма: {total_sum:.2f} ₽\n"
      )
      if change >= 0:
        text_widget.insert(tk.END, f"Изменение: {change_display}\n", "green")
        text_widget.insert(tk.END, f"Заработано за день: {day_change:.2f} ₽\n",
                           "green")
      else:
        text_widget.insert(tk.END, f"Изменение: {change_display}\n", "red")
        text_widget.insert(tk.END, f"Заработано за день: {day_change:.2f} ₽\n",
                           "red")

      for position, quantity, price, value in positions_details:
        share = (value / total_sum) * 100 if total_sum != 0 else 0
        text_widget.insert(
            tk.END,
            f"\nИнструмент: {position.figi} ({position.instrument_type})\nКоличество: {quantity}\nТекущая цена: {price:.2f} ₽\nЗначение: {value:.2f} ₽\nДоля в портфеле: {share:.2f}%\n"
        )

      text_widget.insert(tk.END, "\n\n")

    text_widget.config(state=tk.DISABLED)
    window.after(10000, update_portfolio_summary)


window = tk.Tk()
window.title("Информация о портфеле")
window.geometry("600x500")
window.configure(bg='#1c1c1c')

title_font = font.Font(family="Arial", size=18, weight="bold")
text_font = font.Font(family="Arial", size=12)

title_frame = tk.Frame(window, bg='#2e2e2e', bd=2, relief=tk.GROOVE)
title_frame.pack(fill=tk.X, pady=10)

title_label = tk.Label(title_frame,
                       text="Обзор портфеля",
                       font=title_font,
                       fg="#ecf0f1",
                       bg='#2e2e2e')
title_label.pack(pady=10)

text_frame = tk.Frame(window, bg='#2e2e2e', bd=2, relief=tk.GROOVE)
text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

text_widget = tk.Text(text_frame,
                      font=text_font,
                      bg="#3c3c3c",
                      fg="#ecf0f1",
                      bd=0,
                      padx=10,
                      pady=10,
                      wrap=tk.WORD)
text_widget.tag_config("green", foreground="green")
text_widget.tag_config("red", foreground="red")
text_widget.pack(fill=tk.BOTH, expand=True)

button = tk.Button(window,
                   text="Анализировать и торговать",
                   command=analyze_and_trade,
                   bg='#2e2e2e',
                   fg='#ecf0f1',
                   font=text_font)
button.pack(pady=10)

update_portfolio_summary()

window.mainloop()
