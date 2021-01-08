#!/usr/bin/python3

# pyTelegramBotAPI - https://github.com/eternnoir/pyTelegramBotAPI
import telebot
# pyTelegramBotAPI - required for middleware
from telebot import apihelper

# Event logging - https://docs.python.org/3/howto/logging.html
import logging
# Regular expressions - https://docs.python.org/3/library/re.html
import re                   
# Required for Final (constants?) modifier
from typing import Final
# Required for environment access
import os
# Required to read .env file
from decouple import config

# Global variables
#########################################################

"""
Current version of this bot.
"""
VERSION: Final = 0.1

"""
Activate the middleware included to check that user has
done his own /start
"""
apihelper.ENABLE_MIDDLEWARE = True

"""
Telegram's bot token given by @BotFather
"""
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or config('TELEGRAM_TOKEN')

"""
"Database" in memory of user's tasks to do
"""
tasks = {}

# Basic config
#########################################################

bot = telebot.TeleBot(TELEGRAM_TOKEN)

telebot.logger.setLevel(logging.INFO)   # DEBUG

# Command handlers
#########################################################

@bot.message_handler(commands=['start'])
def on_command_start(message):
	"""
	Execute on /start.

	1. Show welcome message
	2. Show available commands (help message)
	3. Create the current user's "task list"

	:param message: The source message that sumoned the command
	:type message: Message
	"""
	welcome_todo(message, bot.get_me())
	help_todo(message)
	tasks[message.from_user.id] = []

@bot.message_handler(commands=['help'])
def on_command_help(message):
	"""
	Execute on /help: show the available commands.

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	help_todo(message)

@bot.message_handler(commands=['about'])
def on_command_about(message):
	"""
	Execute on /about: show the developer's information.

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	about(message.chat.id)

# Message handlers
#########################################################

@bot.message_handler(regexp=r"(^)agregar ([a-zA-Z0-9_ ]*) prioridad ([0-9]{1,})($)")
def on_add(message):
	"""
	Add a new task to do with priority

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	parts = re.match(r"(^)agregar ([a-zA-Z0-9_ ]*) prioridad ([0-9]{1,})($)", message.text)

	# print (parts.groups())
	task = parts.group(2)
	priority = parts.group(3)

	control = add_todo(message.from_user.id, task, priority)
	
	bot.reply_to(message, "OK" if control else "FAIL")

@bot.message_handler(regexp=r"(^)agregar ([a-zA-Z0-9_ ]*)($)")
def on_add_simple(message):
	"""
	Add a new task to do without priority

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	parts = re.match(r"(^)agregar ([a-zA-Z0-9_ ]*)($)", message.text)

	# print (parts.groups())
	task = parts.group(2)
	
	control = add_todo(message.from_user.id, task)
	
	bot.reply_to(message, "OK" if control else "FAIL")

@bot.message_handler(regexp=r"(^)demo($)")
def on_demo(message):
	"""
	Add demostration tasks to do

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	demo_todo(message.from_user.id)
	bot.reply_to(message, "¡Tareas de demostración agregadas!")

@bot.message_handler(regexp=r"(^)listar($)")
def on_list(message):
	"""
	List pending tasks to do

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	user_tasks = list_todo(message.from_user.id)
	response = ""
	
	for index, element in enumerate(user_tasks):
		response += "{}. {} (p {})\n".format(index, element['task'], element['priority'])

	if(len(response) == 0):
		response = "¡No tienes tareas por hacer!"

	bot.reply_to(message, response)

@bot.message_handler(regexp=r"(^)remover ([0-9]{1,})($)")
def on_remove(message):
	"""
	Remove a pending task to do

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	parts = re.match(r"(^)remover ([0-9]{1,})($)", message.text)

	task_id = parts.group(2)

	control = remove_todo(message.from_user.id, task_id)

	bot.reply_to(message, "OK" if control else "FAIL")

@bot.message_handler(regexp=r"(^)ERROR($)")
def on_error(message):
	"""
	Show an internal error message (generated by the bot)

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	# internal error message (error_text)

	try:
		response = message.error_text
	except AttributeError:
		response = "¿Dónde?"
	
	bot.reply_to(message, response)

@bot.message_handler(func=lambda message: True)
def fallback(message):
	"""
	Any other message that was not understood by the bot (fallback)

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	response = "\U0001F648 No entendí tu orden: \"{}\"".format(message.text)
	bot.reply_to(message, response)

# Support functions (bot logic)
#########################################################

def welcome_todo(message, bot_data):
	"""
	Show welcome message

	:param message: The source message that sumoned the command
	:type message: Message
	:param message: Information about this bot
	:type message: User
	"""    
	response = (
				"Hola, soy *{}* "
				"también conocido como *{}*.  "
				"Estoy aquí para ayudarte a manejar tu lista "
				"de tareas por hacer."
			   ).format(bot_data.first_name, bot_data.username)
	bot.send_message(message.chat.id, response, parse_mode="Markdown")    

def help_todo(message):
	"""
	Show help message

	:param message: The source message that sumoned the command
	:type message: Message
	"""    
	response = (
				"Estos son las órdenes y comandos disponibles:\n\n"
				"*/start* | Inicia correctamente la sesión del usuario \n\n"
				"*/help* | Este mensaje de ayuda \n\n"
				"*/about* | Información acerca del desarrollador \n\n"
				"*agregar {tarea}* | Agregar una nueva tarea por hacer (con prioridad 0) \n\n"
				"*agregar {tarea} prioridad {p}* | Agregar una nueva tarea por hacer con la prioridad especificada \n\n"
				"*demo* | Agrega cinco tareas por hacer de demostración \n\n"
				"*remover {tarea}* | Remueve una tarea pendiente por hacer \n\n"
				"*listar* | Lista las tareas pendientes por hacer \n\n"
			   )
	bot.send_message(message.chat.id, response, parse_mode="Markdown")

def add_todo(user_id, task, priority=0):
	"""
	Add a new task to do

	:param user_id: User internal identification
	:type user_id: int
	:param task: Description of the new task to do
	:type task: str
	:param priority: Priority of the new task to do
	:type priority: int
	"""    
	print(user_id.__class__.__name__)	
	print(task.__class__.__name__)	
	print(priority.__class__.__name__)	
	data = {
		"task": task,
		"priority": priority
	}
	
	tasks[user_id].append(data)

	return True

def demo_todo(user_id):
	"""
	Add demostration tasks to do

	:param user_id: User internal identification
	:type user_id: int
	"""    
	add_todo(user_id, "Estudiar Python", 10)
	add_todo(user_id, "Leer acerca de bots", 20)
	add_todo(user_id, "Aprender a amarrarme los zapatos", 30)
	add_todo(user_id, "Aprender a leer el reloj", 40)
	add_todo(user_id, "Dormir mas", 50)
		
def list_todo(user_id):
	"""
	List user's tasks to do        

	:param user_id: User internal identification
	:type user_id: int
	"""    
	return tasks[user_id]

def remove_todo(user_id, task_id):
	"""
	Remove a user's pending task to do

	:param user_id: User internal identification
	:type user_id: int
	:param task_id: ID of the task to be removed
	:type task_id: int
	"""    
	try:    
		del tasks[user_id][int(task_id)]
	except IndexError:
		return False

	return True

def about(chat_id):
	"""
	Show "about this bot" message

	:param chat_id: ID of the current chat between bot and user
	:type chat_id: int
	"""    
	response = (
				"Simple Todo Bot (pyTelegramBot) v{} \n\n"
				"Developed by Jorge I. Meza \n\n"
				"2021 \n\n"
			   ).format(VERSION)
	bot.send_message(chat_id, response, parse_mode="Markdown")
	
# Middlewares
#########################################################

@bot.middleware_handler(update_types=['message'])
def check_start_completed(bot_instance, message):
	"""
	Check the user has already made his own /start

	:param bot_instance: This bot's instance
	:type bot_instance: TeleBot
	:param message: The source message that issued the middleware
	:type message: Message
	"""    	
	# Avoid the execution of this middleware over /start command

	if message.entities is not None:
		if message.entities[0].type == "bot_command":
			if message.text in ["/start"]:
				return

	# If the user hasn't run yet the /start command,
	# set the internal error message (error_text) according and
	# set the text message on ERROR to be captured in appropiate
	# handler

	if message.from_user.id not in tasks:
		message.error_text = "Error, debes presentarte correctamente, ejecuta \"/start\" primero."
		message.text = "ERROR"

# Last steps
#########################################################

bot.polling()