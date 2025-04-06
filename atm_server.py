import mysql.connector
from mysql.connector import pooling
import logging
import socket
import threading

# 配置数据库连接池
# 创建一个名为server_pool的数据库连接池
# pool_size指定连接池的大小为5，即最多可同时存在5个数据库连接
# host指定数据库服务器的主机为本地主机
# user指定数据库连接的用户名，这里为root
# password指定数据库连接的密码，为5578234Ed?
# database指定要连接的数据库为server_db
# 先不指定数据库，连接到 MySQL 服务器
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="5578234Ed?"
)
cursor = conn.cursor()

# 创建数据库
try:
    cursor.execute("CREATE DATABASE IF NOT EXISTS server_db")
    print("数据库 server_db 创建成功")
except mysql.connector.Error as err:
    print(f"创建数据库时出错: {err}")
finally:
    cursor.close()
    conn.close()

# 现在创建连接池，指定数据库为 server_db
db_pool = pooling.MySQLConnectionPool(
    pool_name="server_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="5578234Ed?",
    database="server_db"
)

# 获取数据库连接的函数，从数据库连接池中获取一个连接并返回
def get_db_connection():
    return db_pool.get_connection()

# 初始化数据库的函数
def init_database():
    try:
        # 获取数据库连接
        conn = get_db_connection()
        # 创建游标，用于执行SQL语句和处理结果集
        cursor = conn.cursor()

        # 创建账户表accounts
        # user_id字段作为主键，用于唯一标识用户
        # password字段存储用户密码，不能为空
        # balance字段存储用户余额，默认值为0.00，数据类型为DECIMAL(10, 2)，表示最多10位数字，其中2位小数
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            user_id VARCHAR(255) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            balance DECIMAL(10,2) DEFAULT 0.00
        )
        """)

        # 创建操作日志表operation_logs
        # log_id字段是自增的整数，作为表的主键
        # user_id字段用于存储操作的用户ID
        # operation_type字段记录操作的类型，现在包含金额信息
        # operation_result字段记录操作的结果
        # error_message字段用于存储操作失败时的错误信息
        # operation_time字段记录操作的时间，默认值为当前时间
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operation_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255),
            operation_type VARCHAR(255),  -- 现在包含金额信息
            operation_result VARCHAR(255),
            error_message TEXT,
            operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 提交事务，将创建表的操作保存到数据库
        conn.commit()
        # 关闭游标
        cursor.close()
        # 关闭数据库连接，归还到连接池
        conn.close()
    except mysql.connector.Error as err:
        # 如果在数据库初始化过程中发生错误，记录错误信息到日志文件
        logging.error(f"数据库初始化错误: {err}")


# 插入测试数据的函数
def insert_test_data():
    try:
        # 获取数据库连接
        conn = get_db_connection()
        # 创建游标
        cursor = conn.cursor()

        # 清空accounts表中的旧数据
        cursor.execute("DELETE FROM accounts")

        # 定义测试数据，包含用户ID、密码和余额
        test_data = [
            ('user1', 'pass1', 1000.00),
            ('user2', 'pass2', 2000.00)
        ]
        # 执行批量插入操作，将测试数据插入到accounts表中
        cursor.executemany(
            "INSERT INTO accounts (user_id, password, balance) VALUES (%s, %s, %s)",
            test_data
        )

        # 提交事务，保存插入操作
        conn.commit()
        # 关闭游标
        cursor.close()
        # 关闭数据库连接
        conn.close()
    except mysql.connector.Error as err:
        # 如果插入测试数据时发生错误，记录错误信息到日志文件
        logging.error(f"测试数据插入错误: {err}")


# 根据用户ID获取账户信息的函数
def get_account_info(user_id):
    try:
        # 获取数据库连接
        conn = get_db_connection()
        # 创建游标，并设置cursor的返回结果为字典形式，方便获取数据
        cursor = conn.cursor(dictionary=True)
        # 执行查询语句，从accounts表中查询指定用户ID的用户信息
        cursor.execute(
            "SELECT user_id, password, balance FROM accounts WHERE user_id = %s",
            (user_id,)
        )
        # 获取查询结果的第一行（因为user_id唯一，最多一行结果），以字典形式返回
        return cursor.fetchone()
    except mysql.connector.Error as err:
        # 如果查询过程中发生错误，记录错误信息到日志文件
        logging.error(f"数据库查询错误: {err}")
        return None
    finally:
        # 无论查询结果如何，都关闭游标和数据库连接
        cursor.close()
        conn.close()


# 更新账户余额的函数
def update_balance(user_id, amount):
    try:
        # 获取数据库连接
        conn = get_db_connection()
        # 创建游标
        cursor = conn.cursor()

        # 执行原子操作：余额检查和更新，只有当余额大于等于取款金额时才更新余额
        cursor.execute(
            "UPDATE accounts SET balance = balance - %s WHERE user_id = %s AND balance >= %s",
            (amount, user_id, amount)
        )

        # 提交事务，保存更新操作
        conn.commit()
        # 返回受影响的行数是否大于0，大于0表示更新成功，否则失败
        return cursor.rowcount > 0
    except mysql.connector.Error as err:
        # 如果更新过程中发生错误，记录错误信息到日志文件
        logging.error(f"数据库更新错误: {err}")
        return False
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        conn.close()


# 记录操作日志的函数
def log_operation(user_id, op_type, result, error=None):
    """修改后的日志记录函数"""
    try:
        # 获取数据库连接
        conn = get_db_connection()
        # 创建游标
        cursor = conn.cursor()

        # 执行参数化查询，将操作日志插入到operation_logs表中
        # 如果error存在且长度超过255，截取前255个字符
        cursor.execute(
            "INSERT INTO operation_logs (user_id, operation_type, operation_result, error_message) "
            "VALUES (%s, %s, %s, %s)",
            (
                user_id,
                op_type,  # 现在包含金额信息
                result,
                error[:255] if error else None
            )
        )
        # 提交事务，保存日志记录
        conn.commit()
    except Exception as e:
        # 如果在记录日志过程中发生错误，记录错误信息到日志文件
        logging.error(f"日志记录失败: {str(e)}")
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        conn.close()


# 处理客户端连接的函数
def handle_client(client_socket):
    # 记录当前已登录的用户ID，初始值为None
    current_user = None
    current_password = None
    try:
        # 循环接收和处理客户端消息，直到客户端断开连接
        while True:
            # 从客户端套接字接收最多1024字节的数据，并解码为字符串，去除字符串两端的空白字符
            data = client_socket.recv(1024).decode().strip()
            # 如果接收到的消息为空，说明客户端已断开连接，跳出循环
            if not data:
                break

            # 将接收到的消息按空格分割成列表
            parts = data.split()
            # 如果分割后的列表长度小于1，说明消息格式不正确，继续接收下一条消息
            if len(parts) < 1:
                continue

            # 获取消息中的命令部分
            cmd = parts[0]

            # HELO处理（保持原有逻辑）
            if cmd == 'HELO':
                if len(parts) == 2:
                    user_id = parts[1]
                    if get_account_info(user_id):
                        current_user = user_id
                        client_socket.send(b'500 sp AUTH REQUIRED!')
                        log_operation(user_id, 'HELO', '成功')
                    else:
                        client_socket.send(b'401 sp ERROR!')
                        log_operation(None, 'HELO', '失败', '无效用户ID')
                else:
                    client_socket.send(b'401 sp ERROR!')
                    log_operation(None, 'HELO', '失败', '报文格式错误')

            # PASS处理（增加参数验证）
            elif cmd == 'PASS':
                if current_user and len(parts) == 2:
                    if current_user:
                        account = get_account_info(current_user)
                        if account and account['password'] == parts[1]:
                            client_socket.send(b'525 OK!')
                            current_password = parts[1]
                            log_operation(current_user, '登录', '成功')
                        else:
                            client_socket.send(b'401 sp ERROR!')
                            log_operation(current_user, '登录', '失败', '密码错误')
                    else:
                        client_socket.send(b'401 sp ERROR!')
                        log_operation(None, '登录', '失败', '无效用户ID')
                else:
                    client_socket.send(b'401 sp ERROR!')
                    log_operation(current_user, '登录', '失败', '报文格式错误')

            # BALA处理（精确协议响应）
            elif cmd == 'BALA':
                if current_user:
                    if current_password:
                        account = get_account_info(current_user)
                        if account:
                            # 严格遵循协议格式，保留两位小数
                            response = f"AMNT:{account['balance']:.2f}"
                            client_socket.send(response.encode())
                            log_operation(current_user, '余额查询', '成功')
                        else:
                            client_socket.send(b'401 sp ERROR!')
                            log_operation(current_user, '余额查询', '失败', '数据库查询错误')
                    else:
                        client_socket.send(b'401 sp ERROR!')
                        log_operation(None, '余额查询', '失败', '请提供用户ID对应的密码')
                else:
                    client_socket.send(b'401 sp ERROR!')
                    log_operation(None, '余额查询', '失败', '无效用户ID')

            # 如果命令是WDRA（取款）
            elif cmd == 'WDRA':
                # 如果无效用户ID
                if not current_user:
                    # 向客户端发送无效用户ID的响应
                    client_socket.send(b'401 sp ERROR!')
                    # 调用log_operation函数记录取款操作日志，结果为失败，错误信息为未认证
                    log_operation(None, '取款', '失败', error='无效用户ID')
                    continue

                if not current_password:
                    # 向客户端发送无效用户ID的响应
                    client_socket.send(b'401 sp ERROR!')
                    # 调用log_operation函数记录取款操作日志，结果为失败，错误信息为未认证
                    log_operation(None, '取款', '失败', error='请提供用户ID对应的密码')
                    continue

                 # 如果消息格式不正确（命令后参数个数不为1）
                if len(parts) != 2:
                    # 向客户端发送错误响应
                    client_socket.send(b'401 sp ERROR!')
                    # 调用log_operation函数记录取款操作日志，结果为失败，错误信息为参数错误
                    log_operation(current_user, '取款', '失败', error='报文格式错误')
                    continue

                try:
                    # 将取款金额转换为浮点数，并保留两位小数
                    amount = round(float(parts[1]), 2)
                    # 如果金额小于等于0
                    if amount <= 0:
                        # 向客户端发送错误响应
                        client_socket.send(b'401 sp ERROR!')
                        # 调用log_operation函数记录取款操作日志，结果为失败，错误信息为金额必须大于0
                        log_operation(current_user, '取款', '失败', error='金额必须大于0')
                        continue

                    # 如果更新余额成功
                    if update_balance(current_user, amount):
                        # 向客户端发送成功响应
                        client_socket.send(b'525 OK!')
                        # 调用log_operation函数记录取款操作日志，结果为成功，并在操作类型中包含取款金额
                        log_operation(current_user, f'取款-{amount:.2f}', '成功')
                    else:
                        # 向客户端发送错误响应
                        client_socket.send(b'401 sp ERROR!')
                        # 调用log_operation函数记录取款操作日志，结果为失败，并在操作类型中包含取款金额，错误信息为余额不足
                        log_operation(current_user, f'取款-{amount:.2f}', '失败', error='余额不足')
                except ValueError:
                    # 调用log_operation函数记录取款操作日志，结果为失败，错误信息为金额格式错误
                    log_operation(current_user, '取款', '失败', error='取款金额格式错误')
                    # 向客户端发送错误响应
                    client_socket.send(b'401 sp ERROR!')
                except Exception as e:
                    # 调用log_operation函数记录取款操作日志，结果为失败，错误信息为系统错误及具体异常信息
                    log_operation(current_user, '取款', '失败', error=str(e))
                    # 向客户端发送错误响应
                    client_socket.send(b'401 sp ERROR!')
    finally:
        # 无论是否发生异常，都关闭客户端套接字连接
        client_socket.close()


# 主函数
def main():
    # 配置日志记录
    # 设置日志文件名为atm_server.log
    # 日志级别为INFO，即记录INFO及以上级别的日志
    # 日志格式包含时间、日志级别和日志消息
    logging.basicConfig(
        filename='server.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # 初始化数据库，创建账户表和操作日志表
    init_database()
    # 插入测试数据到accounts表
    insert_test_data()

    # 创建TCP套接字
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置套接字选项，允许地址重用
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 将套接字绑定到所有可用的本地地址，端口为2525
    server.bind(('0.0.0.0', 2525))
    # 开始监听，最大连接数为5
    server.listen(5)

    # 记录服务器启动信息到日志文件
    logging.info("服务器已启动，监听端口2525...")

    # 循环接受客户端连接
    while True:
        # 接受客户端连接，返回客户端套接字和客户端地址
        client, addr = server.accept()
        # 创建新线程来处理客户端连接
        threading.Thread(target=handle_client, args=(client,)).start()


if __name__ == "__main__":
    # 如果当前脚本是主程序，执行main函数
    main()