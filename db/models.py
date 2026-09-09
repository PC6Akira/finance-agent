"""SQLAlchemy 模型（7 张表）。"""
from sqlalchemy import Column, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Fund(Base):
    """基金基本信息。"""
    __tablename__ = "funds"
    code = Column(String, primary_key=True)          # 基金代码
    name = Column(String)
    manager = Column(String)
    company = Column(String)


class FundNav(Base):
    """净值走势。"""
    __tablename__ = "fund_nav"
    fund_code = Column(String, primary_key=True)
    nav_date = Column(String, primary_key=True)
    unit_nav = Column(Float)
    daily_return = Column(Float)


class FundHolding(Base):
    """季度重仓股。"""
    __tablename__ = "fund_holdings"
    fund_code = Column(String, primary_key=True)
    quarter = Column(String, primary_key=True)
    stock_code = Column(String, primary_key=True)
    stock_name = Column(String)
    weight = Column(Float)
    shares = Column(Float)
    market_value = Column(Float)


class FundIndustryAllocation(Base):
    """季报·行业配置。"""
    __tablename__ = "fund_industry_allocation"
    fund_code = Column(String, primary_key=True)
    report_date = Column(String, primary_key=True)
    industry = Column(String, primary_key=True)
    weight = Column(Float)
    market_value = Column(Float)


class FundAnnouncement(Base):
    """基金公告元数据（全文进 Chroma）。"""
    __tablename__ = "fund_announcements"
    id = Column(String, primary_key=True)            # 报告ID
    fund_code = Column(String, index=True)
    ann_type = Column(String)                        # report / dividend / personnel
    title = Column(Text)
    publish_date = Column(String)


class Diagnosis(Base):
    """诊断结果。"""
    __tablename__ = "diagnosis"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String, index=True)
    goal = Column(Text)
    conclusion = Column(Text)
    risk_points = Column(Text)
    created_at = Column(String)


class BacktestConfig(Base):
    """回测配置。"""
    __tablename__ = "backtest_configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    config = Column(Text)                            # JSON 字符串
    created_at = Column(String)


class User(Base):
    """用户账号。"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
    created_at = Column(String)


class UserHolding(Base):
    """用户持仓。"""
    __tablename__ = "user_holdings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, index=True)
    fund_code = Column(String)
    fund_name = Column(String, nullable=True)
    amount = Column(Float)                            # 持有金额
    cost = Column(Float, nullable=True)               # 成本（可空）
    created_at = Column(String)


class Message(Base):
    """对话历史。"""
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, index=True)
    role = Column(String)                             # user / assistant
    content = Column(Text)
    created_at = Column(String)
