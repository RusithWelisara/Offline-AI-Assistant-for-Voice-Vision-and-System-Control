import logging
import asyncio
import threading
import time
import subprocess
import os
import winreg
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

class Executor:
    """
    The Action Dispatcher.
    Strictly validates and routes actions to registered handlers.
    NEVER allows raw code execution.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._registry = {}
        self._register_default_actions()
        self._subscribe()

    def _subscribe(self):
        self.event_bus.subscribe("action_requested", self.handle_action_request)

    def register_action(self, name: str, handler: Callable, schema: Dict[str, type]):
        """Register a new allowed action."""
        self._registry[name] = {
            "handler": handler,
            "schema": schema
        }
        logger.info(f"Registered action: {name}")

    async def handle_action_request(self, event_data: Dict[str, Any]):
        """
        Main Dispatcher Loop.
        1. Validate action name
        2. Validate arguments strictly
        3. Execute handler
        """
        action_name = event_data.get("type") or event_data.get("name")
        args = event_data.get("params") or event_data.get("args") or {}
        
        if not action_name:
            logger.error("Action request missing 'name' or 'type'")
            return

        if action_name not in self._registry:
            logger.warning(f"BLOCKED: Unknown action '{action_name}' requested.")
            return

        entry = self._registry[action_name]
        handler = entry["handler"]
        schema = entry["schema"]

        # Strict Type Validation
        try:
            validated_args = self._validate_args(action_name, args, schema)
            logger.info(f"Dispatching action: {action_name} with {validated_args}")
            
            # Execute (some actions might be async, currently assuming sync handlers or threads)
            # If handler is async, await it. If sync, run it.
            if asyncio.iscoroutinefunction(handler):
                await handler(**validated_args)
            else:
                await asyncio.to_thread(handler, **validated_args)
                
            logger.info(f"Action {action_name} executed successfully.")
            
        except ValueError as e:
            logger.error(f"Validation failed for {action_name}: {e}")
        except Exception as e:
            logger.error(f"Execution failed for {action_name}: {e}")

    def _validate_args(self, action_name: str, args: Dict[str, Any], schema: Dict[str, type]) -> Dict[str, Any]:
        validated = {}
        for key, expected_type in schema.items():
            if key not in args:
                raise ValueError(f"Missing required argument: '{key}'")
            
            value = args[key]
            
            # Simple type check
            if not isinstance(value, expected_type):
                # Try simple conversion for int/float if it's a number-like string (optional, strict for now)
                raise ValueError(f"Argument '{key}' expected {expected_type.__name__}, got {type(value).__name__}")
            
            validated[key] = value
            
        return validated

    # -------------------------------------------------------------------------
    # Default Action Handlers
    # -------------------------------------------------------------------------
    def _register_default_actions(self):
        # 1. Start Timer
        self.register_action(
            name="start_timer",
            handler=self._handle_start_timer,
            schema={"duration_seconds": int}
        )
        
        # 2. Open App
        self.register_action(
            name="open_app",
            handler=self._handle_open_app,
            schema={"app_name": str}
        )

    def _handle_start_timer(self, duration_seconds: int):
        # We need to capture the loop from the main thread if we want to schedule back
        # Or simpler: Just log for now since the event bus is async
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        def timer_thread():
            logger.info(f"Timer started for {duration_seconds} seconds.")
            time.sleep(duration_seconds)
            logger.info("Timer finished.")
            # Notify system safely
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.event_bus.publish("user_notification", {"message": "Timer finished!"}),
                    loop
                )

        threading.Thread(target=timer_thread, daemon=True).start()

    def _handle_open_app(self, app_name: str):
        synonyms = {
            "google chrome": "chrome",
            "chrome": "chrome",
            "code": "vscode",
            "visual studio code": "vscode",
            "vscode": "vscode",
            "notepad": "notepad",
            "calculator": "calc",
            "calc": "calc",
            "cmd": "cmd",
            "command prompt": "cmd"
        }
        canonical = synonyms.get(app_name.lower())
        if not canonical:
            logger.warning(f"App '{app_name}' not in whitelist. Ignoring.")
            return

        exe_map = {
            "chrome": "chrome.exe",
            "vscode": "Code.exe",
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "cmd": "cmd.exe"
        }
        exe_name = exe_map[canonical]

        def resolve_app_path(exe: str) -> Optional[str]:
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(root, f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe}") as key:
                        path, _ = winreg.QueryValueEx(key, "")
                        if isinstance(path, str) and os.path.isfile(path):
                            return path
                except OSError:
                    pass
            common_paths = []
            if exe.lower() == "chrome.exe":
                common_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
            elif exe.lower() == "code.exe":
                common_paths = [
                    r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
                    r"C:\Program Files\Microsoft VS Code\Code.exe"
                ]
            elif exe.lower() == "notepad.exe":
                common_paths = [r"C:\Windows\System32\notepad.exe"]
            elif exe.lower() == "calc.exe":
                common_paths = [r"C:\Windows\System32\calc.exe"]
            elif exe.lower() == "cmd.exe":
                common_paths = [r"C:\Windows\System32\cmd.exe"]
            for p in common_paths:
                expanded = os.path.expandvars(p)
                if os.path.isfile(expanded):
                    return expanded
            return None

        path = resolve_app_path(exe_name)

        try:
            if path:
                logger.info(f"Opening app: {path}")
                subprocess.Popen([path], shell=False)
            else:
                logger.info(f"Opening app via shell: {exe_name}")
                try:
                    os.startfile(exe_name)
                except OSError:
                    subprocess.Popen(["cmd", "/c", "start", "", exe_name], shell=False)
        except Exception as e:
            logger.error(f"Failed to open app {app_name}: {e}")
