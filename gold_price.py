import requests
import json
from datetime import datetime
import os

def get_gold_price():
    """获取金价数据 - 支持多个数据源"""
    
    print("🟡 开始获取金价...")
    
    # 数据源列表（按优先级排序）
    apis = [
        {
            "name": "GoldAPI",
            "url": "https://www.goldapi.io/api/XAU/USD",
            "headers": {
                "x-access-token": "goldapi-your-token-here",
                "Content-Type": "application/json"
            },
            "parse_func": lambda data: {
                "price": data.get("price", 0),
                "currency": "USD",
                "unit": "per ounce",
                "source": "GoldAPI"
            }
        },
        {
            "name": "金投网",
            "url": "https://api.jijinhao.com/quoteCenter/realPrice.htm?code=GOLD_CNY",
            "headers": {},
            "parse_func": lambda data: {
                "price": data.get("data", {}).get("price", 0),
                "currency": "CNY",
                "unit": "元/克",
                "source": "金投网"
            }
        },
        {
            "name": "简易API",
            "url": "https://api.qingyunke.com/api.php?key=free&appid=0&msg=黄金价格",
            "headers": {},
            "parse_func": lambda data: {
                "price": float(data.get("content", "0").split(" ")[3]),
                "currency": "USD",
                "unit": "美元/盎司",
                "source": "简易API"
            }
        }
    ]
    
    # 尝试每个数据源
    for api in apis:
        try:
            print(f"正在尝试 {api['name']}...")
            
            # 如果是GoldAPI，检查是否有token
            if api["name"] == "GoldAPI":
                token = os.environ.get("GOLDAPI_TOKEN")
                if not token or token == "goldapi-your-token-here":
                    print("跳过GoldAPI（未配置token）")
                    continue
                api["headers"]["x-access-token"] = token
            
            # 发送请求
            response = requests.get(api["url"], headers=api["headers"], timeout=10)
            
            if response.status_code == 200:
                # 解析数据
                if api["name"] == "简易API":
                    # 这个API返回纯文本，需要特殊处理
                    data = json.loads(response.text)
                    price_data = api["parse_func"](data)
                else:
                    data = response.json()
                    price_data = api["parse_func"](data)
                
                if price_data["price"] > 0:
                    # 添加时间戳
                    price_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    print(f"✅ 从 {api['name']} 获取成功")
                    print(f"价格: {price_data['price']} {price_data['currency']} ({price_data['unit']})")
                    
                    return price_data
                    
        except Exception as e:
            print(f"❌ {api['name']} 失败: {e}")
            continue
    
    # 所有数据源都失败
    print("❌ 所有数据源都失败了！")
    return None

def send_to_telegram(price_data):
    """发送通知到Telegram"""
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ 未配置Telegram Bot，跳过通知")
        return
    
    message = f"""
🟡 *实时金价监控*
━━━━━━━━━━━━━━
💰 价格：*{price_data['price']}* {price_data['currency']}
📊 单位：{price_data['unit']}
🕐 时间：{price_data['timestamp']}
📡 来源：{price_data['source']}
━━━━━━━━━━━━━━
自动监控 • 每小时更新
"""
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram通知发送成功")
        else:
            print(f"❌ Telegram发送失败: {response.text}")
    except Exception as e:
        print(f"❌ Telegram错误: {e}")

def save_to_file(price_data):
    """保存数据到文件（用于历史记录）"""
    try:
        # 读取历史记录
        history = []
        try:
            with open("gold_history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []
        
        # 添加新记录
        history.append(price_data)
        
        # 只保留最近100条记录
        if len(history) > 100:
            history = history[-100:]
        
        # 保存
        with open("gold_history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        print("✅ 数据已保存到 gold_history.json")
        
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("金价监控机器人启动")
    print("=" * 50)
    
    # 获取金价
    price_data = get_gold_price()
    
    if price_data:
        # 发送通知
        send_to_telegram(price_data)
        
        # 保存数据
        save_to_file(price_data)
        
        print(f"✅ 任务完成！当前金价: {price_data['price']} {price_data['currency']}")
    else:
        print("❌ 无法获取金价数据")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
