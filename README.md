# libPyAgentConfiguration

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-1.3.0-green)

Easy management of the configuration of an **agent** that monitors a daemon or service and reports to **Telegram**.

`libPyAgentConfiguration` provides the terminal (TUI) workflow to **create, modify and display** an agent's configuration file: how often the agent checks the service, and the Telegram Bot Token and Chat ID used to notify. Secrets are never stored in plain text: they are encrypted with AES-256-GCM before they reach the YAML file.

It is built on top of the same author's libraries and is used by [CVE-Alert-Tool](https://github.com/erickrr-bd/CVE-Alert).

## Features

- Interactive screens (based on `dialog`) to define and modify the agent's settings.
- **Frequency** of the checks expressed in minutes, hours or days, with sane limits.
- **Telegram Bot Token** and **Chat ID** captured in a hidden input (no default value, nothing is echoed back) and stored **encrypted**.
- Each encrypted value is **bound to its field** (AES-GCM authenticated data), so an attacker with write access to the YAML file cannot swap the token and the chat ID.
- Input validation before anything is saved (frequency limits, token and chat ID format).
- Configuration file written **atomically**, with owner and permissions applied (`600` by default).
- Changes are detected by comparing data, not file hashes: nothing is written, and nothing is logged as modified, if the user changes nothing.
- Audit entries in the log file for every creation and modification (never including secret values).
- Sensitive values are masked when the configuration is displayed.
- The current secrets are **never decrypted or shown** when modifying the configuration.

## Requirements

| Requirement | Notes |
| --- | --- |
| Python | 3.10 or newer (tested with 3.13) |
| [libPyUtils](https://github.com/erickrr-bd/libPyUtils) | **>= 2.4.0** (encryption, key file handling, YAML) |
| [libPyDialog](https://github.com/erickrr-bd/libPyDialog) | **>= 2.4.0** (dialogs; also needs `pythondialog` and the `dialog` binary) |
| libPyLog | Logging |

Make sure the three libraries are installed in compatible versions: this version relies on `libPyUtils.encrypt_data(..., context=...)`, `libPyUtils.get_passphrase(..., owner=...)` and `libPyDialog.create_passwordbox(..., validator=...)`.

## Installation

```bash
git clone https://github.com/erickrr-bd/libPyAgentConfiguration.git
```

Copy `libPyAgentConfiguration.py` into your project, or add the cloned folder to your `PYTHONPATH`.

## Quick start

### 1. Create the configuration

```python
from libPyAgentConfiguration import libPyAgentConfiguration
from libPyDialog import DialogCancelled

CONFIG_FILE = "/opt/MyApp/agent/configuration/agent.yaml"
KEY_FILE = "/opt/MyApp/configuration/key"
LOG_FILE = "/var/log/MyApp/agent-tool-log"
USER, GROUP = "my_user", "my_group"

agent = libPyAgentConfiguration("MyApp Tool v1.0", context = "my_agent")

try:
	agent.define_frequency_time()
	agent.define_telegram_bot_token(KEY_FILE, user = USER)
	agent.define_telegram_chat_id(KEY_FILE, user = USER)
except DialogCancelled:
	pass  # the user pressed Cancel or ESC: nothing was saved
else:
	agent.create_file(agent.convert_object_to_dict(), CONFIG_FILE, LOG_FILE, USER, GROUP)
```

`create_file` shows its own success / error messages and writes the audit log entry. Pass `user` and `group`: the file's owner and permissions are applied right after it is written.

### 2. Modify or display it

```python
agent = libPyAgentConfiguration("MyApp Tool v1.0", context = "my_agent")

agent.modify_agent_configuration(CONFIG_FILE, KEY_FILE, LOG_FILE, USER, GROUP)
agent.display_agent_configuration(CONFIG_FILE, LOG_FILE, USER, GROUP)
```

`modify_agent_configuration` asks which fields to change (frequency, bot token, chat ID), applies only those, and saves the file only when something actually changed.

### 3. Read it from the agent (decrypting the secrets)

```python
from libPyUtils import libPyUtils

utils = libPyUtils()
data = utils.read_yaml_file(CONFIG_FILE)

passphrase = utils.get_passphrase(KEY_FILE, owner = USER)
try:
	token = utils.decrypt_data(data["telegram_bot_token"], passphrase, context = "my_agent:telegram_bot_token")
	chat_id = utils.decrypt_data(data["telegram_chat_id"], passphrase, context = "my_agent:telegram_chat_id")
finally:
	utils.zeroize(passphrase)
```

The context passed to `decrypt_data` must be exactly `"<context>:<field>"`, where `<context>` is the value given to the constructor. A mismatch (or a swapped value) fails the authentication check.

## Configuration file

```yaml
frequency_time:
  minutes: 5
telegram_bot_token:
- !!binary |   # ciphertext
  ...
- !!binary |   # nonce
  ...
- !!binary |   # authentication tag
  ...
- !!binary |   # salt
  ...
telegram_chat_id:
- ...
```

| Field | Type | Description |
| --- | --- | --- |
| `frequency_time` | mapping with one entry | Unit and total: `minutes` (1-1440), `hours` (1-720) or `days` (1-365). |
| `telegram_bot_token` | list of 4 binary values | `(ciphertext, nonce, tag, salt)` encrypted with AES-256-GCM. |
| `telegram_chat_id` | list of 4 binary values | Same format as the bot token. |

When a file is loaded (`convert_dict_to_object`), `frequency_time` is validated and a `ValueError` is raised if it is malformed. Validate it in your agent too: never trust a file you did not just write.

### Accepted values

| Value | Rule |
| --- | --- |
| Bot Token | `<digits>:<hash>`, for example `123456789:AAH...` (5+ digits, 30+ characters after the colon) |
| Chat ID | An integer (negative for groups and channels) or a public `@channel` name |
| Frequency | Whole number inside the limits shown above for the chosen unit |

## The key file

Secrets are encrypted with a key derived (PBKDF2-HMAC-SHA256, 600,000 iterations) from a passphrase stored in a **key file**. `libPyUtils.get_passphrase` refuses to use it unless it is:

- a regular file (symbolic links are rejected),
- owned by root, by the current user or by the `user` you pass,
- not accessible by group or others (for example `0600`),
- not empty and not larger than 4 KB.

Keep the key file out of version control and outside of backups that also contain the configuration file: anyone who has both can decrypt the secrets.

## API reference

### `libPyAgentConfiguration(backtitle = "", context = "agent")`

| Parameter | Description |
| --- | --- |
| `backtitle` | Text displayed in the background of the dialogs. |
| `context` | Prefix that binds the encrypted values to your agent. Use a different value for each agent. |

### Methods

| Method | Description |
| --- | --- |
| `define_frequency_time()` | Asks for the unit of time and the total. |
| `define_telegram_bot_token(key_file, user = None)` | Asks (hidden input) for the bot token and stores it encrypted. |
| `define_telegram_chat_id(key_file, user = None)` | Asks (hidden input) for the chat ID and stores it encrypted. |
| `convert_object_to_dict()` | Returns the configuration as a dictionary, ready to be saved. |
| `convert_dict_to_object(data)` | Loads and validates a dictionary read from the file. |
| `create_file(data, file, log_file, user, group, mode = "600")` | Writes the file atomically, applies owner and permissions, and logs it. |
| `modify_agent_configuration(file, key_file, log_file, user, group, mode = "600")` | Interactive modification of the selected fields. |
| `modify_frequency_time(log_file, user, group)` | Modifies the frequency (used by `modify_agent_configuration`). |
| `modify_telegram_bot_token(key_file, log_file, user, group)` | Replaces the bot token. |
| `modify_telegram_chat_id(key_file, log_file, user, group)` | Replaces the chat ID. |
| `display_agent_configuration(file, log_file, user, group)` | Shows the file with the sensitive data masked. |

### Cancelling

When the user presses **Cancel** or **ESC** in a dialog, `libPyDialog` raises `DialogCancelled` (a subclass of `KeyboardInterrupt`). The `define_*` methods let it propagate, so catch it as shown in the quick start. `create_file`, `modify_agent_configuration` and `display_agent_configuration` handle it internally.

## Security notes

- The Telegram token and chat ID are never pre-filled, never displayed, never logged and never decrypted by this library: modifying a value always means entering a new one.
- Secret buffers and the passphrase are overwritten in memory after use. Python cannot guarantee that every copy of a `str` is wiped, so treat this as best-effort hardening, not as a guarantee.
- Run the tool and your agent with the fewest privileges that work, and restrict the configuration and key files to the service user.
- Errors are written to the log file with their details; the dialogs only show a generic message.

## Migrating from 1.2

Version 1.3.0 contains breaking changes:

- **Requires libPyUtils >= 2.4.0 and libPyDialog >= 2.4.0.** The previous version used `get_hash_from_file`, which no longer exists, and calling `modify_agent_configuration` failed.
- **Secrets are bound to a context.** Existing values were encrypted without one. libPyUtils can still read them with `decrypt_data(..., allow_legacy = True)`, but they should be re-entered with this version, and `allow_legacy` disabled afterwards.
- **No default values.** The token and chat ID dialogs used to be pre-filled; they now start empty and use a hidden input.
- **`define_telegram_bot_token` and `define_telegram_chat_id` take an optional `user`** to verify the owner of the key file.
- **Default file permissions are `600`** (previously `640`). Pass `mode = "640"` to keep group read access.
- **Stricter validation.** Frequency limits and token / chat ID formats are now enforced when entering the data, and a malformed file is rejected when loaded.
- **Cancel handling** uses `DialogCancelled`, a subclass of `KeyboardInterrupt`, so existing `except KeyboardInterrupt` blocks keep working.

## Author

**Erick Roberto Rodriguez Rodriguez**
[erodriguez@tekium.mx](mailto:erodriguez@tekium.mx) · [erickrr.tbd93@gmail.com](mailto:erickrr.tbd93@gmail.com) · [GitHub](https://github.com/erickrr-bd/libPyAgentConfiguration)
