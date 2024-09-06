import requests
import urllib.parse
from fake_useragent import UserAgent
import time
import json
import sys
from colorama import Fore, Style, init

# Inisialisasi colorama untuk memastikan warna tampil di terminal
init()

# Fungsi untuk memecah data dan mengambil username dari authorization token atau user data
def extract_username(authorization):
    try:
        parsed_data = urllib.parse.parse_qs(authorization)
        user_data_json = parsed_data.get('user', [''])[0]
        user_data = json.loads(urllib.parse.unquote(user_data_json))
        username = user_data.get('username', 'unknown')
        return username
    except (json.JSONDecodeError, KeyError):
        return 'unknown'

# Fungsi untuk membaca authorization dari file query.txt
def load_authorizations_with_usernames(file_path):
    with open(file_path, 'r') as file:
        authorizations = file.readlines()

    auth_with_usernames = [{'authorization': auth.strip(), 'username': extract_username(auth)} for auth in authorizations]
    return auth_with_usernames

def print_task_progress(task_type, current, total):
    bar = '#' * (current * 50 // total)
    empty = '-' * (50 - (current * 50 // total))
    sys.stdout.write(f"\r{Fore.BLUE}#Task On Progress {task_type}{Style.RESET_ALL} {Fore.GREEN}[{bar}{empty}] {current}/{total} ({int(current / total * 100)}%){Style.RESET_ALL}")
    sys.stdout.flush()

def print_balance_update(claimed, total_balance):
    sys.stdout.write(f"\r{Fore.YELLOW}#Balance Claimed {claimed}, Balance Total {total_balance} AP{Style.RESET_ALL}")
    sys.stdout.flush()

def print_watching_video_progress(current, total, balance_reward):
    sys.stdout.write(f"\r#Watching Video [{current}%] - [ Balance {balance_reward} AP ]")
    sys.stdout.flush()

def claim_tasks(authorization, account_number, username):
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'authorization': authorization.strip(),
        'origin': 'https://telegram.agent301.org',
        'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    url_get_tasks = 'https://api.agent301.org/getMe'
    response = requests.post(url_get_tasks, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        if json_response.get("ok"):
            result = json_response.get("result", {})
            balance = result.get("balance", 0)
            print(f"{Fore.BLUE}Account{Style.RESET_ALL} : {Fore.RED}{username}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Balance{Style.RESET_ALL} : {Fore.YELLOW}{balance} AP{Style.RESET_ALL}")
            print(f"{Fore.BLUE}------------------------------------------------------------------------{Style.RESET_ALL}")

            tasks = result.get("tasks", [])
            for task in tasks:
                task_type = task.get("type")
                title = task.get("title")
                reward = task.get("reward", 0)
                is_claimed = task.get("is_claimed")
                count = task.get("count", 0)
                max_count = task.get("max_count")

                if max_count is None and not is_claimed:
                    print(f"{Fore.BLUE}#Task {task_type}{Style.RESET_ALL} {Fore.YELLOW}[ Balance {reward} AP ]{Style.RESET_ALL}")
                    claim_task(headers, task_type, title)

                elif task_type == "video" and count < max_count:
                    if max_count > 25:
                        max_count = 25

                    while count < max_count:
                        print_task_progress(task_type, count, max_count)
                        success, updated_count = watch_and_claim_video(headers, task_type, title, count, reward)
                        if success:
                            count = updated_count
                            sys.stdout.write(f"\r{Fore.BLUE}Tunggu sebentar, 5 detik sebelum lanjut...{Style.RESET_ALL}")
                            sys.stdout.flush()
                            time.sleep(5)
                        else:
                            sys.stdout.write(f"\r{Fore.RED}Gagal menonton iklan. Coba lagi...{Style.RESET_ALL}")
                            sys.stdout.flush()
                            continue
                elif not is_claimed and count >= max_count:
                    print(f"{Fore.BLUE}#Task {task_type}{Style.RESET_ALL} {Fore.YELLOW}[ Balance {reward} AP ]{Style.RESET_ALL}")
                    claim_task(headers, task_type, title)
            print(f"{Fore.BLUE}------------------------------------------------------------------------{Style.RESET_ALL}")
            print(f"{Fore.BLUE}\t\t\t   All Task Clear !!{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}Gagal mengambil task. Silahkan ulangi.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}HTTP Error: {response.status_code}{Style.RESET_ALL}")

def watch_and_claim_video(headers, task_type, title, current_count, balance_reward):
    try:
        total_duration = 20
        interval = 1
        for elapsed in range(0, total_duration + 1, interval):
            progress = int((elapsed / total_duration) * 100)
            print_watching_video_progress(progress, total_duration, balance_reward)
            time.sleep(interval)

        if claim_task(headers, task_type, title):
            return True, current_count + 1
        else:
            return False, current_count
    except Exception as e:
        sys.stdout.write(f"\r{Fore.RED}Error saat menonton atau klaim video: {str(e)}{Style.RESET_ALL}")
        sys.stdout.flush()
        return False, current_count

def claim_task(headers, task_type, title):
    url_complete_task = 'https://api.agent301.org/completeTask'
    claim_data = {"type": task_type}
    response = requests.post(url_complete_task, headers=headers, json=claim_data)

    if response.status_code == 200 and response.json().get("ok"):
        result = response.json().get("result", {})
        task_reward = result.get("reward", 0)
        balance = result.get("balance", 0)
        return True
    else:
        sys.stdout.write(f"\r{Fore.BLUE}#TASK {task_type} - {title} -{Style.RESET_ALL}{Fore.RED} Gagal klaim!{Style.RESET_ALL}\n")
        sys.stdout.flush()
        return False

def countdown(seconds):
    while seconds:
        hrs, rem = divmod(seconds, 3600)
        mins, secs = divmod(rem, 60)
        sys.stdout.write(f"\r\t\t\t       {Fore.RED}{hrs:02}{Style.RESET_ALL}{Fore.BLUE}:{Style.RESET_ALL}{Fore.YELLOW}{mins:02}{Style.RESET_ALL}{Fore.BLUE}:{Style.RESET_ALL}{Fore.GREEN}{secs:02}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(1)
        seconds -= 1
    sys.stdout.write(f"\r\t\t{Fore.RED}--WAKTU HABIS! TASK BARU TERSEDIA!--{Style.RESET_ALL}\n")
    sys.stdout.flush()
    
# Fungsi utama untuk menjalankan seluruh proses
def main():
    while True:
        auth_data = load_authorizations_with_usernames('query.txt')
        for account_number, data in enumerate(auth_data, start=1):
            authorization = data['authorization']
            username = data['username']

            print(f"{Fore.BLUE}========================================================================{Style.RESET_ALL}")
            print(f"\t\t\t      {Fore.RED}ACCOUNT : {account_number}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}========================================================================{Style.RESET_ALL}")

            claim_tasks(authorization, account_number, username)
        
        countdown(86400)

if __name__ == "__main__":
    main()
