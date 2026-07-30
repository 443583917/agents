"""
accounts.py - 交易账户业务逻辑模块

本文件定义了交易账户的核心数据模型和业务逻辑。

核心类：
  - Transaction: 单笔交易记录
  - Account: 完整的交易账户，包含余额、持仓、交易历史等

账户功能：
  - 存取款（deposit / withdraw）
  - 买卖股票（buy_shares / sell_shares）
  - 计算投资组合价值和盈亏
  - 管理投资策略
  - 生成账户报告
"""

from pydantic import BaseModel
import json
from dotenv import load_dotenv
from datetime import datetime
from market import get_share_price
from database import write_account, read_account, write_log

load_dotenv(override=True)

# ========== 常量 ==========
INITIAL_BALANCE = 10_000.0  # 初始资金：$10,000
SPREAD = 0.002              # 买卖价差：0.2%（模拟交易成本）


class Transaction(BaseModel):
    """交易记录模型。

    属性：
        symbol: 股票代码
        quantity: 数量（正数为买入，负数为卖出）
        price: 交易价格（含价差）
        timestamp: 交易时间
        rationale: 交易理由
    """
    symbol: str
    quantity: int
    price: float
    timestamp: str
    rationale: str

    def total(self) -> float:
        """计算交易总金额"""
        return self.quantity * self.price

    def __repr__(self):
        return f"{abs(self.quantity)} shares of {self.symbol} at {self.price} each."


class Account(BaseModel):
    """交易账户模型。

    属性：
        name: 账户持有人名称
        balance: 现金余额
        strategy: 投资策略描述
        holdings: 持仓字典 {股票代码: 数量}
        transactions: 交易记录列表
        portfolio_value_time_series: 投资组合价值时间序列
    """
    name: str
    balance: float
    strategy: str
    holdings: dict[str, int]
    transactions: list[Transaction]
    portfolio_value_time_series: list[tuple[str, float]]

    @classmethod
    def get(cls, name: str):
        """获取或创建账户。

        如果账户不存在，自动创建一个新账户并存入数据库。

        Args:
            name: 账户持有人名称

        Returns:
            Account: 账户实例
        """
        fields = read_account(name.lower())
        if not fields:
            # 新账户：默认余额 $10,000，无持仓
            fields = {
                "name": name.lower(),
                "balance": INITIAL_BALANCE,
                "strategy": "",
                "holdings": {},
                "transactions": [],
                "portfolio_value_time_series": []
            }
            write_account(name, fields)
        return cls(**fields)

    def save(self):
        """将账户数据保存到数据库"""
        write_account(self.name.lower(), self.model_dump())

    def reset(self, strategy: str):
        """重置账户到初始状态。

        Args:
            strategy: 新的投资策略
        """
        self.balance = INITIAL_BALANCE
        self.strategy = strategy
        self.holdings = {}
        self.transactions = []
        self.portfolio_value_time_series = []
        self.save()

    def deposit(self, amount: float):
        """存入资金。

        Args:
            amount: 存入金额（必须为正数）

        Raises:
            ValueError: 金额非正数时抛出
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        print(f"Deposited ${amount}. New balance: ${self.balance}")
        self.save()

    def withdraw(self, amount: float):
        """取出资金。

        Args:
            amount: 取出金额

        Raises:
            ValueError: 余额不足时抛出
        """
        if amount > self.balance:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        print(f"Withdrew ${amount}. New balance: ${self.balance}")
        self.save()

    def buy_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """买入股票。

        交易流程：
          1. 获取当前股价
          2. 计算买入价（股价 × (1 + 价差)）
          3. 检查余额是否充足
          4. 更新持仓、记录交易、扣减余额

        Args:
            symbol: 股票代码
            quantity: 买入数量
            rationale: 买入理由

        Returns:
            str: 交易结果和最新账户信息

        Raises:
            ValueError: 余额不足或股票代码无效时抛出
        """
        price = get_share_price(symbol)
        buy_price = price * (1 + SPREAD)  # 买入价 = 股价 × 1.002
        total_cost = buy_price * quantity

        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        elif price == 0:
            raise ValueError(f"Unrecognized symbol {symbol}")

        # 更新持仓
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 记录交易
        transaction = Transaction(symbol=symbol, quantity=quantity, price=buy_price, timestamp=timestamp, rationale=rationale)
        self.transactions.append(transaction)

        # 扣减余额
        self.balance -= total_cost
        self.save()
        write_log(self.name, "account", f"Bought {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def sell_shares(self, symbol: str, quantity: int, rationale: str) -> str:
        """卖出股票。

        交易流程：
          1. 检查持仓是否足够
          2. 获取当前股价，计算卖出价（股价 × (1 - 价差)）
          3. 更新持仓（全部卖出时删除条目）、记录交易、增加余额

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            rationale: 卖出理由

        Returns:
            str: 交易结果和最新账户信息

        Raises:
            ValueError: 持仓不足时抛出
        """
        if self.holdings.get(symbol, 0) < quantity:
            raise ValueError(f"Cannot sell {quantity} shares of {symbol}. Not enough shares held.")

        price = get_share_price(symbol)
        sell_price = price * (1 - SPREAD)  # 卖出价 = 股价 × 0.998
        total_proceeds = sell_price * quantity

        # 更新持仓
        self.holdings[symbol] -= quantity
        # 如果该股票持仓为 0，从字典中删除
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 记录交易（卖出用负数表示）
        transaction = Transaction(symbol=symbol, quantity=-quantity, price=sell_price, timestamp=timestamp, rationale=rationale)
        self.transactions.append(transaction)

        # 增加余额
        self.balance += total_proceeds
        self.save()
        write_log(self.name, "account", f"Sold {quantity} of {symbol}")
        return "Completed. Latest details:\n" + self.report()

    def calculate_portfolio_value(self):
        """计算投资组合总价值 = 现金余额 + 所有持仓的市值"""
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def calculate_profit_loss(self, portfolio_value: float):
        """计算盈亏 = 当前组合价值 - 初始投入 - 当前余额"""
        initial_spend = sum(transaction.total() for transaction in self.transactions)
        return portfolio_value - initial_spend - self.balance

    def get_holdings(self):
        """返回当前持仓"""
        return self.holdings

    def get_profit_loss(self):
        """返回当前盈亏"""
        return self.calculate_profit_loss()

    def list_transactions(self):
        """返回所有交易记录（字典列表）"""
        return [transaction.model_dump() for transaction in self.transactions]

    def report(self) -> str:
        """生成账户报告（JSON 格式）。

        包含：余额、持仓、策略、交易记录、总价值、盈亏等。
        同时更新投资组合价值时间序列。

        Returns:
            str: JSON 格式的账户报告
        """
        portfolio_value = self.calculate_portfolio_value()
        self.portfolio_value_time_series.append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"), portfolio_value))
        self.save()
        pnl = self.calculate_profit_loss(portfolio_value)
        data = self.model_dump()
        data["total_portfolio_value"] = portfolio_value
        data["total_profit_loss"] = pnl
        write_log(self.name, "account", f"Retrieved account details")
        return json.dumps(data)

    def get_strategy(self) -> str:
        """返回投资策略"""
        write_log(self.name, "account", f"Retrieved strategy")
        return self.strategy

    def change_strategy(self, strategy: str) -> str:
        """更改投资策略。

        Args:
            strategy: 新策略描述

        Returns:
            str: 确认消息
        """
        self.strategy = strategy
        self.save()
        write_log(self.name, "account", f"Changed strategy")
        return "Changed strategy"


# ========== 示例用法 ==========
if __name__ == "__main__":
    account = Account("John Doe")
    account.deposit(1000)
    account.buy_shares("AAPL", 5)
    account.sell_shares("AAPL", 2)
    print(f"Current Holdings: {account.get_holdings()}")
    print(f"Total Portfolio Value: {account.calculate_portfolio_value()}")
    print(f"Profit/Loss: {account.get_profit_loss()}")
    print(f"Transactions: {account.list_transactions()}")
