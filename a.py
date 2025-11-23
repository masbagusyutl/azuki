import requests
import json
import time
import random
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import sys

init(autoreset=True)

def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop Azuki")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop\n")

def load_accounts():
    try:
        with open('data.txt', 'r') as file:
            accounts = [line.strip() for line in file if line.strip()]
        return accounts
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan!")
        return []

def load_proxies(filename='proxy.txt'):
    """Load proxies from a file, handling both authenticated and simple proxies"""
    try:
        with open(filename, 'r') as file:
            proxies = []
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, user, password = parts
                        proxy_url = f"http://{user}:{password}@{ip}:{port}"
                    elif len(parts) == 2:
                        ip, port = parts
                        proxy_url = f"http://{ip}:{port}"
                    else:
                        continue
                    proxies.append(proxy_url)
        
        if proxies:
            print(Fore.BLUE + f"Berhasil memuat {len(proxies)} proxy.")
        return proxies
    except FileNotFoundError:
        print(Fore.YELLOW + f"File {filename} tidak ditemukan. Melanjutkan tanpa proxy.")
        return []

def get_proxy(proxies):
    """Retrieve a random proxy"""
    if not proxies:
        return None
    proxy_url = random.choice(proxies)
    return {"http": proxy_url, "https": proxy_url}

def create_headers(auth_token=None):
    import uuid
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "client-language": "en",
        "Connection": "keep-alive",
        "Content-Type": "text/plain;charset=UTF-8",
        "Host": "api.gamee.com",
        "Origin": "https://azuki.gamee.com",
        "Referer": "https://azuki.gamee.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-bot-header": "azuki",
        "x-install-uuid": str(uuid.uuid4())
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    return headers

def login(init_data, proxies=None):
    url = "https://api.gamee.com/"
    headers = create_headers()
    proxy = get_proxy(proxies)
    
    payload = [
        {"jsonrpc":"2.0","id":"app.telegram.get","method":"app.telegram.get","params":{}},
        {"jsonrpc":"2.0","id":"user.authentication.loginUsingTelegram",
         "method":"user.authentication.loginUsingTelegram","params":{"initData":init_data}}
    ]
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 1:
            if "result" in data[1] and "tokens" in data[1]["result"]:
                token = data[1]["result"]["tokens"]["authenticate"]
                user = data[1]["result"]["user"]
                nickname = user.get("personal", {}).get("nickname", "Unknown")
                return token, nickname
        
        return None, None
    except Exception as e:
        print(Fore.RED + f"Error saat login: {str(e)}")
        return None, None

def get_daily_checkin_info(token, proxies=None):
    url = "https://api.gamee.com/"
    headers = create_headers(token)
    proxy = get_proxy(proxies)
    
    payload = [
        {"jsonrpc":"2.0","id":"dailyCheckin.getInformation",
         "method":"dailyCheckin.getInformation","params":{}}
    ]
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            result = data[0].get("result", {})
            claimed = result.get("claimedToday", False)
            streak = result.get("streak", 0)
            return claimed, streak
        
        return None, None
    except Exception as e:
        print(Fore.RED + f"Error mendapatkan info checkin: {str(e)}")
        return None, None

def claim_daily_checkin(token, proxies=None):
    url = "https://api.gamee.com/"
    headers = create_headers(token)
    proxy = get_proxy(proxies)
    
    payload = [
        {"jsonrpc":"2.0","id":"dailyCheckin.claim","method":"dailyCheckin.claim","params":{}},
        {"jsonrpc":"2.0","id":"dailyCheckin.getInformation",
         "method":"dailyCheckin.getInformation","params":{}}
    ]
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            result = data[0].get("result", {})
            rewards = result.get("rewards", [])
            
            reward_text = []
            for reward in rewards:
                name = reward.get("currency", {}).get("name", "Unknown")
                amount = reward.get("amountMicroToken", 0) / 1000000
                reward_text.append(f"{name}: {amount:.0f}")
            
            return True, ", ".join(reward_text) if reward_text else "Tidak ada reward"
        
        return False, "Gagal claim"
    except Exception as e:
        print(Fore.RED + f"Error saat claim checkin: {str(e)}")
        return False, str(e)

def get_assets(token, proxies=None):
    url = "https://api.gamee.com/"
    headers = create_headers(token)
    proxy = get_proxy(proxies)
    
    payload = {"jsonrpc":"2.0","id":"user.getAssets","method":"user.getAssets","params":{}}
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        assets = {}
        if "result" in data and "virtualTokens" in data["result"]:
            for token_data in data["result"]["virtualTokens"]:
                ticker = token_data.get("currency", {}).get("ticker", "")
                amount = token_data.get("amountMicroToken", 0) / 1000000
                assets[ticker] = amount
        
        return assets
    except Exception as e:
        print(Fore.RED + f"Error mendapatkan assets: {str(e)}")
        return {}



def countdown(seconds):
    for remaining in range(seconds, 0, -1):
        sys.stdout.write(f"\r{Fore.CYAN}Menunggu {remaining} detik sebelum memproses akun berikutnya...")
        sys.stdout.flush()
        time.sleep(1)
    print()

def countdown_timer(end_time):
    while True:
        now = datetime.now()
        remaining = end_time - now
        
        if remaining.total_seconds() <= 0:
            break
        
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        sys.stdout.write(f"\r{Fore.YELLOW}Hitung mundur: {hours:02d}:{minutes:02d}:{seconds:02d}")
        sys.stdout.flush()
        time.sleep(1)
    
    print()

def process_account(init_data, account_num, total_accounts, proxies=None):
    print(Fore.CYAN + "=" * 60)
    print(Fore.WHITE + f"Memproses Akun {account_num}/{total_accounts}")
    print(Fore.CYAN + "=" * 60)
    
    # Login
    print(Fore.YELLOW + "Login ke akun...")
    token, nickname = login(init_data, proxies)
    
    if not token:
        print(Fore.RED + "Gagal login! Lanjut ke akun berikutnya.")
        return
    
    print(Fore.GREEN + f"Login berhasil! Nickname: {nickname}")
    
    # Check daily checkin
    print(Fore.YELLOW + "\nMengecek status daily checkin...")
    claimed, streak = get_daily_checkin_info(token, proxies)
    
    if claimed is None:
        print(Fore.RED + "Gagal mendapatkan info checkin!")
    elif claimed:
        print(Fore.YELLOW + f"Daily checkin sudah diklaim hari ini. Streak: {streak}")
    else:
        print(Fore.GREEN + f"Belum checkin hari ini. Mencoba claim... Streak: {streak}")
        success, reward_text = claim_daily_checkin(token, proxies)
        
        if success:
            print(Fore.GREEN + f"Daily checkin berhasil diklaim! Reward: {reward_text}")
        else:
            print(Fore.RED + f"Gagal claim daily checkin: {reward_text}")
    
    # Get final assets
    print(Fore.YELLOW + "\nMendapatkan total aset...")
    assets = get_assets(token, proxies)
    
    if assets:
        print(Fore.GREEN + "Total Aset:")
        for ticker, amount in assets.items():
            if amount > 0:
                print(Fore.GREEN + f"  {ticker}: {amount:.0f}")
    else:
        print(Fore.RED + "Gagal mendapatkan informasi aset!")
    
    print()

def main():
    print_welcome_message()
    
    # Load proxies
    proxies = load_proxies()
    
    while True:
        accounts = load_accounts()
        
        if not accounts:
            print(Fore.RED + "Tidak ada akun yang ditemukan di data.txt!")
            break
        
        total_accounts = len(accounts)
        print(Fore.GREEN + f"Total akun ditemukan: {total_accounts}\n")
        
        for idx, init_data in enumerate(accounts, 1):
            try:
                process_account(init_data, idx, total_accounts, proxies)
                
                if idx < total_accounts:
                    countdown(5)
                    
            except Exception as e:
                print(Fore.RED + f"Error tidak terduga pada akun {idx}: {str(e)}")
                print(Fore.YELLOW + "Melanjutkan ke akun berikutnya...")
                continue
        
        print(Fore.GREEN + "=" * 60)
        print(Fore.GREEN + "Semua akun telah diproses!")
        print(Fore.GREEN + "=" * 60)
        
        # Countdown 24 jam
        next_run = datetime.now() + timedelta(days=1)
        print(Fore.CYAN + f"\nProses berikutnya akan dimulai pada: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        countdown_timer(next_run)
        
        print(Fore.GREEN + "\nMemulai siklus baru...\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nProgram dihentikan oleh user.")
        sys.exit(0)
