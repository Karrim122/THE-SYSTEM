import requests

class HabiticaError(Exception):
    """Custom exception for Habitica API errors."""
    pass

class HabiticaClient:
    def __init__(self, user_id, api_token):
        self.user_id = user_id
        self.api_token = api_token
        self.base_url = "https://habitica.com/api/v3"
        self.headers = {
            "x-api-user": self.user_id,
            "x-api-key": self.api_token,
            "x-client": "Streamlit-SoloLeveling-StatusWindow"
        }

    def get_user(self):
        """Fetches core user profile and stats."""
        url = f"{self.base_url}/user"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json().get("data", {})
            else:
                raise HabiticaError(f"API Error ({res.status_code}): {res.text}")
        except Exception as e:
            raise HabiticaError(f"Failed to connect to Habitica: {e}")

    def get_tasks(self, task_type="habits"):
        """Fetches tasks by type ('habits', 'dailys', 'todos')."""
        url = f"{self.base_url}/tasks/user?type={task_type}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json().get("data", [])
            return []
        except Exception:
            return []

    def get_tags(self):
        """Fetches user tags to map attributes."""
        url = f"{self.base_url}/tags"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json().get("data", [])
            return []
        except Exception:
            return []


def fetch_user_data(user_id, api_token):
    """Fetches user, tags, habits, dailies, and todos in a single bundle."""
    client = HabiticaClient(user_id, api_token)
    user_info = client.get_user()
    tags = client.get_tags()
    habits = client.get_tasks("habits")
    dailies = client.get_tasks("dailys")
    todos = client.get_tasks("todos") + client.get_tasks("completedTodos")
    
    return {
        "user": user_info,
        "tags": tags,
        "habits": habits,
        "dailies": dailies,
        "todos": todos,
    }
