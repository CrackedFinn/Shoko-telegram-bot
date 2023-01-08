from aiogram import Bot, Dispatcher, executor, types
from smsactivate.api import SMSActivateAPI
import time
import os
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=os.getenv('TOKEN'))  # Telegram bot token
dp = Dispatcher(bot)
sa = SMSActivateAPI(os.getenv('SMSTOKEN'))  # SMS-Activate token
AllowedIDs = ['501667066', '1006159742']  # Make the bot private by allowing requests only from specific Telegram IDs

kb = [[types.KeyboardButton(text="Новый номер для регистрации")]]
keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True,
                                     input_field_placeholder="")  # Create keyboard


@dp.message_handler(text="Новый номер для регистрации")  # Run action after pressing keyboard
async def get_code(message: types.Message):
    if str(message.chat.id) not in AllowedIDs:  # Delete these 2 strings to make the bot available for everyone
        return
    if float(sa.getBalance()['balance']) < 10:  # Get balance
        msg = "😔 Недостаточно средств на балансе. Обратитесь к администратору"
        await bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    else:
        number = sa.getNumberV2(service='ot', country=0)  # Get new number
        msg = str("📞 Введите данный номер для регистрации: " + number['phoneNumber'][0:1] + "`" + number['phoneNumber'][
                                                                                                  1:] + "`\n\n" + "💰 Цена: *" + str(
            int(float(number['activationCost']))) + "₽*\n\n" + "🕜 Завершите регистрацию в течении *20 мин.*")
        await bot.send_message(message.chat.id, msg, parse_mode="Markdown")  # Get number

        sa.setStatus(id=number['activationId'], status=1)  # Set status ACCESS_READY

        while str(sa.activationStatus(sa.getStatus(id=number['activationId']))["status"]).split(":", 1)[
            0] != "STATUS_OK":
            time.sleep(1)  # Wait for SMS to come

        activations = sa.getActiveActivations()
        for idfind in range(len(activations['activeActivations'])):
            if activations["activeActivations"][idfind]["activationId"] == number['activationId']:
                msg = str("🔐 Ваш код: `" +
                          activations["activeActivations"][idfind]["smsCode"][0].replace("\n", " ").split(" ")[1] + "`")
                await bot.send_message(message.chat.id, msg, parse_mode="Markdown",
                                       reply_markup=keyboard)  # Get SMS code
                break

        sa.setStatus(id=number['activationId'], status=6)  # Finish activation, set status ACCESS_ACTIVATED


@dp.message_handler(commands=['start'])  # Run after /start command
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, "Чтобы получить новый номер для регистрации, нажмите на кнопку ниже",
                           parse_mode="Markdown", reply_markup=keyboard)


if __name__ == '__main__':
    executor.start_polling(dp)
