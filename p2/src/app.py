# src/app.py

def load_dataset(filename="data/data.csv"):
    # Tarea del Sprint 1
    return []



def is_valid_method(method):
    if method is None:
        return False
    return method.upper() == "GET"


def is_valid_status(status):
    return False


def is_valid_resource(resource):
    return False


def is_valid_user_agent(ua):
    return False


def analyze_dataset(data):
    # Tarea del Sprint 2
    return data


def generate_stats(data):
    # Tarea del Sprint 3
    return {
        "Download 200": 0, "Download 206": 0,
        "Bad status": 0, "Bad method": 0,
        "Bad format resource": 0, "Bot detected": 0
    }


def list_top_programs(data):
    return []


def list_top_k_programs(programs, k):
    return []


def list_episodes(data):
    return []


def recommend(observations, episode_set, user):
    return []
