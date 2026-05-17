
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor 
from vk_api.upload import VkUpload 
import matplotlib.pyplot as plt 
import os
import time
import threading
import schedule
import config
import moex_parser
import db_manager

def create_keyboard():
    keyboard = VkKeyboard(one_time=False)
   
    keyboard.add_button('📊 Рынок', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📈 Статистика', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line() 
    
    keyboard.add_button('🔔 Рассылка', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    
    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('✉️ Предложить актив', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def create_and_upload_chart(vk_session):
    history = db_manager.get_moex_history()
    if not history:
        return None
        
    dates = [row[0][-5:] for row in history] 
    prices = [row[1] for row in history]

    # Рисуем график
    plt.figure(figsize=(8, 4))
    plt.plot(dates, prices, marker='o', linestyle='-', color='blue', linewidth=2)
    plt.title("Динамика индекса Мосбиржи (IMOEX)")
    plt.xlabel("Дата")
    plt.ylabel("Значение (п.)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    
    filepath = "temp_chart.png"
    plt.savefig(filepath)
    plt.close() 

    
    upload = VkUpload(vk_session)
    photo = upload.photo_messages(filepath)[0]
    attachment = f"photo{photo['owner_id']}_{photo['id']}"
    
    
    os.remove(filepath)
    
    return attachment

def fetch_all_market_data():
    imoex = moex_parser.get_asset_price("IMOEX", "index")
    usd = moex_parser.get_asset_price("USD000UTSTOM", "currency")
    cny = moex_parser.get_asset_price("CNYRUB_TOM", "currency")
    gold = moex_parser.get_asset_price("GLDRUB_TOM", "currency")
    
    gazp = moex_parser.get_asset_price("GAZP", "share")
    lkoh = moex_parser.get_asset_price("LKOH", "share")
    tatn = moex_parser.get_asset_price("TATN", "share")
    
    
    db_manager.add_quote("IMOEX", imoex)
    db_manager.add_quote("USD", usd)
    
    reply = (
        f"📊 Сводка с Мосбиржи:\n\n"
        f"📈 Индекс IMOEX: {imoex} п.\n"
        f"💵 Доллар (USD): {usd} руб.\n"
        f"🇨🇳 Юань (CNY): {cny} руб.\n"
        f"🥇 Золото: {gold} руб/г\n\n"
        f"💼 Акции:\n"
        f"Газпром: {gazp} руб.\n"
        f"Лукойл: {lkoh} руб.\n"
        f"Татнефть: {tatn} руб."
    )
    return reply

def send_morning_newsletter():
    vk_session = vk_api.VkApi(token=config.VK_TOKEN)
    vk = vk_session.get_api()
    subscribers = db_manager.get_all_subscribers()
    if not subscribers:
        return
    
    market_text = fetch_all_market_data()
    final_message = f"☀️ Доброе утро!\nВот твоя ежедневная сводка:\n\n{market_text}"
    
    for user_id in subscribers:
        try:
            vk.messages.send(user_id=user_id, random_id=get_random_id(), message=final_message, keyboard=create_keyboard())
        except Exception:
            pass

def schedule_loop():
    schedule.every().day.at("08:00").do(send_morning_newsletter)
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    threading.Thread(target=schedule_loop, daemon=True).start()
    
    vk_session = vk_api.VkApi(token=config.VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
    
    print("Вроде бы работает. Ждем сообщений.")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            user_msg = event.obj.message['text'].lower()
            user_id = event.obj.message['from_id']
            
            
            db_manager.check_or_add_user(user_id)
            
            if user_msg == "❓ помощь":
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message="Я твой финансовый ассистент 💼.\n\n📊 Рынок — актуальные цены\n📈 Статистика — график индекса Мосбиржи\n🔔 Рассылка — вкл/выкл ежедневные уведомления\n✉️ Предложить актив — связь с разработчиком", keyboard=create_keyboard())
                
            elif user_msg == "📊 рынок":
                reply = fetch_all_market_data()
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message=reply, keyboard=create_keyboard())
                
            elif user_msg == "📈 статистика":
                
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message="⏳ Формирую график, секундочку...", keyboard=create_keyboard())
                
                
                attachment = create_and_upload_chart(vk_session)
                
                if attachment:
                    vk.messages.send(user_id=user_id, random_id=get_random_id(), message="📈 Вот график изменения индекса IMOEX за все время наблюдений:", attachment=attachment, keyboard=create_keyboard())
                else:
                    vk.messages.send(user_id=user_id, random_id=get_random_id(), message="❌ Пока недостаточно данных для построения графика.", keyboard=create_keyboard())
                
            elif user_msg == "🔔 рассылка":
                new_status = db_manager.toggle_subscription(user_id)
                reply = "✅ Вы успешно подписались на ежедневную рассылку!" if new_status == 1 else "❌ Вы отписались от ежедневной рассылки."
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message=reply, keyboard=create_keyboard())
                
            elif user_msg == "✉️ предложить актив":
                reply = "Хочешь добавить еще катировок? Напиши разработчику напрямую: @crimsonpig"
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message=reply, keyboard=create_keyboard())
                
            else:
                vk.messages.send(user_id=user_id, random_id=get_random_id(), message="Привет! 👋 Я бот для отслеживания фондового рынка.\n\nВоспользуйся кнопками меню ниже!", keyboard=create_keyboard())

if __name__ == '__main__':
    main()