import requests
import json
import time
import random
import uuid
import hashlib
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import sys
import os

init(autoreset=True)

# ============================================================
# KONFIGURASI SAFETY & LEADERBOARD - WEEKLY CYCLE
# ============================================================

def load_safety_config():
    """Load konfigurasi dari file aturgame.txt"""
    try:
        with open('aturgame.txt', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(Fore.GREEN + "✓ Konfigurasi berhasil dimuat dari aturgame.txt")
        return config
    except FileNotFoundError:
        print(Fore.RED + "❌ File aturgame.txt tidak ditemukan!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(Fore.RED + f"❌ Error parsing aturgame.txt: {e}")
        sys.exit(1)

SAFETY_CONFIG = load_safety_config()

def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop Azuki")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop\n")
    print(Fore.CYAN + Style.BRIGHT + f"Target Leaderboard: {SAFETY_CONFIG['target_rank'].upper()}")
    print(Fore.CYAN + Style.BRIGHT + "Strategi: Distribusi mingguan (Weekly Reset)\n")

def animated_countdown(seconds, message="Menunggu"):
    """Animasi countdown sederhana"""
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        timer = f"{mins:02d}:{secs:02d}"
        print(f"\r{Fore.YELLOW}  ⏳ {message}: {timer}", end='')
        sys.stdout.flush()
        time.sleep(1)
    print(f"\r{Fore.GREEN}  ✓ {message}: Selesai!{' ' * 20}")

def animated_timer_countdown(target_time, message="Menunggu"):
    """Countdown sampai waktu tertentu dengan animasi"""
    while True:
        now = datetime.now()
        remaining = (target_time - now).total_seconds()
        
        if remaining <= 0:
            print(f"\r{Fore.GREEN}  ✓ {message}: Waktu tercapai!{' ' * 30}")
            break
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        
        timer = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        print(f"\r{Fore.YELLOW}  ⏳ {message}: {timer}", end='')
        sys.stdout.flush()
        time.sleep(1)

def load_accounts():
    try:
        with open('data.txt', 'r') as file:
            accounts = [line.strip() for line in file if line.strip()]
        return accounts
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan!")
        return []

def load_proxies(filename='proxy.txt'):
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
            print(Fore.BLUE + f"✓ Berhasil memuat {len(proxies)} proxy")
        return proxies
    except FileNotFoundError:
        print(Fore.YELLOW + "File proxy.txt tidak ditemukan. Melanjutkan tanpa proxy.")
        return []

def get_proxy(proxies):
    if not proxies:
        return None
    proxy_url = random.choice(proxies)
    return {"http": proxy_url, "https": proxy_url}

def create_headers(auth_token=None, install_uuid=None):
    if not install_uuid:
        install_uuid = str(uuid.uuid4())
    
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
        "x-install-uuid": install_uuid
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    return headers

def login(init_data, proxies=None):
    url = "https://api.gamee.com/"
    install_uuid = str(uuid.uuid4())
    headers = create_headers(install_uuid=install_uuid)
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
                return token, nickname, install_uuid
        
        return None, None, None
    except Exception as e:
        print(Fore.RED + f"Error saat login: {str(e)}")
        return None, None, None

def get_game_info(token, install_uuid, proxies=None):
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    payload = {"jsonrpc":"2.0","id":"telegram.azuki.getGame","method":"telegram.azuki.getGame","params":{}}
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            game = data["result"].get("game", {})
            daily_rewards = data["result"].get("dailyRewards", {})
            release_number = game.get("release", {}).get("number", 8)
            
            return game, daily_rewards, release_number
        
        return None, None, 8
    except Exception as e:
        print(Fore.RED + f"Error mendapatkan info game: {str(e)}")
        return None, None, 8

def generate_checksum(score, play_time, game_state_data, game_uuid):
    SECRET_KEY = "crmjbjm3lczhlgnek9uaxz2l9svlfjw14npauhen"
    raw_string = f"{score}:{play_time}::{game_state_data}:{game_uuid}:{SECRET_KEY}"
    checksum = hashlib.md5(raw_string.encode()).hexdigest()
    return checksum

def get_daily_xp_target(day_of_week, target_rank):
    """
    Distribusi XP berdasarkan hari dalam seminggu
    Lebih natural: main lebih banyak di weekend
    """
    target_weekly = SAFETY_CONFIG["target_xp_weekly"][target_rank]
    
    if SAFETY_CONFIG["daily_distribution"] == "uniform":
        # Uniform: sama setiap hari
        return target_weekly / 7
    else:
        # Variable: lebih banyak di weekend
        # Mon-Fri: 12% each day (60% total)
        # Sat-Sun: 20% each day (40% total)
        if day_of_week < 5:  # Weekday (0=Monday, 4=Friday)
            return target_weekly * 0.12
        else:  # Weekend
            return target_weekly * 0.20

def is_in_play_window():
    """Check apakah sekarang dalam window waktu main"""
    now = datetime.now()
    current_hour = now.hour
    
    for start, end in SAFETY_CONFIG["play_time_windows"]:
        if start <= current_hour < end:
            return True
    return False

def calculate_next_play_time():
    """Hitung waktu main berikutnya (dalam window)"""
    now = datetime.now()
    current_hour = now.hour
    
    # Cari window berikutnya
    for start, end in SAFETY_CONFIG["play_time_windows"]:
        if current_hour < start:
            # Window hari ini
            target = now.replace(hour=start, minute=random.randint(0, 59), second=0)
            return target
    
    # Kalau sudah lewat semua window hari ini, ambil window pertama besok
    tomorrow = now + timedelta(days=1)
    first_window = SAFETY_CONFIG["play_time_windows"][0]
    target = tomorrow.replace(hour=first_window[0], minute=random.randint(0, 59), second=0)
    return target

def play_game_optimized(token, install_uuid, release_number, target_xp=None, 
                       coin_limit_reached=False, proxies=None):
    """
    Main game dengan optimization
    Coin limit HANYA dicek dari response server, bukan dari current_coins
    """
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    # Fail simulation (5%)
    if random.random() < SAFETY_CONFIG["fail_rate"]:
        print(Fore.YELLOW + "  ⚠ Simulasi network timeout")
        time.sleep(random.uniform(2, 5))
        return False, "Network timeout", 0, 0, False
    
    game_uuid = str(uuid.uuid4())
    gameplay_id = random.randint(1, 5)
    
    skill_level = random.uniform(0.95, 1.15)
    
    if target_xp:
        estimated_playtime = int(target_xp / 1.8)
        playtime = max(30, min(134, estimated_playtime))
    else:
        if random.random() < 0.7:
            playtime = random.randint(50, 90)
        elif random.random() < 0.85:
            playtime = random.randint(30, 49)
        else:
            playtime = random.randint(91, 134)
    
    playtime = int(playtime * random.uniform(0.95, 1.05))
    playtime = max(30, min(134, playtime))
    
    score = random.randint(5, 25) if random.random() < 0.03 else 0
    
    # LOGIKA COINS: 
    # Jika coin_limit_reached = True (dari error sebelumnya) -> coins = 0
    # Jika tidak -> coins NORMAL (biarkan server yang tolak kalau over limit)
    
    if coin_limit_reached:
        coins_earned = 0
    else:
        # Hitung coins NORMAL - biarkan server yang cek limit!
        coins_earned = int(playtime * random.uniform(0.85, 1.15) * skill_level)
        coins_earned = max(25, min(150, coins_earned))
    
    # XP calculation
    xp_rate = random.uniform(1.6, 2.2)
    xp_base = playtime * xp_rate * skill_level
    xp_earned = int(xp_base)
    
    if playtime < 50:
        xp_earned = max(50, min(110, xp_earned))
    elif playtime < 90:
        xp_earned = max(100, min(200, xp_earned))
    else:
        xp_earned = max(180, min(300, xp_earned))
    
    used_lives = int(playtime * random.uniform(0.92, 1.08))
    box_earned = 1 if random.random() < 0.015 else 0
    
    # Animasi bermain
    print(Fore.CYAN + f"  → Memulai game (target: {playtime}s)...")
    time.sleep(random.uniform(1.5, 3.5))
    
    print(Fore.CYAN + f"  → Bermain... ", end='')
    sys.stdout.flush()
    
    simulated_time = playtime / 6
    steps = 20
    
    for i in range(steps):
        filled = int((i + 1) / steps * 30)
        bar = '▰' * filled + '▱' * (30 - filled)
        percentage = int((i + 1) / steps * 100)
        
        sys.stdout.write(f"\r  {Fore.CYAN}→ Bermain... [{Fore.YELLOW}{bar}{Fore.CYAN}] {percentage}%")
        sys.stdout.flush()
        
        time.sleep(simulated_time / steps)
    
    print(f"\r  {Fore.GREEN}→ Bermain... [{'▰' * 30}] 100% - Selesai!{' ' * 10}")
    
    time.sleep(random.uniform(1, 2.5))
    
    now = datetime.now()
    created_time = now.strftime("%Y-%m-%dT%H:%M:%S+07:00")
    
    game_state = {
        "reward": {
            "AZUKICOINS": coins_earned,
            "AZUKIBOXMINI": box_earned,
            "AZUKIXP": xp_earned
        },
        "usedLives": used_lives
    }
    
    game_state_str = json.dumps(game_state, separators=(',', ':'))
    checksum = generate_checksum(score, playtime, game_state_str, game_uuid)
    
    gameplay_data = {
        "gameId": 307,
        "score": score,
        "playTime": playtime,
        "releaseNumber": release_number,
        "createdTime": created_time,
        "metadata": {"gameplayId": gameplay_id},
        "gameStateData": game_state_str,
        "replayData": None,
        "replayVariant": None,
        "replayDataChecksum": None,
        "uuid": game_uuid,
        "checksum": checksum
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": "game.saveTelegramMainGameplay",
        "method": "game.saveTelegramMainGameplay",
        "params": {"gameplayData": gameplay_data}
    }
    
    print(Fore.CYAN + f"  → Menyimpan...", end='')
    sys.stdout.flush()
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            # Sukses - tampilkan hasil
            if coin_limit_reached:
                coin_text = "XP Only (Daily Limit)"
            else:
                coin_text = f"+{coins_earned} Coins"
            
            print(Fore.GREEN + f" ✓ +{xp_earned} XP | {coin_text}")
            return True, "Berhasil", xp_earned, coins_earned, False
        
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown")
            
            # CEK: Jika error "Daily reward limit exceeded" dari SERVER
            if "daily reward limit" in error_msg.lower() or "limit exceeded" in error_msg.lower():
                print(Fore.YELLOW + f" ⚠ {error_msg}")
                print(Fore.YELLOW + f"  📢 Switching to XP Only mode...")
                return False, error_msg, 0, 0, True  # Flag coin_limit_reached = True
            
            print(Fore.RED + f" ✗ {error_msg}")
            return False, error_msg, 0, 0, False
            
    except Exception as e:
        print(Fore.RED + f" ✗ {str(e)[:40]}")
        return False, str(e), 0, 0, False
    
def get_assets(token, install_uuid, proxies=None):
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
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
        return {}

def get_user_assets_detailed(token, install_uuid, proxies=None):
    """Mengambil data assets user untuk cek box"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    payload = [
        {
            "jsonrpc": "2.0",
            "id": "user.getAssets",
            "method": "user.getAssets",
            "params": {}
        }
    ]

    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        decoded = response.json()
        
        if decoded and isinstance(decoded, list):
            assets = decoded[0].get("result", {}).get("assets", [])
            
            # Cari Mini Box (currencyId: 44)
            for asset in assets:
                currency = asset.get("currency", {})
                if currency.get("ticker") == "AZUKIBOXMINI":
                    box_amount = asset.get("amountMicroToken", 0) // 1000000
                    return box_amount
            
            return 0
    except Exception as e:
        print(Fore.RED + f"  ✗ Error getting assets: {e}")
        return 0

def open_box(token, install_uuid, proxies=None):
    """Membuka box sampai gagal/habis"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    opened_count = 0
    all_rewards = []
    
    print(Fore.MAGENTA + "  🎁 Membuka box...")
    
    # Loop terus sampai gagal
    while True:
        payload = {
            "jsonrpc": "2.0",
            "id": "avatar.openPack",
            "method": "avatar.openPack",
            "params": {"currencyId": 44}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
            response.raise_for_status()
            decoded = response.json()
            
            if decoded.get("result"):
                opened_count += 1
                avatar_parts = decoded["result"].get("avatarParts", [])
                
                print(Fore.GREEN + f"  ✓ Box {opened_count} dibuka!")
                
                for part in avatar_parts:
                    name = part.get("name", "Unknown")
                    rarity = part.get("rarity", {}).get("name", "Unknown")
                    score = part.get("score", 0)
                    
                    print(Fore.CYAN + f"    • {name} ({rarity}) - Score: {score}")
                    
                    all_rewards.append({
                        "name": name,
                        "rarity": rarity,
                        "part_id": part.get("id"),
                        "score": score
                    })
                
                time.sleep(1)
            else:
                # Gagal = tidak ada box lagi
                error_msg = decoded.get("error", {}).get("message", "No more boxes")
                print(Fore.YELLOW + f"  ⚠ Berhenti: {error_msg}")
                break
                
        except Exception as e:
            print(Fore.RED + f"  ✗ Error membuka box: {e}")
            break

    if opened_count > 0:
        print(Fore.GREEN + f"  ✓ Total box dibuka: {opened_count}")
    else:
        print(Fore.YELLOW + "  ℹ Tidak ada box untuk dibuka")
    
    return all_rewards

def get_inventory(token, install_uuid, proxies=None):
    """Mengambil SEMUA inventory avatar parts dengan pagination"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    all_parts = []
    offset = 0
    limit = 100
    
    while True:
        payload = [
            {
                "jsonrpc": "2.0",
                "id": "avatar.inventory.getAll",
                "method": "avatar.inventory.getAll",
                "params": {
                    "avatarSlug": "azuki",
                    "avatarTraitTypeId": None,
                    "pagination": {"offset": offset, "limit": limit}
                }
            }
        ]

        try:
            response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
            response.raise_for_status()
            decoded = response.json()
            
            if decoded and isinstance(decoded, list):
                avatar_parts = decoded[0].get("result", {}).get("avatarParts", [])
                
                if not avatar_parts:
                    break
                
                all_parts.extend(avatar_parts)
                
                # Jika hasil kurang dari limit, berarti sudah habis
                if len(avatar_parts) < limit:
                    break
                
                offset += limit
                time.sleep(0.5)
        except Exception as e:
            print(Fore.RED + f"  ✗ Error getting inventory: {e}")
            break
    
    return all_parts

def equip_best_items(token, install_uuid, proxies=None):
    """Equip item dengan score tertinggi dari SELURUH inventory"""
    inventory = get_inventory(token, install_uuid, proxies)
    
    if not inventory:
        print(Fore.YELLOW + "  ℹ Tidak ada item untuk di-equip")
        return

    print(Fore.CYAN + f"  📦 Total item di inventory: {len(inventory)}")
    
    # Group by trait type dan ambil yang score tertinggi
    best_items = {}
    for item in inventory:
        trait_type_id = item.get("avatarTraitType", {}).get("id")
        trait_type_name = item.get("avatarTraitType", {}).get("name")
        score = item.get("score", 0)
        
        if trait_type_id not in best_items or score > best_items[trait_type_id]["score"]:
            best_items[trait_type_id] = {
                "id": item.get("id"),
                "name": item.get("name"),
                "score": score,
                "type": trait_type_name,
                "rarity": item.get("rarity", {}).get("name", "Unknown")
            }

    print(Fore.MAGENTA + f"  ⚙️ Equip {len(best_items)} item terbaik...")
    
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    equipped_count = 0
    for trait_id, item_data in best_items.items():
        payload = {
            "jsonrpc": "2.0",
            "id": "avatar.equip",
            "method": "avatar.equip",
            "params": {"avatarPartId": item_data["id"]}
        }

        try:
            response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
            response.raise_for_status()
            decoded = response.json()
            
            if decoded.get("result"):
                equipped_count += 1
                print(Fore.GREEN + f"  ✓ {item_data['type']}: {item_data['name']} ({item_data['rarity']}) - Score: {item_data['score']}")
                time.sleep(0.5)
                
        except Exception as e:
            pass

    print(Fore.GREEN + f"  ✓ Berhasil equip {equipped_count}/{len(best_items)} item")


def get_lucky_boxes_info(token, install_uuid, proxies=None):
    """Ambil informasi Lucky Boxes draw"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    payload = [{
        "jsonrpc": "2.0",
        "id": "draw.getAll",
        "method": "draw.getAll",
        "params": {"pagination": {"offset": 0, "limit": 100}}
    }]
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            result = data[0]
            if "result" in result and "draws" in result["result"]:
                draws = result["result"]["draws"]
                for draw in draws:
                    if draw.get("name") == "Lucky Boxes":
                        return draw
        return None
    except Exception as e:
        print(Fore.RED + f"  ✗ Error getting Lucky Boxes info: {e}")
        return None

def submit_lucky_boxes_ticket(token, install_uuid, draw_id, amount=1, proxies=None):
    """Submit tiket ke Lucky Boxes"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    payload = {
        "jsonrpc": "2.0",
        "id": "draw.enter",
        "method": "draw.enter",
        "params": {
            "drawId": draw_id,
            "enterAmountMicroToken": amount * 1000000
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and "draw" in data["result"]:
            draw_result = data["result"]["draw"]
            my_input = draw_result.get("myInputVirtualToken", {})
            total_submitted = my_input.get("amountMicroToken", 0) // 1000000
            
            return {
                "success": True,
                "total_tickets": total_submitted,
                "participants": draw_result.get("participantsCount", 0)
            }
        elif "error" in data:
            error = data["error"]
            return {
                "success": False,
                "error": error.get("message", "Unknown error")
            }
        
        return {"success": False, "error": "Unknown response"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def process_lucky_boxes(token, install_uuid, proxies=None):
    """Process Lucky Boxes - submit tiket sesuai config (tanpa cek tiket terlebih dahulu)"""
    # Cek apakah fitur enabled di config
    lucky_boxes_config = SAFETY_CONFIG.get("lucky_boxes", {})
    
    if not lucky_boxes_config.get("enabled", False):
        return
    
    print(Fore.MAGENTA + "  🎰 Mengecek Lucky Boxes...")
    
    # Ambil info draw
    draw_info = get_lucky_boxes_info(token, install_uuid, proxies)
    
    if not draw_info:
        print(Fore.YELLOW + "  ℹ Lucky Boxes tidak tersedia saat ini")
        return
    
    draw_id = draw_info["id"]
    entry_fee = draw_info["entryFeeVirtualToken"]["amountMicroToken"] // 1000000
    participants = draw_info.get("participantsCount", 0)
    
    print(Fore.CYAN + f"  📦 {draw_info['name']} (ID: {draw_id})")
    print(Fore.CYAN + f"  💰 Entry Fee: {entry_fee} tiket")
    print(Fore.CYAN + f"  📊 Participants: {participants}")
    
    # Tentukan mode submit
    mode = lucky_boxes_config.get("submit_mode", "single")
    
    if mode == "all":
        # Mode ALL: Submit terus sampai server bilang gabisa
        print(Fore.YELLOW + f"  → Mode: ALL - Submit sampai gagal...")
        
        success_count = 0
        attempt = 0
        
        while True:
            attempt += 1
            print(Fore.CYAN + f"  → Submit #{attempt}...", end='')
            sys.stdout.flush()
            
            result = submit_lucky_boxes_ticket(token, install_uuid, draw_id, 1, proxies)
            
            if result["success"]:
                success_count += 1
                print(Fore.GREEN + f" ✓ Total: {result['total_tickets']} | Participants: {result['participants']}")
                
                # Delay antar submit
                delay = random.uniform(2, 5)
                time.sleep(delay)
            else:
                # Gagal = tiket habis atau error
                print(Fore.YELLOW + f" ⚠ {result['error']}")
                break
        
        if success_count > 0:
            print(Fore.GREEN + f"  ✓ Berhasil submit {success_count}x tiket ke Lucky Boxes")
        else:
            print(Fore.YELLOW + f"  ℹ Tidak ada tiket untuk disubmit")
    
    else:
        # Mode SINGLE: Submit 1 kali saja
        print(Fore.YELLOW + f"  → Mode: SINGLE - Submit 1x tiket...")
        
        print(Fore.CYAN + f"  → Submit...", end='')
        sys.stdout.flush()
        
        result = submit_lucky_boxes_ticket(token, install_uuid, draw_id, 1, proxies)
        
        if result["success"]:
            print(Fore.GREEN + f" ✓ Total: {result['total_tickets']} | Participants: {result['participants']}")
            print(Fore.GREEN + f"  ✓ Berhasil submit 1x tiket ke Lucky Boxes")
        else:
            print(Fore.YELLOW + f" ⚠ {result['error']}")
            print(Fore.YELLOW + f"  ℹ Tidak ada tiket untuk disubmit")

def claim_journey(token, install_uuid, proxies=None):
    """Claim journey milestone yang tersedia"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
    proxy = get_proxy(proxies)
    
    pre_payload = [
        {
            "jsonrpc": "2.0",
            "id": "rewardedProgress.getAll",
            "method": "rewardedProgress.getAll",
            "params": {"pagination": {"offset": 0, "limit": 100}},
        },
    ]

    try:
        response = requests.post(url, headers=headers, json=pre_payload, proxies=proxy, timeout=30)
        response.raise_for_status()
        pre_decoded = response.json()
    except Exception as e:
        print(Fore.RED + f"  ✗ Error mendapat journey data: {e}")
        return 0

    try:
        journeys = pre_decoded[0]["result"]["rewardedProgress"]
        journey = journeys[0] if journeys else {}
        milestones = journey.get("milestones", [])
        
        claimables = [
            m for m in milestones if m.get("reward", {}).get("claimAvailable") is True
        ]
        
        if not claimables:
            print(Fore.YELLOW + "  ℹ Tidak ada milestone untuk di-claim")
            return 0
        
        print(Fore.MAGENTA + f"  🗺️ Claiming {len(claimables)} milestone...")
        
    except Exception as e:
        print(Fore.RED + f"  ✗ Error parsing journey: {e}")
        return 0

    claimed_count = 0
    for m in claimables:
        mid = m["id"]

        claim_payload = {
            "jsonrpc": "2.0",
            "id": "rewardedProgress.claim",
            "method": "rewardedProgress.claim",
            "params": {"milestoneId": mid, "premium": False},
        }

        try:
            response = requests.post(url, headers=headers, json=claim_payload, proxies=proxy, timeout=30)
            response.raise_for_status()
            decoded_claim = response.json()
            
            if decoded_claim.get("result"):
                claimed_count += 1
            
            time.sleep(0.5)
        except Exception as e:
            pass

    print(Fore.GREEN + f"  ✓ Berhasil claim {claimed_count} milestone")
    return claimed_count

def get_daily_checkin_info(token, install_uuid, proxies=None):
    """Mendapatkan informasi daily checkin"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
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
        print(Fore.RED + f"  ✗ Error mendapatkan info checkin: {str(e)}")
        return None, None

def claim_daily_checkin(token, install_uuid, proxies=None):
    """Claim daily checkin"""
    url = "https://api.gamee.com/"
    headers = create_headers(token, install_uuid)
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
            
            return True, ", ".join(reward_text) if reward_text else "No reward"
        
        return False, "Gagal claim"
    except Exception as e:
        print(Fore.RED + f"  ✗ Error saat claim checkin: {str(e)}")
        return False, str(e)

def process_account_session(init_data, account_num, proxies=None):
    """Process 1 session untuk 1 akun dengan fitur lengkap"""
    
    # Login
    token, nickname, install_uuid = login(init_data, proxies)
    
    if not token:
        print(Fore.RED + f"  ✗ Gagal login untuk akun #{account_num}")
        return 0
    
    print(Fore.GREEN + f"  ✓ Login berhasil: {nickname}")
    
    time.sleep(random.uniform(1.5, 3))
    
    # === DAILY CHECKIN ===
    print(Fore.YELLOW + "  → Mengecek daily checkin...")
    claimed, streak = get_daily_checkin_info(token, install_uuid, proxies)
    
    if claimed is None:
        print(Fore.RED + "  ✗ Gagal mendapatkan info checkin")
    elif claimed:
        print(Fore.CYAN + f"  ℹ Daily checkin sudah diklaim hari ini (Streak: {streak})")
    else:
        print(Fore.YELLOW + f"  → Belum checkin hari ini (Streak: {streak}). Claiming...")
        time.sleep(random.uniform(1, 2))
        
        success, reward_text = claim_daily_checkin(token, install_uuid, proxies)
        
        if success:
            print(Fore.GREEN + f"  ✓ Daily checkin berhasil! Reward: {reward_text}")
        else:
            print(Fore.RED + f"  ✗ Gagal claim: {reward_text}")
    
    time.sleep(random.uniform(1, 2))
    
    # === OPEN BOX ===
    print(Fore.YELLOW + "  → Mengecek box...")
    rewards = open_box(token, install_uuid, proxies)
    
    if rewards:
        time.sleep(random.uniform(1, 2))
        print(Fore.YELLOW + "  → Equipping item terbaik...")
        equip_best_items(token, install_uuid, proxies)
    
    time.sleep(random.uniform(1, 2))
    
    # === CLAIM JOURNEY ===
    print(Fore.YELLOW + "  → Mengecek journey...")
    claim_journey(token, install_uuid, proxies)
    
    time.sleep(random.uniform(1, 2))
    
    # === LUCKY BOXES (FITUR BARU) ===
    process_lucky_boxes(token, install_uuid, proxies)
    
    time.sleep(random.uniform(1, 2))
    
    # Get game info
    game, daily_rewards, release_number = get_game_info(token, install_uuid, proxies)
    
    if not game:
        print(Fore.RED + "  ✗ Gagal mendapatkan info game")
        return 0
    
    # Get current assets
    assets = get_assets(token, install_uuid, proxies)
    current_xp = assets.get("AZUKIXP", 0)
    current_coins = assets.get("AZUKICOINS", 0)
    
    print(Fore.CYAN + f"  💎 XP: {current_xp:.0f} | 🪙 Coins: {current_coins:.0f}")
    
    # Tentukan berapa game di session ini
    now = datetime.now()
    is_weekend = now.weekday() >= 5
    
    if is_weekend:
        games_in_session = random.randint(
            SAFETY_CONFIG["min_games_per_session"],
            SAFETY_CONFIG["max_games_per_session"]
        )
    else:
        games_in_session = random.randint(
            SAFETY_CONFIG["min_games_per_session"],
            SAFETY_CONFIG["max_games_per_session"] - 1
        )
    
    print(Fore.YELLOW + f"  🎮 Session: {games_in_session} game")
    
    session_xp = 0
    session_coins = 0
    coin_limit_reached = False
    
    for game_num in range(1, games_in_session + 1):
        print(Fore.CYAN + f"\n  [Game {game_num}/{games_in_session}]")
        
        target_xp = random.randint(
            SAFETY_CONFIG["xp_per_game_min"],
            SAFETY_CONFIG["xp_per_game_max"]
        )
        
        success, msg, xp, coins, limit_flag = play_game_optimized(
            token, install_uuid, release_number,
            target_xp, coin_limit_reached, proxies
        )
        
        if success:
            session_xp += xp
            session_coins += coins
        
        if limit_flag:
            coin_limit_reached = True
            print(Fore.YELLOW + f"  📢 Mode XP aktif untuk game selanjutnya")
        
        if game_num < games_in_session:
            delay = random.randint(
                SAFETY_CONFIG["min_delay_between_games"],
                SAFETY_CONFIG["max_delay_between_games"]
            )
            
            animated_countdown(delay, f"Cooldown game")
            print()
    
    coin_status = f"+{session_coins} Coins" if session_coins > 0 else "(XP Mode)"
    print(Fore.GREEN + f"\n  ✓ Session selesai! +{session_xp} XP {coin_status}")
    return session_xp

def print_box_line(text, width=68, color=Fore.YELLOW):
    """Helper untuk print baris dalam box dengan padding otomatis"""
    padding = " " * (width - len(text))
    print(color + "║" + text + padding + "║")

def main():
    print_welcome_message()
    
    target_rank = SAFETY_CONFIG["target_rank"]
    target_weekly = SAFETY_CONFIG["target_xp_weekly"][target_rank]
    
    box_width = 68
    
    print(Fore.CYAN + "╔" + "═" * box_width + "╗")
    print_box_line(" KONFIGURASI:", box_width)
    print_box_line(f"  Target Rank: {target_rank.upper()}", box_width)
    print_box_line(f"  Target XP/minggu: {target_weekly:,}", box_width)
    print_box_line(f"  Game per session: {SAFETY_CONFIG['min_games_per_session']}-{SAFETY_CONFIG['max_games_per_session']}", box_width)
    print(Fore.CYAN + "╚" + "═" * box_width + "╝\n")
    
    proxies = load_proxies()
    
    while True:
        accounts = load_accounts()
        
        if not accounts:
            print(Fore.RED + "Tidak ada akun yang ditemukan!")
            break
        
        print(Fore.GREEN + f"Total akun ditemukan: {len(accounts)}\n")
        
        # Check play window
        if not is_in_play_window():
            next_time = calculate_next_play_time()
            print(Fore.YELLOW + f"Di luar waktu main. Waktu main berikutnya: {next_time.strftime('%H:%M')}\n")
            
            animated_timer_countdown(next_time, "Menunggu waktu main")
            print()
        
        # Process semua akun (1 session per akun)
        for idx, init_data in enumerate(accounts, 1):
            print(Fore.CYAN + "\n" + "═" * 70)
            print(Fore.WHITE + f"Akun {idx}/{len(accounts)}")
            print(Fore.CYAN + "═" * 70)
            
            try:
                session_xp = process_account_session(init_data, idx, proxies)
                
                if idx < len(accounts):
                    delay = random.randint(15, 45)
                    print(Fore.CYAN + f"\n→ Delay sebelum akun berikutnya...")
                    animated_countdown(delay, "Menunggu akun berikutnya")
                    print()
                    
            except Exception as e:
                print(Fore.RED + f"Error: {str(e)}")
                continue
        
        # Hitung next session
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        
        if is_weekend:
            sessions_today = SAFETY_CONFIG["sessions_per_day"]["weekend"]
        else:
            sessions_today = SAFETY_CONFIG["sessions_per_day"]["weekday"]
        
        # Random delay untuk session berikutnya
        hours_delay = random.uniform(
            SAFETY_CONFIG["min_delay_between_sessions"],
            SAFETY_CONFIG["max_delay_between_sessions"]
        )
        
        next_session = now + timedelta(hours=hours_delay)
        
        print(Fore.GREEN + "\n" + "═" * 70)
        print(Fore.GREEN + "Session selesai!")
        print(Fore.CYAN + f"Session berikutnya: {next_session.strftime('%Y-%m-%d %H:%M:%S')}")
        print(Fore.GREEN + "═" * 70 + "\n")
        
        # Countdown dengan animasi
        animated_timer_countdown(next_session, "Session berikutnya dalam")
        
        print(Fore.GREEN + "\n\nMemulai session baru...\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nProgram dihentikan oleh user.")
        sys.exit(0)
