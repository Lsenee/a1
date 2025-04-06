import tkinter as tk
from tkinter import messagebox
import socket
from ttkbootstrap import Style  # 导入 ttkbootstrap
from PIL import Image, ImageTk  # 导入 Pillow 库

# 服务器配置
SERVER_HOST = '192.168.140.114'  # 服务器 IP
SERVER_PORT = 2525              # 服务器端口

# 客户端 GUI 类
class ATMClient:
    def __init__(self, root):
        self.root = root
        self.root.title("ATM 客户端")
        self.root.geometry("500x400")  # 调整窗口大小

        # 使用 ttkbootstrap 主题
        self.style = Style(theme="cosmo")  # 可选主题：cosmo, flatly, journal, etc.

        # 主框架
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        self.label_title = tk.Label(self.main_frame, text="ATM 客户端", font=("Arial", 18, "bold"))
        self.label_title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 账户 ID 输入
        self.label_account = tk.Label(self.main_frame, text="账户 ID:", font=("Arial", 12))
        self.label_account.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.entry_account = tk.Entry(self.main_frame, font=("Arial", 12))
        self.entry_account.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)

        # 密码输入
        self.label_password = tk.Label(self.main_frame, text="密码:", font=("Arial", 12))
        self.label_password.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.entry_password = tk.Entry(self.main_frame, font=("Arial", 12), show="*")  # 隐藏密码
        self.entry_password.grid(row=2, column=1, padx=10, pady=10, sticky=tk.EW)

        # 加载图标
        self.load_icons()

        # 操作按钮
        self.button_login_width = 15  # 登录按钮宽度
        self.button_balance_width = 18  # 查询余额按钮宽度（增大）
        self.button_withdraw_width = 12  # 取款按钮宽度（减少）

        # 登录按钮
        self.button_login = tk.Button(self.main_frame, text="登录", command=self.login, font=("Arial", 12), bg="#4CAF50", fg="white", width=self.button_login_width, image=self.login_icon, compound=tk.LEFT)
        self.button_login.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky=tk.EW)

        # 查询余额按钮
        self.button_balance = tk.Button(self.main_frame, text="查询余额", command=self.check_balance, font=("Arial", 12), bg="#2196F3", fg="white", width=self.button_balance_width, state=tk.DISABLED, image=self.balance_icon, compound=tk.LEFT)
        self.button_balance.grid(row=4, column=0, padx=10, pady=10, sticky=tk.EW)

        # 取款按钮
        self.button_withdraw = tk.Button(self.main_frame, text="取款", command=self.show_withdraw, font=("Arial", 12), bg="#FF9800", fg="white", width=self.button_withdraw_width, state=tk.DISABLED, image=self.withdraw_icon, compound=tk.LEFT)
        self.button_withdraw.grid(row=4, column=1, padx=10, pady=10, sticky=tk.EW)

        # 金额输入框（动态显示）
        self.label_amount = tk.Label(self.main_frame, text="金额:", font=("Arial", 12))
        self.entry_amount = tk.Entry(self.main_frame, font=("Arial", 12))
        self.amount_frame = tk.Frame(self.main_frame)  # 用于动态显示金额输入框

        # Socket 连接
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(20)  # 设置超时时间为 20 秒
        try:
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
        except socket.timeout:
            messagebox.showerror("错误", "连接服务器超时")
        except Exception as e:
            messagebox.showerror("错误", f"连接服务器失败: {e}")

        # 登录状态
        self.logged_in = False

    # 加载图标
    def load_icons(self):
        try:
            # 加载登录图标
            login_image = Image.open("H:/LOGIN.jpg").resize((20, 20), Image.Resampling.LANCZOS)
            self.login_icon = ImageTk.PhotoImage(login_image)
            print("登录图标加载成功")
        except Exception as e:
            print(f"登录图标加载失败: {e}")
            self.login_icon = None

        try:
            # 加载查询余额图标
            balance_image = Image.open("H:/balance.png").resize((20, 20), Image.Resampling.LANCZOS)
            self.balance_icon = ImageTk.PhotoImage(balance_image)
            print("查询余额图标加载成功")
        except Exception as e:
            print(f"查询余额图标加载失败: {e}")
            self.balance_icon = None

        try:
            # 加载取款图标
            withdraw_image = Image.open("H:/withdraw.jpg").resize((20, 20), Image.Resampling.LANCZOS)
            self.withdraw_icon = ImageTk.PhotoImage(withdraw_image)
            print("取款图标加载成功")
        except Exception as e:
            print(f"取款图标加载失败: {e}")
            self.withdraw_icon = None

    # 登录
    def login(self):
        account_id = self.entry_account.get()
        password = self.entry_password.get()
        if not account_id or not password:
            messagebox.showerror("错误", "请输入账户 ID 和密码")
            return

        # 发送 HELO 请求
        helo_request = f"HELO {account_id}"
        helo_response = self.send_request(helo_request)

        if helo_response == "500 sp AUTH REQUIRED!":
            # 发送 PASS 请求
            pass_request = f"PASS {password}"
            pass_response = self.send_request(pass_request)

            if pass_response == "525 OK!":
                self.logged_in = True
                messagebox.showinfo("成功", "登录成功")
                # 启用功能按钮
                self.button_balance.config(state=tk.NORMAL)
                self.button_withdraw.config(state=tk.NORMAL)
            else:
                messagebox.showerror("错误", "登录失败，请检查密码")
        else:
            messagebox.showerror("错误", "登录失败，请检查账户 ID")

    # 查询余额
    def check_balance(self):
        if not self.logged_in:
            messagebox.showerror("错误", "请先登录")
            return
        response = self.send_request("BALA")
        if response.startswith("AMNT:"):
            messagebox.showinfo("余额", f"当前余额: {response[5:]}")
        else:
            messagebox.showerror("错误", "查询余额失败")

    # 显示取款金额输入框
    def show_withdraw(self):
        if not self.logged_in:
            messagebox.showerror("错误", "请先登录")
            return
        self.clear_amount_frame()
        self.label_amount.grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        self.entry_amount.grid(row=5, column=1, padx=10, pady=10, sticky=tk.EW)
        self.button_confirm = tk.Button(self.main_frame, text="确认取款", command=self.withdraw, font=("Arial", 12), bg="#F44336", fg="white", width=self.button_withdraw_width, image=self.withdraw_icon, compound=tk.LEFT)
        self.button_confirm.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky=tk.EW)

    # 取款
    def withdraw(self):
        amount = self.entry_amount.get()
        if not amount:
            messagebox.showerror("错误", "请输入金额")
            return
        try:
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("错误", "金额必须大于 0")
                return
        except ValueError:
            messagebox.showerror("错误", "金额必须为数字")
            return

        # 发送取款请求
        withdraw_request = f"WDRA {amount:.2f}"
        response = self.send_request(withdraw_request)

        if response == "525 OK!":
            messagebox.showinfo("成功", "取款成功")
        else:
            messagebox.showerror("错误", "取款失败")
        self.clear_amount_frame()

    # 清空金额输入框
    def clear_amount_frame(self):
        self.label_amount.grid_forget()
        self.entry_amount.grid_forget()
        if hasattr(self, 'button_confirm'):
            self.button_confirm.grid_forget()

    # 发送请求到服务器
    def send_request(self, request):
        try:
            print(f"发送请求: {request}")  # 打印请求
            self.client_socket.send(request.encode())
            response = self.client_socket.recv(1024).decode()
            print(f"收到响应: {response}")  # 打印响应
            return response
        except socket.timeout:
            messagebox.showerror("错误", "服务器响应超时")
        except Exception as e:
            messagebox.showerror("错误", f"与服务器通信失败: {e}")

    # 关闭连接
    def __del__(self):
        if hasattr(self, 'client_socket'):
            self.client_socket.close()

# 启动客户端
if __name__ == "__main__":
    root = tk.Tk()
    client = ATMClient(root)
    root.mainloop()