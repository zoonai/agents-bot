import requests
import urllib.parse
from fake_useragent import UserAgent
import time
import json
from datetime import datetime, timedelta
import threading
import random
from colorama import Fore, Style, init
from threading import Lock

# Inisialisasi colorama untuk pewarnaan teks
init(autoreset=True)

# Fungsi untuk menghitung waktu hingga tengah malam UTC
def time_until_midnight_utc():
    now = datetime.utcnow()
    midnight_utc = datetime.combine(now + timedelta(days=1), datetime.min.time())
    seconds_until_midnight = (midnight_utc - now).total_seconds()
    print(f"{Fore.CYAN}🕛 MENUNGGU RESET TASK, DILANJUT DALAM {seconds_until_midnight / 3600:.2f} JAM!{Style.RESET_ALL}")
    return seconds_until_midnight

# Fungsi untuk memecah data dan mengambil username dari authorization token atau user data
def extract_username(authorization):
    try:
        parsed_data = urllib.parse.parse_qs(authorization)
        user_data_json = parsed_data.get('user', [''])[0]
        user_data = json.loads(urllib.parse.unquote(user_data_json))
        username = user_data.get("username", "unknown")
        return username
    except (json.JSONDecodeError, KeyError):
        return "unknown"

# Fungsi untuk membaca authorization dari file query.txt
def load_authorizations_with_usernames(file_path):
    with open(file_path, "r") as file:
        authorizations = file.readlines()

    auth_with_usernames = [{"authorization": auth.strip(), "username": extract_username(auth)} for auth in authorizations]
    return auth_with_usernames

# Fungsi untuk mengupdate jumlah tiket terbaru
def update_ticket_count(headers):
    url_get_tasks = "https://api.agent301.org/getMe"
    response = requests.post(url_get_tasks, headers=headers)
    if response.status_code == 200:
        json_response = response.json()
        if json_response.get("ok"):
            result = json_response.get("result", {})
            tickets = result.get("tickets", 0)
            return tickets
    return 0

# Fungsi untuk mendapatkan sisa kuota menonton iklan
def get_remaining_ads_quota(headers):
    url_get_tasks = "https://api.agent301.org/getMe"
    response = requests.post(url_get_tasks, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        if json_response.get("ok"):
            result = json_response.get("result", {})
            tasks = result.get("tasks", [])
            for task in tasks:
                if task.get("type") == "video":
                    max_count = task.get("max_count", 25)
                    count = task.get("count", 0)
                    remaining_ads = max_count - count
                    print(f"{Fore.YELLOW}📺 Sisa kuota iklan: {remaining_ads}/{max_count}{Style.RESET_ALL}")
                    return remaining_ads
    return 0

# Fungsi untuk menjalankan auto task menonton iklan
def auto_watch_ads(headers, authorization, username):
    url_complete_task = "https://api.agent301.org/completeTask"
    
    # Dapatkan sisa kuota iklan pengguna
    remaining_ads = get_remaining_ads_quota(headers)
    
    if remaining_ads <= 0:
        print(f"{Fore.RED}📵 Tidak ada kuota iklan yang tersisa.{Style.RESET_ALL}")
        return
    
    ads_watched = 0
    
    while ads_watched < remaining_ads:
        print(f"{Fore.LIGHTYELLOW_EX}🎬 Menonton iklan ke-{ads_watched + 1} dari {remaining_ads}{Style.RESET_ALL}")
        time.sleep(20)  # Simulasi menonton video selama 20 detik
        
        # Klaim task setelah nonton iklan
        task_data = {"type": "video"}  # Ganti dengan jenis task yang sesuai
        try:
            response = requests.post(url_complete_task, headers=headers, json=task_data)
            
            if response.status_code == 200 and response.json().get("ok"):
                result = response.json().get("result", {})
                reward = result.get("reward", 0)
                balance = result.get("balance", 0)
                ads_watched += 1
                print(f"{Fore.GREEN}🎉 Iklan selesai: Reward {reward} AP | Balance: {balance} AP{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❗ Gagal klaim task iklan ke-{ads_watched + 1}, coba lagi...{Style.RESET_ALL}")
                time.sleep(5)  # Tambahkan delay retry
                continue
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❗ Terjadi kesalahan jaringan: {str(e)}. Retry...{Style.RESET_ALL}")
            time.sleep(5)  # Retry setelah delay kecil
            continue
        
        # Menambahkan delay agar server tidak terlalu sering menerima request
        time.sleep(10)  # Tambahkan cooldown setelah setiap iklan
        
    print(f"{Fore.CYAN}🎉 Semua iklan selesai ditonton untuk akun {username}.{Style.RESET_ALL}")

# Fungsi untuk klaim task dan auto-spin Wheel
def claim_tasks_and_auto_spin(authorization, account_number, username):
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "authorization": authorization.strip(),
        "origin": "https://telegram.agent301.org",
        "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    url_get_tasks = "https://api.agent301.org/getMe"
    response = requests.post(url_get_tasks, headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        if json_response.get("ok"):
            result = json_response.get("result", {})
            balance = result.get("balance", 0)
            tickets = result.get("tickets", 0)  # Jumlah tiket untuk Wheel
            print(f"{Fore.CYAN}🎉 #ACCOUNT {username} | SALDO: {balance} AP | TIKET: {tickets}{Style.RESET_ALL}")
            print(random.choice([
                f"{Fore.GREEN}💫 Bersiap menjalankan Auto Spin dan Task rutin...{Style.RESET_ALL}",
                f"{Fore.YELLOW}🎡 Menjalankan, auto spin wheel dan task rutin!{Style.RESET_ALL}",
                f"{Fore.MAGENTA}🚀 Auto task dimulai, siap mengumpulkan doku!{Style.RESET_ALL}"
            ]))

            # Lakukan Spin Wheel otomatis jika ada tiket
            if tickets > 0:
                print(f"{Fore.LIGHTBLUE_EX}⚡️ Ada {tickets} tiket siap digunakan untuk Wheel Spin!{Style.RESET_ALL}")
                spin_wheel(headers, tickets, authorization)
            else:
                print(f"{Fore.RED}❗ Tiket habis, menjalankan watch ads task...{Style.RESET_ALL}")
                auto_watch_ads(headers, authorization, username)
        else:
            print(f"{Fore.RED}⛔ Gagal mengambil data task. Coba lagi!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}🚨 HTTP Error: {response.status_code} - Tidak dapat mengakses API!{Style.RESET_ALL}")

def spin_wheel(headers, available_tickets, authorization):
    url_spin_wheel = "https://api.agent301.org/wheel/spin"
    prizepool = {
        "t1": "1 Tiket",
        "t3": "3 Tiket",
        "c10000": "10k AP",
        "c1000": "1k AP",
        "nt1": "1 $NOT",
        "nt5": "5 $NOT",
        "tc1": "0.01 $TON",
        "tc40": "0.4 $TON",
    }

    # Fetch the initial number of tickets
    available_tickets = update_ticket_count(headers)
    if available_tickets == 0:
        print(f"{Fore.RED}🎫 Tidak ada tiket tersisa untuk spin.{Style.RESET_ALL}")
        return

    while available_tickets > 0:
        print(f"{Fore.LIGHTCYAN_EX}🎫 Tiket tersisa: {available_tickets}. Siap untuk spin!{Style.RESET_ALL}")
        response = requests.post(url_spin_wheel, headers=headers)
        if response.status_code == 200 and response.json().get("ok"):
            print(f"{Fore.MAGENTA}🌀 Melakukan Spin... Tunggu 15 detik...{Style.RESET_ALL}")
            time.sleep(15)  # Simulasi durasi spin 15 detik
            result = response.json().get("result", {})
            reward = result.get("reward", "Tidak Ada Hadiah")
            prize = prizepool.get(reward, reward)

            # Menambahkan warna pada hasil spin
            print(f"{Fore.GREEN}🎁 Hasil spin: {Fore.YELLOW}Hore Dapet {prize}!{Style.RESET_ALL}")

            # Menunggu pembaruan dari prizepool
            print(f"{Fore.LIGHTBLUE_EX}⏳ Memproses hadiah yang didapatkan...{Style.RESET_ALL}")
            time.sleep(5)  # Tambahan waktu tunggu setelah hadiah didapatkan

            # Jika reward adalah t1 atau t3, tambahkan tiket baru ke total
            if reward == "t1":
                print(f"{Fore.YELLOW}🎟️ Lau dapet 1 tiket ekstra prend!{Style.RESET_ALL}")
            elif reward == "t3":
                print(f"{Fore.YELLOW}🎟️🎟️🎟️ Alig! 3 tiket ekstra didapat!{Style.RESET_ALL}")

            # After each spin, fetch the updated ticket count from the API
            available_tickets = update_ticket_count(headers)
            print(f"{Fore.LIGHTCYAN_EX}🎟️ Tiket diperbarui dari API: {available_tickets}{Style.RESET_ALL}")

            # Memisahkan log setiap spin
            print(f"{Fore.LIGHTWHITE_EX}{'-' * 50}{Style.RESET_ALL}")

        else:
            print(f"{Fore.RED}❌ Spin gagal, tiketmu habis cuk!{Style.RESET_ALL}")
            break

        if available_tickets == 0:
            print(f"{Fore.RED}🎫 Tiketmu habis cuk!{Style.RESET_ALL}")
            break

        # Tambahkan delay 10 detik sebelum spin berikutnya
        print(f"{Fore.LIGHTGREEN_EX}⌛️ Cooldown spin selama 10 detik...{Style.RESET_ALL}")
        time.sleep(10)

    # Setelah selesai, perbarui jumlah tiket dari API untuk kepastian akhir
    final_ticket_count = update_ticket_count(headers)
    print(f"{Fore.CYAN}🔄 Periksa ulang tiket dari API: {final_ticket_count}{Style.RESET_ALL}")
    return final_ticket_count

# Fungsi untuk menjalankan task harian pada 00:00 UTC
def reset_task_at_midnight(auth_data):
    while True:
        seconds_until_midnight = time_until_midnight_utc()
        time.sleep(seconds_until_midnight)  # Tidur hingga 00:00 UTC

        # Jalankan task untuk setiap akun pada 00:00 UTC
        for account_number, data in enumerate(auth_data, start=1):
            authorization = data["authorization"]
            username = data["username"]

            print(f"\n{Fore.LIGHTMAGENTA_EX}{'-' * 36}")
            print(f"🌙 RESET TASK UNTUK AKUN KE#{account_number} ({username}) DIMULAI!")
            print(f"{'-' * 36}{Style.RESET_ALL}")

            # Auto-clear tasks and spin wheel
            claim_tasks_and_auto_spin(authorization, account_number, username)

# Fungsi utama untuk menjalankan task rutin kapan saja
def main():
    auth_data = load_authorizations_with_usernames("query.txt")

    # Jalankan thread terpisah untuk menjalankan task setiap 00:00 UTC
    reset_thread = threading.Thread(target=reset_task_at_midnight, args=(auth_data,))
    reset_thread.daemon = True  # Thread ini akan berhenti saat main thread berhenti
    reset_thread.start()

    # Loop utama untuk task rutin yang bisa dijalankan kapanpun
    while True:
        for account_number, data in enumerate(auth_data, start=1):
            authorization = data["authorization"]
            username = data["username"]

            print(f"\n{Fore.CYAN}{'-' * 36}")
            print(f"✅ MENJALANKAN TASK RUTIN UNTUK AKUN KE#{account_number} ({username})")
            print(f"{'-' * 36}{Style.RESET_ALL}")

            # Jalankan task rutin (misalnya auto-watch ads)
            claim_tasks_and_auto_spin(authorization, account_number, username)

        print(random.choice([
            f"{Fore.LIGHTGREEN_EX}⏳ Task selesai, tunggu 24 jam lagi...{Style.RESET_ALL}",
            f"{Fore.MAGENTA}🌀 Semua task sudah selesai, looping lagi dalam 24 jam!{Style.RESET_ALL}",
            f"{Fore.YELLOW}🚀 Task berikutnya akan dimulai dalam 24 jam!{Style.RESET_ALL}"
        ]))
        time.sleep(86400)  # Misalnya menunggu 24 jam sebelum menjalankan task lagi

if __name__ == "__main__":
    main()
