import telebot
import threading
from telebot import types
import subprocess
import os
import re
import requests
import json

BOT_TOKEN = "our_bot_token"

bot = telebot.TeleBot(BOT_TOKEN)

admin_id = 6598357832

####################
# Ban Unban Command#
####################

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id == admin_id:
        admin_start(message)
    elif is_user_banned(user_id):
        bot.send_message(message.chat.id, "You are banned! 🚫")
    else:
        normal_start(message)

def admin_start(message):
    clickmetostart = types.InlineKeyboardButton("Click Me To Start!", callback_data="clickmetostart")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(clickmetostart)
    message_text = "<b>🚀 Welcome Admin! 🤖\n\nYou have admin privileges. Use /ban [user_id] to ban a user and /unban [user_id] to unban a user.</b>"
    bot.send_message(message.chat.id, message_text, parse_mode="HTML", reply_markup=markup)

def normal_start(message):
    clickmetostart = types.InlineKeyboardButton("Click Me To Start!", callback_data="clickmetostart")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(clickmetostart)
    message_text = "<b>🚀 Welcome to our Zuzu Bot! 🤖\n\nRun your Python code effortlessly and receive the results instantly. Whether you're a beginner or an experienced coder, we're here to assist you. Just send your Python code, and we'll take care of the rest.\n\nHappy coding! 🎉</b>"
    bot.send_message(message.chat.id, message_text, parse_mode="HTML", reply_markup=markup)


@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id == admin_id:
        user_id_to_ban = extract_user_id_from_command(message.text)
        if user_id_to_ban:
            ban_user_by_id(user_id_to_ban)
            bot.send_message(message.chat.id, f"User {user_id_to_ban} has been banned! 🚫")
        else:
            bot.send_message(message.chat.id, "Invalid command format. Use /ban [user_id]")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id == admin_id:
        user_id_to_unban = extract_user_id_from_command(message.text)
        if user_id_to_unban:
            unban_user_by_id(user_id_to_unban)
            bot.send_message(message.chat.id, f"User {user_id_to_unban} has been unbanned! ✅")
        else:
            bot.send_message(message.chat.id, "Invalid command format. Use /unban [user_id]")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def extract_user_id_from_command(command):
    try:
        user_id = int(command.split(' ')[1])
        return user_id
    except (IndexError, ValueError):
        return None

def ban_user_by_id(user_id):
    banned_users = load_banned_users()
    banned_users.append(user_id)
    save_banned_users(banned_users)

def unban_user_by_id(user_id):
    banned_users = load_banned_users()
    if user_id in banned_users:
        banned_users.remove(user_id)
        save_banned_users(banned_users)

def is_user_banned(user_id):
    banned_users = load_banned_users()
    return user_id in banned_users

def load_banned_users():
    try:
        with open('banneduserlist.json', 'r') as file:
            banned_users = json.load(file)
            return banned_users
    except FileNotFoundError:
        return []

def save_banned_users(banned_users):
    with open('banneduserlist.json', 'w') as file:
        json.dump(banned_users, file)

####################
# Ban Unban Command#
####################

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("clickmetostart"))
def clickmetostart(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    addbot(message=call.message)

def run_code(message, user_code, bot_data):
  disallowed_keywords = ['while', 'print', 'While True', 'os', 'subprocess', 'flask']

  for keyword in disallowed_keywords:
      if re.search(fr'\b{re.escape(keyword)}\b', user_code):
          bot.send_message(message.chat.id, f"*Error:* Disallowed keyword found: `{keyword}`", parse_mode="Markdown")
          return

  try:
      with open(f"bot_{bot_data}.py", "w") as code_file:
          code_file.write(user_code)

      bot.send_message(message.chat.id, "<b>Your Bot is Working Now!</b>", parse_mode="HTML")

      def execute_code():
          try:
              subprocess.run(["pkill", "-f", f"bot_{bot_data}.py"])
              result = subprocess.run(["python3", f"bot_{bot_data}.py"], text=True, timeout=None, capture_output=True)

              if result.returncode == 0:
                  bot.send_message(message.chat.id, result.stdout, parse_mode="Markdown")
              else:
                  bot.send_message(message.chat.id, f"*Error:* `{result.stderr}`", parse_mode="Markdown")
          except subprocess.TimeoutExpired:
              bot.send_message(message.chat.id, "*Your Code Execution Timed Out.*", parse_mode="Markdown")

      execution_thread = threading.Thread(target=execute_code)
      execution_thread.start()

  except Exception as e:
      bot.send_message(message.chat.id, f"*Error:* `{str(e)}`", parse_mode="Markdown")

def edit_codehandler2(message, user_code, bot_data):
  run_code(message, user_code, bot_data)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("edit_code"))
def editcodehandle_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    user_id = call.from_user.id
    bot_data = call.data[9:]
    bot.send_message(user_id, "*Send Your Bot Code Or Bot File\n\nNote: Only .py files are allowed.\n\nYou clicked it by mistake. Please use the /cancel command. 🚫*", parse_mode="Markdown")

    bot.register_next_step_handler(call.message, receive_code, bot_data)

def receive_code(message, bot_data):
    user_id = message.from_user.id
    if message.text == '/cancel':
      bot.send_message(user_id, "<b>Code Editing Cancelled!</b>", parse_mode="HTML")
      return
    if message.content_type == 'text':
        user_code = message.text
        edit_codehandler2(message, user_code, bot_data)
    elif message.content_type == 'document':
        if message.document.file_name.endswith(".py") and message.document.file_size <= 2000000:
            file_info = bot.get_file(message.document.file_id)
            file = bot.download_file(file_info.file_path)

            with open(f"user_code_{message.from_user.username}.py", "wb") as code_file:
                code_file.write(file)

            user_code = open(f"user_code_{message.from_user.username}.py").read()
            os.remove(f"user_code_{message.from_user.username}.py")
            run_code(message, user_code, bot_data)
        else:
            bot.send_message(user_id, "*Invalid file format or size. Please send a valid .py file (max 2 MB).*", parse_mode="Markdown")



@bot.message_handler(commands=['addbot'])
def addbot(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "You are banned! 🚫")
    else:
        normal_addbot(message)

def normal_addbot(message):
    usid = message.chat.id
    bot.send_message(message.chat.id, "*🤖 Please provide your bot token to get started!*", parse_mode="Markdown")
    bot.register_next_step_handler(message, tokenchecker, usid)


def tokenchecker(message, usid):
    user_token = message.text
    chat_id = message.chat.id
    bot.delete_message(message.chat.id, message.message_id)
    message_id = message.message_id
    url = f'https://api.telegram.org/bot{user_token}/getMe'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        bot_username = data['result']['username']
        file_name = f"user_bots{usid}.json"
        try:
            with open(file_name, 'r') as file:
                bot_info_list = json.load(file)
        except FileNotFoundError:
            bot_info_list = []

        if any(bot_info['token'] == user_token for bot_info in bot_info_list):
            bot.send_message(message.chat.id, "*❌ You Already Added This Bot!*", parse_mode="Markdown")
        else:
            bot_info = {
                "token": user_token,
                "username": bot_username,
                "status": "Stop"
            }
            bot_info_list.append(bot_info)

            with open(file_name, 'w') as file:
                json.dump(bot_info_list, file)
            bot.send_message(message.chat.id, f"*✅ Your Bot Successfully Added!\nYour Bot Username: @{bot_username}*", parse_mode="Markdown")
            #create_bot_script(usid, bot_username, user_token)
    else:
        bot.send_message(message.chat.id, "*🚫 Oops! It seems like you entered an incorrect token. Please make sure you've provided the right one and try again. If you have any questions or need assistance, feel free to ask. We're here to help!*", parse_mode="Markdown")

def create_bot_script(usid, username, token):
  script = f"""import telebot
import json
import os
from telebot import types
import requests

token = "{token}"
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.chat.id, "*Your Bots Working!\\nMade BY-@ZexusX - BY-@ZuzuPythonBots*", parse_mode="Markdown")

bot.infinity_polling()
"""

  file_name = f"bot_{username}.py"
  with open(file_name, 'w') as file:
      file.write(script)

  try:
      result = subprocess.run(["python3", file_name], text=True, timeout=None, capture_output=True)

      if result.returncode == 0:
          bot.send_message(usid, result.stdout, parse_mode="Markdown")
      else:
          bot.send_message(usid, f"*Error:* `{result.stderr}`", parse_mode="Markdown")
  except Exception as e:
      bot.send_message(usid, f"*Error:* `{str(e)}`", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_handler(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "*You are banned! 🚫*", parse_mode="Markdown")
    else:
        normal_help(message)

def normal_help(message):
    channel = types.InlineKeyboardButton("📣 Channel", url="https://t.me/ZuzuPythonChannel")
    group = types.InlineKeyboardButton("🛠️ Helper Group", url="https://t.me/ZuzuPythonChat")
    developper = types.InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/ZexusX")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(channel, group, developper)
    bot.send_message(message.chat.id, """*👋 Hello, I'm Zuzu, your friendly Telegram bot assistant! I'm here to help you manage your Telegram bots with the power of Python.

🤖 Here are some commands you can use:

📚 General Commands:
/help - Display this help menu.
/start - Start or restart the bot.

🤖 Bot Management:
/addbot - Add a new bot to your list.
/mybots - List the bots you've added.

Feel free to use these commands to interact with me and manage your bots. If you have any questions, need assistance, or encounter any issues, don't hesitate to reach out. I'm here to make your bot development journey easier and more enjoyable! 🚀*""", parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=['mybots'])
def mybots(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "*You are banned! 🚫*", parse_mode="Markdown")
    else:
        normal_mybots(message)


def normal_mybots(message):
    user_id = message.from_user.id
    file_name = f"user_bots{user_id}.json"
    try:
        with open(file_name, 'r') as file:
            bot_info_list = json.load(file)

        bot_count = len(bot_info_list)

        if bot_count > 0:
            markup = types.InlineKeyboardMarkup(row_width=2)
            buttons = []
            for i, bot_info in enumerate(bot_info_list):
                button_text = f"@{bot_info['username']}"
                callback_data = f"bot_{bot_info['username']}"
                button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
                buttons.append(button)

                if len(buttons) == 10 or i == bot_count - 1:
                    markup.add(*buttons)
                    bot.send_message(user_id, "*Choose a bot from the list below:*", parse_mode="Markdown", reply_markup=markup)
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    buttons = []
    except FileNotFoundError:
        bot.send_message(user_id, "*You haven't added any bots yet.\nUse /addbot to add bot*", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("bot_"))
def editbot(call):
    file_name = f"user_bots{call.from_user.id}.json"
    user_id = call.from_user.id
    try:
        with open(file_name, 'r') as file:
            bot_status = json.load(file)
            bot_data = call.data[4:]
            bot_info_found = False
            for bot_info in bot_status:
                if 'status' in bot_info and bot_data == bot_info['username']:
                    botstatus = f"{bot_info['status']}"
                    bottoken = f"{bot_info['token']}"
                    get_bot_code_button = types.InlineKeyboardButton("Get Bot Code", callback_data=f"get_bot_bot_{bot_data}")

                    get_api_token_button = types.InlineKeyboardButton("Get API Token", callback_data=f"api_token_{bottoken}")

                    start_stop_button_text = f"{botstatus} Bot"
                    start_stop_button = types.InlineKeyboardButton(start_stop_button_text, callback_data=f"{botstatus}_{bot_data}")

                    back_list_button = types.InlineKeyboardButton("« Back To Bot List", callback_data="back_list")

                    delete_bot_button = types.InlineKeyboardButton("Delete Bot", callback_data=f"delete_bot_{bot_data}")
                    edit_code_button = types.InlineKeyboardButton("Edit Full Code", callback_data=f"edit_code{bot_data}")

                    markup = types.InlineKeyboardMarkup(row_width=2)
                    markup.add(get_api_token_button, start_stop_button, delete_bot_button, get_bot_code_button, edit_code_button, back_list_button)

                    bot_info_found = True
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f"*Here it is: @{bot_data}.\nWhat do you want to do with the bot?*", parse_mode="Markdown", reply_markup=markup)

            if not bot_info_found:
                bot.send_message(user_id, f"*Bot with username @{bot_data} not found.*", parse_mode="Markdown")
    except FileNotFoundError:
        bot.send_message(user_id, "*You haven't added any bots yet.*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("next_page"))
def change_page(call):
    bot_data = call.data.split("_")
    page_number = int(bot_data[-1])
    bot_data = "_".join(bot_data[2:-1])
    show_commands_page(call, bot_data, page_number)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("prev_page"))
def prev_page(call):
    bot_data = call.data.split("_")
    page_number = int(bot_data[-1])
    bot_data = "_".join(bot_data[2:-1])
    show_commands_page(call, bot_data, page_number)


def show_commands_page(call, bot_data, page_number):
    user_id = call.from_user.id
    file_name = f"bot_{bot_data}_commands.json"

    try:
        with open(file_name, 'r') as file:
            command_info_list = json.load(file)

        command_count = len(command_info_list)

        if command_count > 0:
            per_page = 9
            total_pages = (command_count + per_page - 1) // per_page

            if page_number > total_pages or page_number < 1:
                page_number = 1

            start_index = (page_number - 1) * per_page
            end_index = min(start_index + per_page, command_count)

            markup = types.InlineKeyboardMarkup(row_width=3)
            buttons = []

            for i in range(start_index, end_index):
                command_info = command_info_list[i]
                button_text = f"{command_info['commandname']}"
                callback_data = f"cmd{command_info['commandname']}:{bot_data}"
                button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
                add_cmd_button = types.InlineKeyboardButton("Add Command", callback_data=f"addcmd_{bot_data}")
                back_button = types.InlineKeyboardButton("Back", callback_data=f"bot_{bot_data}")
                buttons.append(button)
            if page_number > 1:
                prev_button = types.InlineKeyboardButton("Previous Page", callback_data=f"prev_page_{bot_data}_{page_number - 1}")
                back_button = types.InlineKeyboardButton("Back", callback_data=f"bot_{bot_data}")
                buttons.append(prev_button)


            if page_number < total_pages:
                next_button = types.InlineKeyboardButton("Next Page", callback_data=f"next_page_{bot_data}_{page_number + 1}")
                buttons.append(next_button)

            markup.add(*buttons)
            markup.add(add_cmd_button, back_button)
            text = f"<b>Your Bot Commands, Select To Edit Command Code</b>\n<code>Page: {page_number}</code>"
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="*You haven't added any commands yet.\nUse /addcommand to add a command*", parse_mode="Markdown")

    except FileNotFoundError:
        bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="*You haven't added any commands yet.\nUse /addcommand to add a command*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("addcmd_"))
def add_cmd_handler(call):
  bot_data = call.data[7:]
  bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="*Please send the command name*", parse_mode="Markdown")
  bot.register_next_step_handler(call.message, add_cmd_name_handler, bot_data)

def add_cmd_name_handler(message, bot_data):
  command_name = message.text
  if "/" in command_name:
    bot.send_message(message.chat.id, "*Invalid Command Name*\n*Command name cannot contain '/'*", parse_mode="Markdown")
  else:
    bot.send_message(message.chat.id, "*Please send the command code*", parse_mode="Markdown")
    bot.register_next_step_handler(message, add_cmd_code_handler, command_name, bot_data)

def add_cmd_code_handler(message, command_name, bot_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "<b>Code Editing Cancelled!</b>", parse_mode="HTML")
        return

    if message.content_type == 'text':
        command_code = message.text
        if "import" in command_code or "@bot.message_handler" in command_code:
            bot.send_message(message.chat.id, "*Invalid Command Code*\n*Command code cannot contain 'import' or '@bot.message_handler'", parse_mode="Markdown")
        else:
            file_name = f"bot_{bot_data}_commands.json"
            bot_file = f"bot_{bot_data}.py"
            try:
                with open(file_name, 'r') as file:
                    command_info_list = json.load(file)
            except FileNotFoundError:
                command_info_list = []

            command_info = {
                "commandname": command_name,
                "commandcode": command_code
            }

            command_info_list.append(command_info)

            with open(file_name, 'w') as file:
                json.dump(command_info_list, file)

            with open(bot_file, 'r') as bot_code_file:
                bot_code = bot_code_file.readlines()

            command_handler_code = f"@bot.message_handler(commands=['{command_name}'])\n"
            command_handler_code += f"def {command_name}_message_handler(message):\n"
            command_handler_code += f"{command_code}\n"
            command_handler_code += "\n"

            bot_code.insert(11, command_handler_code)

            with open(bot_file, 'w') as bot_code_file:
                bot_code_file.writelines(bot_code)

            bot.send_message(message.chat.id, "*Command Added Successfully*", parse_mode="Markdown")
            bot.send_message(message.chat.id, f"<b>Command Name:</b> <code>/{command_name}</code>\nPlease Stop And Re Start Your Bot To Work Code", parse_mode="HTML")
    elif message.content_type == 'document':
        if message.document.file_name.endswith(".py") and message.document.file_size <= 2000000:
            file_info = bot.get_file(message.document.file_id)
            file = bot.download_file(file_info.file_path)

            with open(f"user_code_{message.from_user.username}.py", "wb") as code_file:
                code_file.write(file)

            with open(f"user_code_{message.from_user.username}.py", "rb") as code_file:
                command_code = code_file.read().decode('utf-8')

            os.remove(f"user_code_{message.from_user.username}.py")

            if "import" in command_code or "@bot.message_handler" in command_code:
                bot.send_message(message.chat.id, "*Invalid Command Code*\n*Command code cannot contain 'import' or '@bot.message_handler'", parse_mode="Markdown")
            else:
                file_name = f"bot_{bot_data}_commands.json"
                bot_file = f"bot_{bot_data}.py"
                try:
                    with open(file_name, 'r') as file:
                        command_info_list = json.load(file)
                except FileNotFoundError:
                    command_info_list = []

                command_info = {
                    "commandname": command_name,
                    "commandcode": command_code
                }

                command_info_list.append(command_info)

                with open(file_name, 'w') as file:
                    json.dump(command_info_list, file)

                with open(bot_file, 'r') as bot_code_file:
                    bot_code = bot_code_file.readlines()

                command_handler_code = f"@bot.message_handler(commands=['{command_name}'])\n"
                command_handler_code += f"def {command_name}_message_handler(message):\n"
                command_handler_code += f"{command_code}\n"
                command_handler_code += "\n"

                bot_code.insert(9, command_handler_code)

                with open(bot_file, 'w') as bot_code_file:
                    bot_code_file.writelines(bot_code)

                bot.send_message(message.chat.id, "*Command Added Successfully*", parse_mode="Markdown")
                bot.send_message(message.chat.id, f"<b>Command Name:</b> <code>/{command_name}</code>\nPlease Stop And Re Start Your Bot To Work Code", parse_mode="HTML")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("cmd"))
def editcommandcodehandler(call):
    bot_data = call.data[call.data.find(':') + 1:]
    command_data = call.data[3:call.data.find(':')]
    user_id = call.from_user.id
    file_name = f"bot_{bot_data}_commands.json"

    try:
        with open(file_name, 'r') as file:
            command_info_list = json.load(file)

            command_info = next((item for item in command_info_list if item['commandname'] == command_data), None)
            if command_info:
                command_name = command_info['commandname']
                command_code = command_info['commandcode']

                if len(command_code) > 320:
                    bot.delete_message(call.from_user.id, call.message.message_id)
                    file_content = f"Made BY-Zexus - BY-Zuzu\n\nCommand Name:\n{command_name}\n\nCommand Code:\n{command_code}"

                    temp_file_name = f"Made BY-Zuzu_{command_name}.py"

                    with open(temp_file_name, 'w') as temp_file:
                        temp_file.write(file_content)
                    edit_code_btn = types.InlineKeyboardButton("Edit Command Code", callback_data=f"editcmd{bot_data}:{command_data}")
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.add(edit_code_btn)
                    bot.send_document(user_id, document=open(temp_file_name, 'rb'), caption=f"<b>Command Info:</b>\n\n<b>Command Name:</b>\n<code>/{command_name}</code>", parse_mode="HTML", reply_markup=markup)

                    os.remove(temp_file_name)
                else:
                    back_bot_settings = types.InlineKeyboardButton("Back Commands", callback_data=f"edit_command{bot_data}")
                    edit_code_btn = types.InlineKeyboardButton("Edit Command Code", callback_data=f"editcmd{bot_data}:{command_data}")
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    markup.add(edit_code_btn, back_bot_settings)
                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f"<b>Command Info:</b>\n\n<b>Command Name:</b>\n<code>/{command_name}</code>\n\n<b>Command Code:</b>\n<code>{command_code}</code>", parse_mode="HTML", reply_markup=markup)
            else:
                bot.send_message(user_id, f"Command with name '{command_data}' not found.", parse_mode="HTML")
    except FileNotFoundError:
        bot.send_message(chat_id=call.from_user.id, text="*Your Command is Not Have A Code Click Edit Command Code Button To Add Some Code*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("editcmd"))
def editcmd_handler(call):
  bot.delete_message(call.from_user.id, call.message.message_id)
  command_data = call.data[call.data.find(':') + 1:]
  bot_data = call.data[7:call.data.find(':')]
  user_id = call.from_user.id
  file_name = f"bot_{bot_data}_commands.json"
  try:
     with open(file_name, 'r') as file:
        command_info_list = json.load(file)

        command_info = next((item for item in command_info_list if item['commandname'] == command_data), None)
        if command_info:
            command_name = command_info['commandname']
            command_code = command_info['commandcode']

            bot.send_message(user_id, "*Send Your Bot Code Or Bot File\n\nNote: Only .py files are allowed.\n\nYou clicked it by mistake. Please use the /cancel command. 🚫*", parse_mode="Markdown")

            bot.register_next_step_handler(call.message, edit_code_handler, bot_data, command_data)

  except FileNotFoundError:
      bot.send_message(call.from_user.id, "*You haven't added any commands yet.\nUse /addcommand to add a command*", parse_mode="Markdown")

def edit_code_handler(message, bot_data, command_data):
  user_id = message.from_user.id
  if message.text == '/cancel':
      bot.send_message(user_id, "<b>Code Editing Cancelled!</b>", parse_mode="HTML")
      return

  if message.content_type == 'text':
      user_code = message.text
      edit_code_handler2(message, user_code, bot_data, command_data)
  elif message.content_type == 'document':
      if message.document.file_name.endswith(".py") and message.document.file_size <= 2000000:
          file_info = bot.get_file(message.document.file_id)
          file = bot.download_file(file_info.file_path)

          with open(f"user_edit_code_{message.from_user.username}.py", "wb") as code_file:
              code_file.write(file)

          with open(f"user_edit_code_{message.from_user.username}.py", "r") as code_file:
              user_code = code_file.read()
          edit_code_handler2(message, user_code, bot_data, command_data)
          os.remove(f"user_edit_code_{message.from_user.username}.py")
      else:
          bot.send_message(user_id, "*Invalid file format or size. Please send a valid .py file (max 2 MB).*", parse_mode="Markdown")


def edit_code_handler2(message, user_code, bot_data, command_data):
  bots_data = bot_data[bot_data.find(':') + 1:]
  commands_data = command_data
  user_id = message.from_user.id
  new_command_code = user_code

  file_name = f"bot_{bots_data}_commands.json"
  bot_file = f"bot_{bots_data}.py"

  try:
      with open(file_name, 'r') as file:
          command_info_list = json.load(file)
          for command_info in command_info_list:
              if command_info['commandname'] == commands_data:
                  old_command_code = command_info['commandcode']
                  command_info['commandcode'] = new_command_code

                  with open(file_name, 'w') as updated_file:
                    json.dump(command_info_list, updated_file, indent=4)

                  bot.send_message(message.from_user.id, f"*Your command (/{commands_data}) has been successfully updated!*", parse_mode="Markdown")

                  with open(bot_file, 'r') as bot_code_file:
                    bot_code = bot_code_file.read()

                  bot_code = bot_code.replace(old_command_code, new_command_code)

                  with open(bot_file, 'w') as updated_bot_code_file:
                    updated_bot_code_file.write(bot_code)
                    bot.send_message(message.from_user.id, f"*Your bot has been successfully updated!*", parse_mode="Markdown")
                    mybots(message)
                    return
  except FileNotFoundError:
    bot.send_message(message.from_user.id, "*You haven't added any commands yet.\nUse /addcommand to add a command*", parse_mode="Markdown")

  bot.send_message(message.from_user.id, f"Command '{commands_data}' not found or an error occurred.", parse_mode="Markdown")

@bot.message_handler(commands=['addcommand'])
def addcomand_handler(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "*You are banned! 🚫*", parse_mode="Markdown")
    else:
        normal_addcom(message)

def normal_addcom(message):
  user_id = message.chat.id
  file_name = f"user_bots{user_id}.json"
  try:
      with open(file_name, 'r') as file:
          bot_info_list = json.load(file)

      bot_count = len(bot_info_list)

      if bot_count > 0:
          markup = types.InlineKeyboardMarkup(row_width=2)
          buttons = []
          for i, bot_info in enumerate(bot_info_list):
              button_text = f"@{bot_info['username']}"
              callback_data = f"addcmd_{bot_info['username']}"
              button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
              buttons.append(button)

              if len(buttons) == 10 or i == bot_count - 1:
                  markup.add(*buttons)
                  bot.send_message(message.chat.id, f"*🤗 Welcome {message.from_user.first_name}!\n🤖 Select Bot To Add Command*", parse_mode="Markdown", reply_markup=markup)
                  markup = types.InlineKeyboardMarkup(row_width=2)
                  buttons = []
  except FileNotFoundError:
      bot.send_message(message.chat.id, "*You haven't added any bots yet.\nUse /addbot to add bot*", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("edit_command"))
def editcommandhandler(call):
    bot_data = call.data[12:]
    user_id = call.from_user.id
    file_name = f"bot_{bot_data}_commands.json"

    try:
        with open(file_name, 'r') as file:
            command_info_list = json.load(file)

        command_count = len(command_info_list)

        if command_count > 0:
            page_number = 1
            show_commands_page(call, bot_data, page_number)
        else:
            bot.send_message(chat_id=call.from_user.id, text="*You haven't added any command yet.\nUse /addcommand to add command*", parse_mode="Markdown")

    except FileNotFoundError:
        bot.send_message(chat_id=call.from_user.id, text="*You haven't added any command yet.\nUse /addcommand to add command*", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("back_list"))
def back_listhandler(call):
  user_id = call.from_user.id
  file_name = f"user_bots{user_id}.json"
  try:
      with open(file_name, 'r') as file:
          bot_info_list = json.load(file)

      bot_count = len(bot_info_list)

      if bot_count > 0:
          markup = types.InlineKeyboardMarkup(row_width=2)
          buttons = []
          for i, bot_info in enumerate(bot_info_list):
              button_text = f"@{bot_info['username']}"
              callback_data = f"bot_{bot_info['username']}"
              button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
              buttons.append(button)

              if len(buttons) == 10 or i == bot_count - 1:
                  markup.add(*buttons)
                  bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="*Choose a bot from the list below:*", parse_mode="Markdown", reply_markup=markup)
                  markup = types.InlineKeyboardMarkup(row_width=2)
                  buttons = []
  except FileNotFoundError:
      bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="*You haven't added any bots yet.\nUse /addbot to add bot*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("get_bot_"))
def get_bot_file(call):
    bot.delete_message(call.from_user.id, call.message.message_id)
    user_id = call.from_user.id
    bot_data = call.data[8:]

    file_name = f"{bot_data}.py"

    try:
        with open(file_name, 'rb') as file:
            bot.send_document(user_id, file, caption="*Here is Your Bot File*", parse_mode="Markdown")
    except FileNotFoundError:
        bot.send_message(user_id, "*🚫Your bot is not available code!*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("api_token_"))
def get_api_token(call):
    file_name = f"user_bots{call.from_user.id}.json"
    try:
        with open(file_name, 'r') as file:
            bot_status = json.load(file)
            bot_data = call.data[10:]
            found = False

            for bot_info in bot_status:
                if 'username' in bot_info and bot_data == bot_info['token']:
                    user_id = call.from_user.id
                    apitoken = call.data[10:]
                    bot_data2 = bot_info['username']
                    back = types.InlineKeyboardButton("« Back To Bot", callback_data=f"bot_{bot_data2}")
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.add(back)

                    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f"<b>Here is the token for bot</b>\n@{bot_data2}:\n\n<code>{apitoken}</code>", parse_mode="HTML", reply_markup=markup)
                    found = True

            if not found:
                bot.send_message(call.from_user.id, "*Bot not found.*", parse_mode="Markdown")
    except FileNotFoundError:
        bot.send_message(call.from_user.id, "*You haven't added any bots yet.*", parse_mode="Markdown")


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("delete_bot_"))
def delete_bot(call):
    bot_data = call.data[11:]
    yes_delete = types.InlineKeyboardButton("Yes, Delete The Bot", callback_data=f"yes_delete{bot_data}")
    back = types.InlineKeyboardButton("« Back To Bot", callback_data=f"bot_{bot_data}")
    no_never = types.InlineKeyboardButton("Nope, Nevermind", callback_data=f"no_never{bot_data}")
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(yes_delete, no_never, back)
    bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text=f"*You are about to delete your bot @{bot_data}. Is that correct?*", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("yes_delete"))
def yes_delete_(call):
    bot.delete_message(call.from_user.id, call.message.message_id)
    bot_data = call.data[10:]
    user_id = call.from_user.id
    bot_file_name = f"bot_{bot_data}.py"
    json_file_name = f"user_bots{user_id}.json"

    try:
        with open(bot_file_name, 'rb') as file:
            bot.send_document(user_id, file)
            os.remove(bot_file_name)
    except FileNotFoundError:
        return

    with open(json_file_name, 'r') as json_file:
        bot_data_list = json.load(json_file)

    updated_bot_data_list = [bot for bot in bot_data_list if bot['username'] != bot_data]

    with open(json_file_name, 'w') as json_file:
        json.dump(updated_bot_data_list, json_file)

    bot.send_message(user_id, "*✅ Your Bot has been deleted successfully!*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("no_never"))
def no_no_delete(call):
    bot.delete_message(call.from_user.id, call.message.message_id)
    bot.send_message(call.from_user.id, "*Okey, No Problem 🤗*", parse_mode="Markdown")



def toggle_bot_status(bot_data, user_id):
    file_name = f"user_bots{user_id}.json"

    with open(file_name, 'r') as json_file:
        data = json.load(json_file)

    for bot_info in data:
        if 'status' in bot_info and bot_info['username'] == bot_data:

            bot_info['status'] = "Stop" if bot_info['status'] == "Start" else "Start"

    with open(file_name, 'w') as json_file:
        json.dump(data, json_file, indent=4)

@bot.callback_query_handler(func=lambda callback: callback.data.startswith("St"))
def startstophandler(call):
    bot.delete_message(call.from_user.id, call.message.message_id)
    status, bot_data = call.data.split("_", 1)
    user_id = call.from_user.id
    file_name = f"bot_{bot_data}.py"

    if status == "Start":
        try:
            subprocess.Popen(["python3", f"{file_name}"])
            bot.send_message(call.from_user.id, "<b>✅ Your Bot is Working Now!</b>", parse_mode="HTML")
            toggle_bot_status(bot_data, user_id)
            #mybots(message)
        except Exception as e:
            bot.send_message(user_id, f"*Error starting bot: {str(e)}*", parse_mode="Markdown")
    elif status == "Stop":
        try:
            subprocess.run(["pkill", "-f", f"{file_name}"])
            bot.send_message(call.from_user.id, "<b>❌Your Bot is Not Working Now!</b>", parse_mode="HTML")
            toggle_bot_status(bot_data, user_id)
            #mybots(message)
        except Exception as e:
            bot.send_message(user_id, f"*Error stopping bot: {str(e)}*", parse_mode="Markdown")
