import tkinter as tk
from tkinter import ttk, scrolledtext
from ftplib import FTP
import time
import os
import threading

def get_download_files():
    try:
        ftp = FTP("ftp.speed.hinet.net", timeout=10)
        ftp.login(user='ftp', passwd='ftp')
        files = ftp.nlst()
        ftp.quit()
        return [f for f in files if f.endswith(".zip")]
    except Exception as e:
        return [f"⚠️ 取得失敗：{e}"]

def test_download_speed():
    try:
        ftp = FTP("ftp.speed.hinet.net", timeout=30)
        ftp.login(user='ftp', passwd='ftp')

        remote_filename = file_var.get()
        local_filename = os.path.join(os.getcwd(), remote_filename)

        ftp.sendcmd("TYPE I")
        total_size = ftp.size(remote_filename)

        result_text.insert(tk.END, f"📥 開始下載 {remote_filename}（{total_size / 1024 / 1024:.1f} MB）...\n")
        result_text.update()

        downloaded = 0
        chunk_size = 8192

        def callback(data):
            nonlocal downloaded
            downloaded += len(data)
            progress = int((downloaded / total_size) * 100)
            progress_var.set(progress)
            progress_bar.update()
            f.write(data)

        with open(local_filename, "wb") as f:
            start = time.time()
            ftp.retrbinary(f"RETR {remote_filename}", callback, blocksize=chunk_size)
            end = time.time()

        file_size = os.path.getsize(local_filename)
        duration = end - start
        speed_mbps = (file_size * 8) / (duration * 1024 * 1024)

        result_text.insert(tk.END, f"✅ 下載完成：{file_size / 1024:.1f} KB，耗時 {duration:.2f} 秒\n")
        result_text.insert(tk.END, f"🚀 平均下載速度：{speed_mbps:.2f} Mbps\n")
        result_text.insert(tk.END, f"📁 檔案儲存於：{local_filename}\n\n")

        ftp.quit()
        progress_var.set(0)
        progress_bar.update()

    except Exception as e:
        result_text.insert(tk.END, f"❌ 下載錯誤：{str(e)}\n\n")
        progress_var.set(0)
        progress_bar.update()

def test_upload_speed():
    try:
        ftp = FTP("ftp.speed.hinet.net", timeout=30)
        ftp.login(user='ftp', passwd='ftp')
        ftp.cwd('/uploads')

        # 使用選擇的檔案上傳
        local_filename = os.path.join(os.getcwd(), file_var.get())
        if not os.path.exists(local_filename):
            result_text.insert(tk.END, f"❌ 找不到檔案：{local_filename}\n請先下載再上傳\n\n")
            return

        file_size = os.path.getsize(local_filename)
        chunk_size = 8192
        uploaded = 0

        result_text.insert(tk.END, f"📤 開始上傳 {file_var.get()}（{file_size / 1024 / 1024:.1f} MB）...\n")
        result_text.update()

        def upload_callback(block):
            nonlocal uploaded
            uploaded += len(block)
            progress = int((uploaded / file_size) * 100)
            progress_var.set(progress)
            progress_bar.update()

        with open(local_filename, "rb") as f:
            start = time.time()
            ftp.storbinary(f"STOR {os.path.basename(local_filename)}", f, blocksize=chunk_size, callback=upload_callback)
            end = time.time()

        duration = end - start
        speed_mbps = (file_size * 8) / (duration * 1024 * 1024)

        result_text.insert(tk.END, f"✅ 上傳完成，耗時 {duration:.2f} 秒\n")
        result_text.insert(tk.END, f"🚀 平均上傳速度：{speed_mbps:.2f} Mbps\n\n")

        ftp.quit()
        progress_var.set(0)
        progress_bar.update()

    except Exception as e:
        result_text.insert(tk.END, f"❌ 上傳錯誤：{str(e)}\n\n")
        progress_var.set(0)
        progress_bar.update()

def set_ui_state(state):
    server_combobox.config(state=state)
    file_combobox.config(state=state)
    start_button.config(state=state)
    for rb in radio_buttons:
        rb.config(state=state)

def update_label():
    mode = action_var.get()
    if mode == "Download":
        file_label.config(text="選擇測試檔案（Download）:")
    elif mode == "Upload":
        file_label.config(text="選擇上傳檔案（需先下載）:")
    else:
        file_label.config(text="選擇測試檔案（Download & Upload）:")

def threaded_test():
    set_ui_state('disabled')
    selected_action = action_var.get()
    result_text.insert(tk.END, f"🔄 開始測試：{selected_action}\n")
    result_text.update()

    try:
        if selected_action in ["Download", "Download & Upload"]:
            test_download_speed()
        if selected_action in ["Upload", "Download & Upload"]:
            test_upload_speed()
    finally:
        set_ui_state('normal')

def start_test():
    threading.Thread(target=threaded_test, daemon=True).start()

# === UI 建立 ===
root = tk.Tk()
root.title("Hinet FTP 測速工具")
root.iconbitmap("ftp_speed_icon.ico")
root.geometry("580x560")

# FTP Server 選擇
ttk.Label(root, text="選擇 FTP Server:").pack(pady=(10, 0))
server_var = tk.StringVar()
server_combobox = ttk.Combobox(root, textvariable=server_var, state="readonly")
server_combobox['values'] = ['Hinet (ftp://ftp.speed.hinet.net)']
server_combobox.current(0)
server_combobox.pack(pady=5)

# 測試選項
ttk.Label(root, text="選擇測試項目:").pack(pady=(10, 0))
action_var = tk.StringVar(value="Download")
actions = ["Download", "Upload", "Download & Upload"]
radio_buttons = []
for action in actions:
    rb = ttk.Radiobutton(root, text=action, variable=action_var, value=action, command=update_label)
    rb.pack(anchor='w', padx=20)
    radio_buttons.append(rb)

# 測試檔案選擇
file_label = ttk.Label(root, text="選擇測試檔案（Download）:")
file_label.pack(pady=(10, 0))
file_var = tk.StringVar()
file_combobox = ttk.Combobox(root, textvariable=file_var, state="readonly")
available_files = get_download_files()
file_combobox['values'] = available_files
if available_files:
    file_combobox.current(0)
file_combobox.pack(pady=5)

# 開始測試按鈕
start_button = ttk.Button(root, text="開始測試", command=start_test)
start_button.pack(pady=10)

# 進度條
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, orient="horizontal", length=450, mode="determinate", variable=progress_var)
progress_bar.pack(pady=(0, 10))

# 測試結果區
ttk.Label(root, text="測試結果:").pack()
result_text = scrolledtext.ScrolledText(root, width=70, height=12, wrap=tk.WORD)
result_text.pack(padx=10, pady=(0, 10))

# 啟動主程式
root.mainloop()
