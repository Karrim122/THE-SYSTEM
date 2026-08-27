"""
Thin wrapper around the Habitica API v3.
Docs: https://habitica.com/apidoc/
"""

import requests

BASE_URL = "https://habitica.com/api/v3"


class HabiticaError(Exception):
    pass


class HabiticaClient:
    def __init__(self, user_id: str, api_token: str):
        self.user_id = user_id
        self.api_token = api_token
        self.headers = {
            "x-api-user": user_id,
            "x-api-key": api_token,
            # Habitica asks integrations to identify themselves like this:
            "x-client": f"{user_id}-HunterStatusWindow",
            "Content-Type": "application/json",
        }

    def _get(self, path, params=None):
        resp = requests.get(f"{BASE_URL}{path}", headers=self.headers, params=params, timeout=15)
        if resp.status_code == 401:
            raise HabiticaError("Authentication failed. Check your User ID and API Token.")
        if not resp.ok:
            raise HabiticaError(f"Habitica API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", True):
            raise HabiticaError(str(data))
        return data.get("data")

    def _post(self, path, payload=None):
        resp = requests.post(f"{BASE_URL}{path}", headers=self.headers, json=payload, timeout=15)
        if resp.status_code == 401:
            raise HabiticaError("Authentication failed. Check your User ID and API Token.")
        if not resp.ok:
            raise HabiticaError(f"Habitica API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        if not data.get("success", True):
            raise HabiticaError(str(data))
        return data.get("data")

    def get_user(self):
        """Fetches profile data for the authenticated user."""
        return self._get("/user")

    def get_tags(self):
        """Returns list of {id, name} tag dicts the user has defined."""
        return self._get("/tags")

    def get_tasks(self, task_type=None):
        """
        task_type: 'habits', 'dailys', 'todos', 'completedTodos', 'rewards' or None for all.
        Returns a list of task dicts.
        """
        params = {"type": task_type} if task_type else None
        return self._get("/tasks/user", params=params)

    def get_task(self, task_id: str):
        """Fetches details for a single specific task by ID."""
        return self._get(f"/tasks/{task_id}")

    def score_task(self, task_id: str, direction: str = "up"):
        """
        Scores a task either 'up' (positive completion) or 'down' (negative habit).
        
        Parameters:
            task_id (str): Habitica task UUID
            direction (str): 'up' or 'down' (defaults to 'up')
            
        Returns:
            dict: Habitica API score response object
        """
        dir_clean = "down" if str(direction).lower() == "down" else "up"
        return self._post(f"/tasks/{task_id}/score/{dir_clean}")