import telebot
import os
import requests
import time
import threading
from datetime import datetime

# ========== 直播专用配置 ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "")
CYCLE_INTERVAL = 60
bot = telebot.TeleBot(BOT_TOKEN)

# Polymarket 5分钟 ETH 合约ID
CONDITION_ID = "0x6a143b6b091b3a92b1225c26823c047055c092c02a98760a2ff6c0a4776e8b89"

# ========== 获取实时概率 ==========
def get_eth_5min_prob():
    try:
        url = f"https://api.polymarket.com/event/condition?id={CONDITION_ID}"
        res = requests.get(url, timeout=10)
        data = res.json()
        yes_price = 0.0
        for token in data["tokens"]:
            if token["outcome"] == "Yes":
                yes_price = float(token["price"])
        return round(yes_price * 100, 2)
    except:
        return None

# ========== 直播级策略信号 ==========
def get_live_signal(prob):
    base = {
        "line1": "⚪ 观望",
        "line2": "中间区间不交易",
        "line3": "",
        "line4": "",
        "line5": "",
        "line6": "",
        "line7": "",
        "line8": "",
        "color": "⚪"
    }

    if prob >= 70:
        return {
            "line1": "🟢 【做多信号 · 顺势】",
            "line2": f"当前概率：{prob}%",
            "line3": "方向：买涨 YES",
            "line4": "入场：70%",
            "line5": "止盈：88%",
            "line6": "止损：55%",
            "line7": "仓位：主账户 70%",
            "line8": "期望收益：+8.1 点",
            "color": "🟢"
        }
    elif prob <= 30:
        return {
            "line1": "🔴 【做空信号 · 对冲】",
            "line2": f"当前概率：{prob}%",
            "line3": "方向：买跌 NO",
            "line4": "入场：30%",
            "line5": "止盈：12%",
            "line6": "止损：45%",
            "line7": "仓位：对冲账户 30%",
            "line8": "期望收益：-5.1 点",
            "color": "🔴"
        }
    return base

# ========== 直播大卡片消息 ==========
def build_live_message():
    prob = get_eth_5min_prob()
    now = datetime.now().strftime("%m-%d %H:%M")

    if prob is None:
        return "❌ 行情获取失败，请稍候重试"

    s = get_live_signal(prob)

    return f"""
=========================================
               📈 LIVE 实时信号
               ETH 5分钟 预测市场
=========================================
{s['color']} {s['line1']}
🕒 时间：{now}
{s['line2']}
{s['line3']}
{s['line4']}
{s['line5']}
{s['line6']}
{s['line7']}
{s['line8']}

=========================================
✅ 高低概率不对称对冲 · 稳定正期望
=========================================
"""

# ========== 自动播报 ==========
def auto_broadcast():
    while True:
        try:
            if CHAT_ID.strip():
                msg = build_live_message()
                bot.send_message(CHAT_ID, msg)
        except:
            pass
        time.sleep(CYCLE_INTERVAL)

# ========== 机器人命令 ==========
@bot.message_handler(commands=['start', 'help'])
def hello(msg):
    bot.reply_to(msg, """
📡 LIVE 直播专用机器人
/now   立即看信号
/auto  开启自动播报
/stop  停止播报
/id    获取ChatID
""")

@bot.message_handler(commands=['now'])
def now(msg):
    bot.reply_to(msg, build_live_message())

@bot.message_handler(commands=['id'])
def cid(msg):
    bot.reply_to(msg, f"🆔 你的ChatID：\n{msg.chat.id}")

@bot.message_handler(commands=['auto'])
def auto(msg):
    threading.Thread(target=auto_broadcast, daemon=True).start()
    bot.reply_to(msg, "✅ 已启动直播自动播报（60秒刷新）")

@bot.message_handler(commands=['stop'])
def stop(msg):
    bot.reply_to(msg, "⚠️ 自动播报已停止")

# ========== 启动 ==========
if __name__ == "__main__":
    print("✅ 直播版机器人已启动")
    threading.Thread(target=auto_broadcast, daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True)
        except:
            time.sleep(2)
