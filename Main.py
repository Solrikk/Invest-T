import time
import os
import json
from tinkoff.invest import Client
from datetime import datetime
import tkinter as tk
from tkinter import font

TOKEN = "t._токен"
filename = "portfolio_start_value.json"

def save_start_of_day_value(value):
    with open(filename, 'w') as f:
        json.dump({"start_of_day_value": value, "date": datetime.now().strftime('%Y-%m-%d')}, f)

def load_start_of_day_value():
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            if data["date"] == datetime.now().strftime('%Y-%m-%d'):
                return data["start_of_day_value"]
    return None

def update_portfolio_summary():
    with Client(TOKEN) as client:
        accounts = client.users.get_accounts().accounts
        start_of_day_value = load_start_of_day_value()
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)

        for account in accounts:
            portfolio = client.operations.get_portfolio(account_id=account.id)
            total_sum = 0

            for position in portfolio.positions:
                quantity = position.quantity.units + position.quantity.nano / 1e9
                price = position.current_price.units + position.current_price.nano / 1e9
                total_sum += quantity * price

            if start_of_day_value is None:
                save_start_of_day_value(total_sum)
                start_of_day_value = total_sum

            change = total_sum - start_of_day_value
            change_percent = (change / start_of_day_value * 100) if start_of_day_value != 0 else 0
            change_display = f"+{change:.2f} ₽ ({change_percent:.2f}%)" if change >= 0 else f"{change:.2f} ₽ ({change_percent:.2f}%)"
            day_change = total_sum - start_of_day_value

            text_widget.insert(tk.END, f"ID счета: {account.id}\nНазвание: {account.name}\nОбщая сумма: {total_sum:.2f} ₽\n")
            if change >= 0:
                text_widget.insert(tk.END, f"Изменение: {change_display}\n", "green")
                text_widget.insert(tk.END, f"Заработано за день: {day_change:.2f} ₽\n\n", "green")
            else:
                text_widget.insert(tk.END, f"Изменение: {change_display}\n", "red")
                text_widget.insert(tk.END, f"Заработано за день: {day_change:.2f} ₽\n\n", "red")

        text_widget.config(state=tk.DISABLED)
        window.after(10000, update_portfolio_summary)

window = tk.Tk()
window.title("Информация о портфеле")
window.geometry("600x450")
window.configure(bg='#1c1c1c')

title_font = font.Font(family="Arial", size=18, weight="bold")
text_font = font.Font(family="Arial", size=12)

title_frame = tk.Frame(window, bg='#2e2e2e', bd=2, relief=tk.GROOVE)
title_frame.pack(fill=tk.X, pady=10)

title_label = tk.Label(title_frame, text="Обзор портфеля", font=title_font, fg="#ecf0f1", bg='#2e2e2e')
title_label.pack(pady=10)

text_frame = tk.Frame(window, bg='#2e2e2e', bd=2, relief=tk.GROOVE)
text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

text_widget = tk.Text(text_frame, font=text_font, bg="#3c3c3c", fg="#ecf0f1", bd=0, padx=10, pady=10, wrap=tk.WORD)
text_widget.tag_config("green", foreground="green")
text_widget.tag_config("red", foreground="red")
text_widget.pack(fill=tk.BOTH, expand=True)

update_portfolio_summary()

window.mainloop()
