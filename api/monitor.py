#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Cron 监控脚本
每 30 分钟自动运行一次
"""

import requests
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ============ 配置 ============
SENDKEY = os.environ.get('SENDKEY', '')
TARGETS = {
    'crypto': {
        'bitcoin': ('BTC', 50000),
        'ethereum': ('ETH', 1500),
        'hypeliquid': ('HYPE', 18),
    },
    'stocks': {
        '513050.SS': ('513050', 1.1),
        '001330.SZ': ('SZ001330', 3.6),
    }
}

def get_crypto_price(coin_id):
    """获取加密货币价格"""
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if coin_id in data:
            return data[coin_id]['usd']
    except Exception as e:
        print(f"获取 {coin_id} 价格失败：{e}")
    return None

def get_stock_price(symbol):
    """获取股票价格"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        return float(info['lastPrice'])
    except Exception as e:
        print(f"获取 {symbol} 价格失败：{e}")
    return None

def send_wechat_notify(title, content):
    """微信推送"""
    if not SENDKEY:
        print("⚠️ 未配置 SENDKEY")
        return False
    
    url = f'https://sctapi.ftqq.com/{SENDKEY}.send'
    data = {'title': title, 'desp': content}
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
        print(f"✅ 微信推送成功")
        return True
    except Exception as e:
        print(f"❌ 微信推送失败：{e}")
        return False

def check_and_notify():
    """检查价格并发送通知"""
    print(f"\n{'='*50}")
    print(f"🔍 开始检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    all_alerts = []
    
    # 检查加密货币
    print("【加密货币】")
    for coin_id, (symbol, target) in TARGETS['crypto'].items():
        price = get_crypto_price(coin_id)
        if price:
            print(f"📊 {symbol}: ${price:.2f} (目标：${target})")
            if price >= target:
                alerts.append(f"🚨 {symbol} 突破 ${target}！当前：${price:.2f}")
    
    # 检查股票
    print("\n【股票】")
    for symbol, (name, target) in TARGETS['stocks'].items():
        price = get_stock_price(symbol)
        if price:
            print(f"📈 {name}: ¥{price:.2f} (目标：¥{target})")
            if price >= target:
                all_alerts.append(f"🚨 {name} 突破 ¥{target}！当前：¥{price:.2f}")
    
    # 发送通知
    if all_alerts:
        message = '\n\n'.join(all_alerts)
        message += f"\n\n检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_wechat_notify("🔔 价格突破提醒", message)
    else:
        print("\n✅ 无触发条件")
    
    print(f"\n{'='*50}\n")

# Vercel Serverless 函数入口
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        check_and_notify()
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Monitor executed successfully')

# Cron 直接执行入口
if __name__ == '__main__':
    check_and_notify()
