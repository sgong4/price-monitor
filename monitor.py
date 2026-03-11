#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密货币和股票价格监控脚本
运行在 GitHub Actions 上，每 5 分钟检查一次
"""

import requests
import os
import sys
from datetime import datetime

# ============ 从环境变量获取配置 ============
SENDKEY = os.environ.get('SENDKEY', '')
TARGETS = {
    # 加密货币 (CoinGecko ID)
    'crypto': {
        'bitcoin': ('BTC', 50000),
        'ethereum': ('ETH', 1500),
        'hypeliquid': ('HYPE', 18),
    },
    # 股票 (Yahoo Finance 代码)
    'stocks': {
        '513050.SS': ('513050', 1.1),
        '001330.SZ': ('SZ001330', 3.6),
    }
}

def get_crypto_price(coin_id):
    """获取加密货币价格 (CoinGecko 免费 API)"""
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
    """获取股票价格 (Yahoo Finance)"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        return float(info['lastPrice'])
    except Exception as e:
        print(f"获取 {symbol} 价格失败：{e}")
    return None

def send_wechat_notify(title, content):
    """微信推送 (Server 酱)"""
    if not SENDKEY:
        print("⚠️ 未配置 SENDKEY，跳过微信推送")
        return False
    
    url = f'https://sctapi.ftqq.com/{SENDKEY}.send'
    data = {
        'title': title,
        'desp': content
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
        print(f"✅ 微信推送成功")
        return True
    except Exception as e:
        print(f"❌ 微信推送失败：{e}")
        return False

def check_crypto():
    """检查加密货币价格"""
    alerts = []
    for coin_id, (symbol, target) in TARGETS['crypto'].items():
        price = get_crypto_price(coin_id)
        if price:
            print(f"📊 {symbol}: ${price:.2f} (目标：${target})")
            if price >= target:
                alerts.append(f"🚨 {symbol} 突破 ${target}！当前：${price:.2f}")
    return alerts

def check_stocks():
    """检查股票价格"""
    alerts = []
    for symbol, (name, target) in TARGETS['stocks'].items():
        price = get_stock_price(symbol)
        if price:
            print(f"📈 {name}: ¥{price:.2f} (目标：¥{target})")
            if price >= target:
                alerts.append(f"🚨 {name} 突破 ¥{target}！当前：¥{price:.2f}")
    return alerts

def main():
    print(f"\n{'='*50}")
    print(f"🔍 开始检查价格 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")
    
    all_alerts = []
    
    # 检查加密货币
    print("【加密货币】")
    crypto_alerts = check_crypto()
    all_alerts.extend(crypto_alerts)
    
    # 检查股票
    print("\n【股票】")
    stock_alerts = check_stocks()
    all_alerts.extend(stock_alerts)
    
    # 发送通知
    if all_alerts:
        print(f"\n🚨 触发 {len(all_alerts)} 个提醒")
        message = '\n\n'.join(all_alerts)
        message += f"\n\n检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_wechat_notify("🔔 价格突破提醒", message)
    else:
        print("\n✅ 无触发条件")
    
    print(f"\n{'='*50}\n")
    return 0

if __name__ == '__main__':
    sys.exit(main())
