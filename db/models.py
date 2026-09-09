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
