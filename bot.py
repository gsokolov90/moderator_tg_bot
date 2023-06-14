import telebot
import time
from dotenv import load_dotenv
from os import environ
import loguru

load_dotenv()

@loguru.logger.catch 
def run_bot():
    TOKEN = environ.get('TELEGRAM_TOKEN')
    BAD_WORDS = environ.get('BAD_WORDS').split(',')
    DELETE_LINKS = environ.get('DELETE_LINKS')

    bot = telebot.TeleBot(TOKEN)

    def is_admin(message):
        admins = [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id in admins:
            return True
        else:
            return False

    # Обработка сообщения, содержащего новых участников
    @bot.message_handler(content_types=["new_chat_members"])
    def handler_new_member(message):
        message_id = bot.send_message(message.chat.id, text=f'Добро пожаловать, @{message.new_chat_members[0].username} 👋',
                                      reply_markup=telebot.types.InlineKeyboardMarkup([
                                          [
                                              telebot.types.InlineKeyboardButton(text="👉 Правила группы",
                                                                                 callback_data='rules')
                                          ]]))
        time.sleep(10)
        bot.delete_message(message.chat.id, message_id.message_id)

    # Комманда для отображения правил
    @bot.message_handler(commands=['rules'])
    def show_rules(message):
        message_id = bot.send_message(message.chat.id, text=environ.get('RULES_TEXT'), parse_mode='Markdown')
        time.sleep(60)
        bot.delete_message(message.chat.id, message_id.message_id)
    
    # Функция обработки инлайн-запроса на просмотр правил
    @bot.callback_query_handler(func=lambda call: call.data == "rules")
    def callback_inline(call):
        message_id = bot.send_message(call.message.chat.id, text=environ.get('RULES_TEXT'), parse_mode='Markdown')
        time.sleep(60)
        bot.delete_message(call.message.chat.id, message_id.message_id)

    # Функция для удаления сообщений, которые содержат запрещенные слова (не для администраторов)  
    @bot.message_handler(func=lambda message: True)  
    def delete_bad_words(message):
        current_message_text = message.text.lower()
        is_bad = False
        for word in BAD_WORDS:
            word = word.replace(' ','').lower()
            if word in current_message_text: is_bad = True    

        if not is_admin(message) and (is_bad or (DELETE_LINKS and ('http://' in message.text or 'https://' in message.text))):
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            message_id = bot.send_message(chat_id=message.chat.id,
                                          text=f'⚠️ @{message.from_user.username}\nВаше сообщение было удалено, так как оно нарушает установленные правила сообщества. Пожалуйста, убедитесь, что вы следуете всем указанным правилам, чтобы избежать будущих проблем.', 
                                          reply_markup=telebot.types.InlineKeyboardMarkup([
                                              [
                                                  telebot.types.InlineKeyboardButton(text="👉 Правила группы", callback_data='rules')
                                              ]]))
            time.sleep(10)
            bot.delete_message(message.chat.id, message_id.message_id)

    while True:
        try:
            loguru.logger.info("Start Telegram Bot")
            bot.polling()
        except Exception as e:
            loguru.logger.exception(f"Error in bot {e}\n Restarting...")

run_bot()