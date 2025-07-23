"""
Author: Erick Roberto Rodriguez Rodriguez
Email: erodriguez@tekium.mx, erickrr.tbd93@gmail.com
GitHub: https://github.com/erickrr-bd/libPyAgentConfiguration
libPyAgentConfiguration v1.0 - April 2025
"""
from os import path
from libPyLog import libPyLog
from libPyUtils import libPyUtils
from libPyDialog import libPyDialog
from dataclasses import dataclass, field

@dataclass
class libPyAgentConfiguration:
	"""
	Easy management of agent configuration for monitoring daemons or services.
	"""

	frequency_time: dict = field(default_factory = dict)
	telegram_bot_token: tuple = field(default_factory = tuple)
	telegram_chat_id: tuple = field(default_factory = tuple)


	def __init__(self, backtitle: str = ""):
		"""
		Class constructor.

		Parameters:
			backtitle (str): Text displayed in the background.
		"""
		self.logger = libPyLog()
		self.utils = libPyUtils()
		self.dialog = libPyDialog(backtitle)


	def define_frequency_time(self) -> None:
		"""
		Method that defines the frequency with which the agent validates the status of the daemon or service.
		"""
		UNIT_TIME = [["minutes", "Time expressed in minutes", 1], ["hours", "Time expressed in hours", 0], ["days", "Time expressed in days", 0]]

		option = self.dialog.create_radiolist("Select a option:", 10, 50, UNIT_TIME, "Unit Time")
		total_time = self.dialog.create_integer_inputbox(f"Enter the total in {option} each time the service status is validated:", 9, 50, "1")
		self.frequency_time = {option : int(total_time)}


	def define_telegram_bot_token(self, key_file: str) -> None:
		"""
		Method that defines the Telegram Bot Token.

		Parameters:
			key_file (str): Key file path.
		"""
		passphrase = self.utils.get_passphrase(key_file)
		self.telegram_bot_token = self.utils.encrypt_data(self.dialog.create_inputbox("Enter the Telegram Bot Token:", 8, 50, "751988420:AAHrzn7RXWxVQQNha0tQUzyouE5lUcPde1g"), passphrase)


	def define_telegram_chat_id(self, key_file: str) -> None:
		"""
		Method that defines the Telegram Chat ID.

		Parameters:
			key_file (str): Key file path.
		"""
		passphrase = self.utils.get_passphrase(key_file)
		self.telegram_chat_id = self.utils.encrypt_data(self.dialog.create_inputbox("Enter the Telegram Chat ID:", 8, 50, "-1002365478941"), passphrase)


	def convert_object_to_dict(self) -> dict:
		"""
		Method that converts an object of type libPyAgentConfiguration into a dictionary.

		Returns:
			agent_configuration_json (dict): Dictionary with the object's data.
		"""
		agent_configuration_json = {
			"frequency_time" : self.frequency_time,
			"telegram_bot_token" : self.telegram_bot_token,
			"telegram_chat_id" : self.telegram_chat_id
		}

		return agent_configuration_json


	def convert_dict_to_object(self, agent_configuration_data: dict) -> None:
		"""
		Method that converts a dictionary into an object of type libPyAgentConfiguration.

		Parameters:
			agent_configuration_data (dict): Dictionary to convert.
		"""
		unit_time = list(agent_configuration_data["frequency_time"].keys())[0]
		self.frequency_time = {unit_time : agent_configuration_data["frequency_time"][unit_time]}
		self.telegram_bot_token = agent_configuration_data["telegram_bot_token"]
		self.telegram_chat_id = agent_configuration_data["telegram_chat_id"]


	def create_file(self, agent_configuration_data: dict, agent_configuration_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that creates the YAML file corresponding to the Agent configuration.

		Parameters:
			agent_configuration_data (dict): Data to save in the YAML file.
			agent_configuration_file (str): Agent configuration file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		try:
			self.utils.create_yaml_file(agent_configuration_data, agent_configuration_file)
			self.utils.change_owner(agent_configuration_file, user, group, "640")
			if path.exists(agent_configuration_file):
				self.dialog.create_message("\nAgent configuration created.", 7, 50, "Notification Message")
				self.logger.create_log("Agent configuration created", 2, "__createAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)
		except Exception as exception:
			self.dialog.create_message("\nError creating Agent configuration. For more information, see the logs.", 8, 50, "Error Message")
			self.logger.create_log(exception, 4, "_createAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)
		except KeyboardInterrupt:
			pass
		finally:
			raise KeyboardInterrupt("Exit")


	def modify_agent_configuration(self, agent_configuration_file: str, key_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the Agent configuration.

		Parameters:
			agent_configuration_file (str): Agent Configuration file path.
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		AGENT_CONFIGURATION_FIELDS = [("Frequency Time", "Frequency at which the service is validated", 0), ("Bot Token", "Telegram Bot Token", 0), ("Chat ID", "Telegram channel identifier", 0)]

		try:
			options = self.dialog.create_checklist("Select one or more options:", 10, 70, AGENT_CONFIGURATION_FIELDS, "Agent Configuration Fields")
			agent_configuration_data = self.utils.read_yaml_file(agent_configuration_file)
			self.convert_dict_to_object(agent_configuration_data)
			original_hash = self.utils.get_hash_from_file(agent_configuration_file)
			if "Frequency Time" in options:
				self.modify_frequency_time(log_file_name, user, group)
			if "Bot Token" in options:
				self.modify_telegram_bot_token(key_file, log_file_name, user, group)
			if "Chat ID" in options:
				self.modify_telegram_chat_id(key_file, log_file_name, user, group)
			agent_configuration_data = self.convert_object_to_dict()
			self.utils.create_yaml_file(agent_configuration_data, agent_configuration_file)
			new_hash = self.utils.get_hash_from_file(agent_configuration_file)
			if new_hash == original_hash:
				self.dialog.create_message("\nAgent Configuration not modified.", 7, 50, "Notification Message")
			else:
				self.dialog.create_message("\nAgent Configuration modified.", 7, 50, "Notification Message")
		except Exception as exception:
			self.dialog.create_message("\nError modifying Agent configuration. For more information, see the logs.", 8, 50, "Error Message")
			self.logger.create_log(exception, 4, "_modifyAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)
		except KeyboardInterrupt:
			pass
		finally:
			raise KeyboardInterrupt("Exit")


	def modify_frequency_time(self, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the frequency with which the agent validates the status of the service.

		Parameters:
			agent_configuration_file (str): Agent Configuration file path.
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		UNIT_TIME = [["minutes", "Time expressed in minutes", 1], ["hours", "Time expressed in hours", 0], ["days", "Time expressed in days", 0]]

		old_unit_time = list(self.frequency_time.keys())[0]

		for unit in UNIT_TIME:
			if unit[0] == old_unit_time:
				unit[2] = 1
			else:
				unit[2] = 0

		option = self.dialog.create_radiolist("Select a option:", 10, 50, UNIT_TIME, "Unit Time")
		total_time = self.dialog.create_integer_inputbox(f"Enter the total in {option} each time the service status is validated:", 9, 50, str(self.frequency_time[old_unit_time]))
		self.frequency_time = {option : int(total_time)}
		self.logger.create_log(f"Frequency time modified: {self.frequency_time}", 3, "_modifyAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)


	def modify_telegram_bot_token(self, key_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the Telegram Bot Token.

		Parameters:
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		passphrase = self.utils.get_passphrase(key_file)
		self.telegram_bot_token = self.utils.encrypt_data(self.dialog.create_inputbox("Enter the Telegram Bot Token:", 8, 50, self.utils.decrypt_data(self.telegram_bot_token, passphrase).decode("utf-8")), passphrase)
		self.logger.create_log("Telegram Bot Token modified.", 3, "_modifyAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)


	def modify_telegram_chat_id(self, key_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the Telegram Chat ID.

		Parameters:
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		passphrase = self.utils.get_passphrase(key_file)
		self.telegram_chat_id = self.utils.encrypt_data(self.dialog.create_inputbox("Enter the Telegram Chat ID:", 8, 50, self.utils.decrypt_data(self.telegram_chat_id, passphrase).decode("utf-8")), passphrase)
		self.logger.create_log("Telegram Chat ID modified.", 3, "_modifyAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)


	def display_agent_configuration(self, agent_configuration_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that displays the contents of the Agent configuration file.

		Parameters:
			agent_configuration_file (str): Agent configuration file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		try:
			agent_configuration_data = self.utils.convert_yaml_to_str(agent_configuration_file)
			text = "\nData:\n\n" + agent_configuration_data
			self.dialog.create_scrollbox(text, 18, 70, "Agent Configuration")
		except Exception as exception:
			self.dialog.create_message("\nError displaying Agent configuration. For more information, see the logs.", 8, 50, "Error Message")
			self.logger.create_log(exception, 4, "_displayAgentConfiguration", use_file_handler = True, file_name = log_file_name, user = user, group = group)
		except KeyboardInterrupt:
			pass
		finally:
			raise KeyboardInterrupt("Exit")
			