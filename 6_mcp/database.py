"""
database.py - SQLite 数据库操作模块

本文件提供所有数据持久化功能，使用 SQLite 作为存储后端。

数据库表结构：
  - accounts: 存储交易账户信息（名称 → JSON 数据）
  - logs:     存储操作日志（时间、类型、消息）
  - market:   存储市场数据缓存（日期 → 股价 JSON）

所有数据都以 JSON 字符串形式存储在 TEXT 字段中，便于灵活扩展。
"""

import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

# 数据库文件路径（当前目录下的 accounts.db）
DB = "accounts.db"


# ========== 初始化数据库表 ==========
# 使用 with 语句确保连接自动关闭
with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
    # accounts 表：name 为主键，account 存储 JSON 格式的账户数据
    cursor.execute('CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)')
    # logs 表：自增 ID，记录操作日志
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            datetime DATETIME,
            type TEXT,
            message TEXT
        )
    ''')
    # market 表：按日期缓存市场数据，避免重复 API 调用
    cursor.execute('CREATE TABLE IF NOT EXISTS market (date TEXT PRIMARY KEY, data TEXT)')
    conn.commit()


def write_account(name, account_dict):
    """写入或更新账户数据。

    使用 UPSERT 语法：如果 name 已存在则更新，否则插入新行。

    Args:
        name: 账户名称（自动转为小写）
        account_dict: 账户数据字典，会被序列化为 JSON
    """
    json_data = json.dumps(account_dict)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (name, account)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET account=excluded.account
        ''', (name.lower(), json_data))
        conn.commit()


def read_account(name):
    """读取账户数据。

    Args:
        name: 账户名称（自动转为小写）

    Returns:
        dict 或 None: 账户数据字典，不存在时返回 None
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT account FROM accounts WHERE name = ?', (name.lower(),))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None


def write_log(name: str, type: str, message: str):
    """写入操作日志。

    Args:
        name: 关联的账户名称
        type: 日志类型（如 "account", "trace", "agent", "function"）
        message: 日志消息内容
    """
    now = datetime.now().isoformat()
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
        ''', (name.lower(), type, message))
        conn.commit()


def read_log(name: str, last_n=10):
    """读取最近的操作日志。

    Args:
        name: 账户名称
        last_n: 返回的日志条数（默认 10）

    Returns:
        list: 日志条目列表，每条是 (datetime, type, message) 元组
              按时间正序排列（最早的在前）
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT datetime, type, message FROM logs
            WHERE name = ?
            ORDER BY datetime DESC
            LIMIT ?
        ''', (name.lower(), last_n))
        # reversed() 将 DESC 结果转为时间正序
        return reversed(cursor.fetchall())


def write_market(date: str, data: dict) -> None:
    """缓存市场数据。

    Args:
        date: 日期字符串（如 "2025-01-15"）
        data: 股价数据字典（如 {"AAPL": 150.0, "GOOGL": 2800.0}）
    """
    data_json = json.dumps(data)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO market (date, data)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET data=excluded.data
        ''', (date, data_json))
        conn.commit()


def read_market(date: str) -> dict | None:
    """读取缓存的市场数据。

    Args:
        date: 日期字符串

    Returns:
        dict 或 None: 股价数据字典，未缓存时返回 None
    """
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM market WHERE date = ?', (date,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
