from dotenv import load_dotenv
import os
import telebot
import requests
import json


load_dotenv()

# os.environ["API_KEY_TELEGRAM"]
apiKeyRecipes = os.environ["API_KEY_RECIPES"]
apiKeyTelebot = os.environ["API_KEY_TELEGRAM"]

bot = telebot.TeleBot(apiKeyTelebot)
glob_message = ''
glob_offset = 0


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, f"Hi, <b>{message.from_user.first_name} {message.from_user.last_name}</b> type recipe you are looking for", parse_mode="html")


@bot.message_handler(content_types=['text'])
def get_recipes(message, offset=0):
    global glob_message
    recipe = message.text.strip().lower()
    glob_message = message
    try:
        res = json.loads((requests.get(
            f"https://api.spoonacular.com/recipes/complexSearch?apiKey={apiKeyRecipes}&query={recipe}&offset={offset}")).text)
        if (res["totalResults"] == 0):
            bot.send_message(
                message.chat.id, f"Sorry, there are no {message.text} recipes")

        else:
            recipes = res["results"]
            for recipe in recipes:
                markup = send_markup_recipe(recipe)
                bot.send_photo(message.chat.id,
                               recipe["image"], reply_markup=markup)

        global glob_offset
        glob_offset = offset + 10
        is_offset = (glob_offset >= res["totalResults"])
        send_markup(message, is_offset)
    except Exception as e:
        print("Error: %s" % e)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'more':
        get_recipes(glob_message, glob_offset)
    elif call.data == 'search':
        bot.send_message(
            call.message.chat.id, f"Dear, <b>{call.from_user.first_name} {call.from_user.last_name}</b> type another recipe you are looking for", parse_mode="html")
    elif call.data.split(' ')[0] == "instruction":
        instruction_message = get_instructions(call.data.split(' ')[1])
        ingredients_message = get_ingredients(call.data.split(' ')[1])
        bot.send_message(call.message.chat.id,
                         instruction_message, parse_mode="html")
        bot.send_message(call.message.chat.id,
                         ingredients_message, parse_mode="html")


def send_markup(message, is_offset):
    markup = telebot.types.InlineKeyboardMarkup()
    more_btn = telebot.types.InlineKeyboardButton(
        f"more {message.text} recipes", callback_data="more")
    search_btn = telebot.types.InlineKeyboardButton(
        "search someting else 🔎", callback_data="search")
    if (is_offset):
        markup.add(search_btn)
    else:
        markup.add(more_btn, search_btn)
    bot.send_message(message.chat.id, "<b>Choose next options</b>",
                     parse_mode="html", reply_markup=markup)


def send_markup_recipe(recipe):
    markup = telebot.types.InlineKeyboardMarkup()
    recipe_instructions = "instruction {recipe}".format(recipe=recipe["id"])
    btn_recipe_title = telebot.types.InlineKeyboardButton(
        recipe["title"], callback_data=recipe_instructions)
    markup.add(btn_recipe_title)
    return markup


def send_instructions(res):
    steps = res[0]["steps"]
    instrucation_steps = '\n'
    for step in steps:
        instrucation_steps += "<b>{num}</b>. {step}\n".format(
            num=step["number"], step=step["step"])

    instrucation_message = f"<em>Steps</em>: {instrucation_steps} "
    return instrucation_message


def send_ingredients(res):
    ingredients = res["ingredients"]
    instruction_ingredients = '\n'
    for ingredient in ingredients:
        instruction_ingredients += "🔹<b>{name}</b> - {amount} {unit}\n".format(
            name=ingredient["name"], amount=ingredient["amount"]["metric"]["value"], unit=ingredient["amount"]["metric"]["unit"])
    instruction_message = f"<em>Ingredients</em>:{instruction_ingredients}"
    return instruction_message


def get_instructions(id):
    try:
        res = json.loads((requests.get(
            f"https://api.spoonacular.com/recipes/{id}/analyzedInstructions?apiKey={apiKeyRecipes}")).text)
        instruction_message = send_instructions(res)
        return instruction_message
    except Exception as e:
        print("Error: %s" % e)


def get_ingredients(id):
    try:
        res = json.loads((requests.get(
            f"https://api.spoonacular.com/recipes/{id}/ingredientWidget.json?apiKey={apiKeyRecipes}")).text)
        ingredients_message = send_ingredients(res)
        return ingredients_message
    except Exception as e:
        print("Error: %s" % e)


bot.polling(none_stop=True)
