import tkinter as tk
import random
from tkinter import messagebox

root = tk.Tk()

frame = tk.Frame(root)
frame.pack(side=tk.BOTTOM)

def start_random():
    entry.delete(0, tk.END)
    num = random.randint(0, 9)
    entry.insert(0, str(num))
    global after_id
    after_id = root.after(500, start_random)
    entry.config(bg="white")

def stop_random():
    root.after_cancel(after_id)
    check_number()

def check_number():
    if entry.get() == "7":
        entry.config(bg="red")
        messagebox.showinfo('ピッタリ！！！','おめでとう')
    else:
        messagebox.showinfo('７ちゃうやん！！！','もう一回やってみよう')
        

entry = tk.Entry(frame, font=("Helvetica", 24), width=10)
entry.pack(side=tk.LEFT)

button_start = tk.Button(frame, text="Start", font=("Helvetica", 24), width=10, height=2, command=start_random)
button_start.pack(side=tk.LEFT)

button_stop = tk.Button(frame, text="Stop", font=("Helvetica", 24), width=10, height=2, command=stop_random)
button_stop.pack(side=tk.LEFT)

root.title("目押しゲーム　7を当てろ！！")
root.mainloop()
