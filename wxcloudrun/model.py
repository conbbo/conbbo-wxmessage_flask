'''
Date: 2025-02-06 11:47:25
LastEditors: kongbo
Description: 
LastEditTime: 2025-02-06 14:36:22
weibo: kongbo@
FilePath: /wxcloudrun/model.py
'''
from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now())


# 用户表
class Users(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'users'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(200))
    type = db.Column(db.String(100))
    stime = db.Column(db.DateTime, default=datetime.now())
