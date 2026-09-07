import requests

class HabiticaError(Exception):
    pass

class HabiticaClient:
    BASE_URL = "https://habitica.com/api/v3"

    def __init__(self, user_id, api_token):
        self.user_id = user_id
        self.api_token = api_token
        self.headers = {
            "x-api-user": self.user_id,
            "x-api-key": self.api_token,
            "x-client": "HunterStatusApp-Streamlit",
        }

    def _get(self, endpoint):
        try:
            res = requests.get(f"{self.BASE_URL}/{endpoint}", headers=self.headers, timeout=10)
            if res.status_code != 200:
                raise HabiticaError(f"Habitica API Error ({res.status_code}): {res.text}")
            data = res.json()
            if not data.get("success"):
                raise HabiticaError(data.get("message", "Unknown Habitica API Error"))
            return data.get("data")
        except requests.RequestException as e:
            raise HabiticaError(f"Network connection error: {e}")

    def get_user(self):
        return self._get("user")

    def get_tags(self):
        return self._get("tags")

    def get_tasks(self, task_type="tasks"):
        return self._get(f"tasks/user?type={task_type}")
