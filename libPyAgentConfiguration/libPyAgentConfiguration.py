"""
Author: Erick Roberto Rodriguez Rodriguez
Email: erodriguez@tekium.mx, erickrr.tbd93@gmail.com
GitHub: https://github.com/erickrr-bd/libPyAgentConfiguration
libPyAgentConfiguration v1.3.0 - November 2026
Easy management of agent configuration for monitoring daemons or services.
Requires libPyUtils >= 2.4.0 and libPyDialog >= 2.4.0.
"""
import re
from copy import deepcopy
from os import path
from libPyLog import libPyLog
from libPyUtils import libPyUtils
from libPyDialog import libPyDialog, DialogCancelled

# Units of time offered to the user: (tag, description).
UNIT_TIME_CHOICES = (("minutes", "Time expressed in minutes"), ("hours", "Time expressed in hours"), ("days", "Time expressed in days"))

# Maximum total accepted for each unit of time.
MAX_TOTAL_BY_UNIT = {"minutes": 1440, "hours": 720, "days": 365}

AGENT_CONFIGURATION_FIELDS = (("Frequency Time", "Frequency at which the service is validated", 0), ("Bot Token", "Telegram Bot Token", 0), ("Chat ID", "Telegram channel identifier", 0))

TOKEN_REGEX = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{30,}$")
CHAT_ID_REGEX = re.compile(r"^(-?\d+|@[A-Za-z0-9_]{5,})$")


class libPyAgentConfiguration:

	def __init__(self, backtitle: str = "", context: str = "agent"):
		"""
		Class constructor.

		Parameters:
			backtitle (str): Text displayed in the background.
			context (str): Prefix that binds the encrypted secrets to this agent (authenticated by AES-GCM).
			               The service that decrypts them must use the same value.
		"""
		self.frequency_time = {}
		self.logger = libPyLog()
		self.utils = libPyUtils()
		self.context = context
		self.telegram_chat_id = None
		self.telegram_bot_token = None
		self.dialog = libPyDialog(backtitle)


	def _log(self, message, level: int, tag: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that writes an entry in the log file.
		"""
		self.logger.create_log(message, level, tag, use_file_handler = True, file_name = log_file_name, user = user, group = group)


	def _unit_choices(self, selected_unit: str) -> list:
		"""
		Method that builds the radiolist choices marking the selected unit.
		"""
		return [(unit, description, 1 if unit == selected_unit else 0) for unit, description in UNIT_TIME_CHOICES]


	def _ask_frequency(self, selected_unit: str = "minutes", current_total: int = 1) -> dict:
		"""
		Method that asks for the unit of time and the total (with limits).

		Returns:
			frequency_time (dict): {unit: total}
		"""
		unit = self.dialog.create_radiolist("Select a option:", 10, 50, self._unit_choices(selected_unit), "Unit Time")
		maximum = MAX_TOTAL_BY_UNIT[unit]
		total = self.dialog.create_integer_inputbox(f"Enter the total in {unit} ({1}-{maximum}) each time the service status is validated:", 10, 60, str(min(max(current_total, 1), maximum)), min_value = 1, max_value = maximum)
		return {unit : total}


	def _encrypt_secret(self, prompt: str, title: str, field: str, key_file: str, validator, error_message: str, user: str = None) -> tuple:
		"""
		Method that asks for a secret (hidden input, no default value) and returns it encrypted.
		"""
		passphrase = None
		secret_buffer = None
		try:
			passphrase = self.utils.get_passphrase(key_file, owner = user)
			value = self.dialog.create_passwordbox(prompt, 9, 60, True, title = title, validator = validator, error_message = error_message)
			secret_buffer = bytearray(value.encode("utf-8"))
			return self.utils.encrypt_data(secret_buffer, passphrase, context = f"{self.context}:{field}")
		finally:
			if passphrase is not None:
				self.utils.zeroize(passphrase)
			if secret_buffer is not None:
				self.utils.zeroize(secret_buffer)


	def define_frequency_time(self) -> None:
		"""
		Method that defines the frequency with which the agent validates the status of the daemon or service.
		"""
		self.frequency_time = self._ask_frequency()


	def define_telegram_bot_token(self, key_file: str, user: str = None) -> None:
		"""
		Method that defines the Telegram Bot Token.

		Parameters:
			key_file (str): Key file path.
			user (str): User expected to own the key file.
		"""
		self.telegram_bot_token = self._encrypt_secret("Enter the Telegram Bot Token:", "Bot Token", "telegram_bot_token", key_file, lambda value: TOKEN_REGEX.fullmatch(value) is not None, "Invalid Telegram Bot Token (<id>:<hash>).", user)


	def define_telegram_chat_id(self, key_file: str, user: str = None) -> None:
		"""
		Method that defines the Telegram Chat ID.

		Parameters:
			key_file (str): Key file path.
			user (str): User expected to own the key file.
		"""
		self.telegram_chat_id = self._encrypt_secret("Enter the Telegram Chat ID:", "Chat ID", "telegram_chat_id", key_file, lambda value: CHAT_ID_REGEX.fullmatch(value) is not None, "Invalid Telegram Chat ID (integer, negative for groups, or @channel).", user)


	def convert_object_to_dict(self) -> dict:
		"""
		Method that converts an object of type libPyAgentConfiguration into a dictionary.

		Returns:
			agent_configuration_json (dict): Dictionary with the object's data.
		"""
		return {
			"frequency_time" : self.frequency_time,
			"telegram_bot_token" : self.telegram_bot_token,
			"telegram_chat_id" : self.telegram_chat_id
		}


	def convert_dict_to_object(self, agent_configuration_data: dict) -> None:
		"""
		Method that converts a dictionary into an object of type libPyAgentConfiguration (the data is validated).

		Parameters:
			agent_configuration_data (dict): Dictionary to convert.
		"""
		frequency = agent_configuration_data.get("frequency_time")
		if not isinstance(frequency, dict) or len(frequency) != 1:
			raise ValueError("Invalid frequency_time in the configuration file.")
		unit, total = next(iter(frequency.items()))
		if unit not in self.utils.TIME_UNITS or isinstance(total, bool) or not isinstance(total, int) or not 1 <= total <= MAX_TOTAL_BY_UNIT[unit]:
			raise ValueError("Invalid frequency_time in the configuration file.")
		self.frequency_time = {unit : total}
		self.telegram_bot_token = agent_configuration_data["telegram_bot_token"]
		self.telegram_chat_id = agent_configuration_data["telegram_chat_id"]


	def create_file(self, agent_configuration_data: dict, agent_configuration_file: str, log_file_name: str, user: str = None, group: str = None, mode: str = "600") -> None:
		"""
		Method that creates the YAML file corresponding to the Agent configuration.

		Parameters:
			agent_configuration_data (dict): Data to save in the YAML file.
			agent_configuration_file (str): Agent configuration file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
			mode (str): Permissions of the file (octal string).
		"""
		try:
			self.utils.create_yaml_file(agent_configuration_data, agent_configuration_file)
			self.utils.change_owner(agent_configuration_file, user, group, mode)
			if path.exists(agent_configuration_file):
				self.dialog.create_message("\nAgent configuration created.", 7, 50, "Notification Message")
				self._log("Agent configuration created", 2, "_createAgentConfiguration", log_file_name, user, group)
		except Exception as exception:
			self.dialog.create_message("\nError creating Agent configuration. For more information, see the logs.", 8, 50, "Error Message")
			self._log(exception, 4, "_createAgentConfiguration", log_file_name, user, group)
		except DialogCancelled:
			pass


	def modify_agent_configuration(self, agent_configuration_file: str, key_file: str, log_file_name: str, user: str = None, group: str = None, mode: str = "600") -> None:
		"""
		Method that modifies the Agent configuration.

		Parameters:
			agent_configuration_file (str): Agent Configuration file path.
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
			mode (str): Permissions of the file (octal string).
		"""
		try:
			options = self.dialog.create_checklist("Select one or more options:", 10, 70, AGENT_CONFIGURATION_FIELDS, "Agent Configuration Fields")
			original_data = self.utils.read_yaml_file(agent_configuration_file)
			self.convert_dict_to_object(deepcopy(original_data))
			if "Frequency Time" in options:
				self.modify_frequency_time(log_file_name, user, group)
			if "Bot Token" in options:
				self.modify_telegram_bot_token(key_file, log_file_name, user, group)
			if "Chat ID" in options:
				self.modify_telegram_chat_id(key_file, log_file_name, user, group)
			new_data = self.convert_object_to_dict()
			if new_data == original_data:
				self.dialog.create_message("\nAgent Configuration not modified.", 7, 50, "Notification Message")
				return
			self.utils.create_yaml_file(new_data, agent_configuration_file)
			self.utils.change_owner(agent_configuration_file, user, group, mode)
			self._log("Agent configuration modified", 3, "_modifyAgentConfiguration", log_file_name, user, group)
			self.dialog.create_message("\nAgent Configuration modified.", 7, 50, "Notification Message")
		except Exception as exception:
			self.dialog.create_message("\nError modifying Agent configuration. For more information, see the logs.", 8, 50, "Error Message")
			self._log(exception, 4, "_modifyAgentConfiguration", log_file_name, user, group)
		except DialogCancelled:
			pass


	def modify_frequency_time(self, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the frequency with which the agent validates the status of the service.

		Parameters:
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		old_unit, old_total = next(iter(self.frequency_time.items()))
		self.frequency_time = self._ask_frequency(old_unit, old_total)
		self._log(f"Frequency time modified: {self.frequency_time}", 3, "_modifyAgentConfiguration", log_file_name, user, group)


	def modify_telegram_bot_token(self, key_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the Telegram Bot Token (the current value is never decrypted or displayed).

		Parameters:
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		self.define_telegram_bot_token(key_file, user)
		self._log("Telegram Bot Token modified.", 3, "_modifyAgentConfiguration", log_file_name, user, group)


	def modify_telegram_chat_id(self, key_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that modifies the Telegram Chat ID (the current value is never decrypted or displayed).

		Parameters:
			key_file (str): Key file path.
			log_file_name (str): Log file path.
			user (str): Owner user.
			group (str): Owner group.
		"""
		self.define_telegram_chat_id(key_file, user)
		self._log("Telegram Chat ID modified.", 3, "_modifyAgentConfiguration", log_file_name, user, group)


	def display_agent_configuration(self, agent_configuration_file: str, log_file_name: str, user: str = None, group: str = None) -> None:
		"""
		Method that displays the contents of the Agent configuration file (sensitive data masked).

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
			self._log(exception, 4, "_displayAgentConfiguration", log_file_name, user, group)
		except DialogCancelled:
			pass
	