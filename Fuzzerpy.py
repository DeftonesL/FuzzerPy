"""
FuzzerPy - Advanced Async Directory Scanner & Intelligent Wordlist Generator
Copyright (c) 2025 Saleh Al-Otaibi. All rights reserved.
"""

import aiohttp
import asyncio
import argparse
import sys
import random
import itertools
from datetime import datetime
from urllib.parse import urlparse
from colorama import Fore, Style, init
from tqdm.asyncio import tqdm

# === (Integrity Check) ===
__author__ = "Saleh Al-Otaibi"
__version__ = "3.0.0 (Elite Edition)"
__tool_name__ = "FuzzerPy"

init(autoreset=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

class SmartGenerator:

    def __init__(self, target_url):
        self.target_domain = self.extract_domain_name(target_url)
        

        self.cores = [
            "admin", "administrator", "root", "login", "user", "member", "account",
            "api", "v1", "v2", "beta", "staging", "dev", "developer", "test",
            "prod", "production", "backup", "private", "db", "sql", "data",
            "config", "conf", "settings", "install", "setup", "update", "patch",
            "logs", "cache", "tmp", "temp", "assets", "static", "media", "images",
            "js", "css", "lib", "vendor", "includes", "modules", "plugins",
            "dashboard", "panel", "control", "cpanel", "webmail", "server-status"
        ]
        

        self.actions = ["upload", "download", "view", "edit", "delete", "auth", "register", "search"]
  
        self.modifiers = ["bak", "old", "new", "copy", "temp", "archive", "dist"]
        

        current_year = datetime.now().year
        self.years = [str(y) for y in range(current_year - 5, current_year + 2)] # 5 سنوات ماضية وسنة قادمة
        

        self.separators = ["", "-", "_", "."]

    def extract_domain_name(self, url):

        try:
            domain = urlparse(url).netloc

            name = domain.split('.')
            if 'www' in name: name.remove('www')
            return name[0] 
        except:
            return "site"

    def generate(self):

        wordlist = set()
        
        print(f"{Fore.CYAN}[*] Analyzing target context: {self.target_domain}")

        self.cores.append(self.target_domain)
        
        for word in self.cores:
            wordlist.add(word)

        for core in self.cores:
            for year in self.years:
                wordlist.add(f"{core}{year}")
                wordlist.add(f"{core}_{year}")
                wordlist.add(f"{core}-{year}")

        combinations = itertools.product(self.cores, self.separators, self.modifiers)
        for core, sep, mod in combinations:
            wordlist.add(f"{core}{sep}{mod}")

        for core in self.cores:
            if core != self.target_domain:
                wordlist.add(f"{self.target_domain}_{core}")
                wordlist.add(f"{self.target_domain}-{core}")

        for c1 in ["admin", "api", "test", "dev"]:
            for c2 in ["login", "user", "v1", "db"]:
                wordlist.add(f"{c1}_{c2}")
                wordlist.add(f"{c1}-{c2}")

        return list(wordlist)

class FuzzerPyEngine:
    def __init__(self, target, wordlist_data, extensions, threads, output_file=None):
        self.target = target.rstrip('/')
        self.wordlist_data = wordlist_data
        self.extensions = extensions
        self.semaphore = asyncio.Semaphore(threads)
        self.output_file = output_file
        self.found_urls = []
        
        # حماية الحقوق
        if __author__ != "Saleh Al-Otaibi":
            sys.exit("Integrity Error: Author signature missing.")

    def get_random_agent(self):
        return random.choice(USER_AGENTS)

    def save_result(self, line):
        if self.output_file:
            with open(self.output_file, 'a') as f:
                f.write(line + '\n')

    async def scan_url(self, session, path, pbar):
        url = f"{self.target}/{path}"
        headers = {'User-Agent': self.get_random_agent()}
        
        async with self.semaphore:
            try:
                async with session.get(url, headers=headers, allow_redirects=False, timeout=6) as response:
                    status = response.status
                    msg = ""
                    if status == 200:
                        msg = f"{Fore.GREEN}[200] OK: {url}{Style.RESET_ALL}"
                    elif status == 403:
                        msg = f"{Fore.YELLOW}[403] Forbidden: {url}{Style.RESET_ALL}"
                    elif status in [301, 302]:
                        loc = response.headers.get('Location', 'Unknown')
                        msg = f"{Fore.BLUE}[{status}] Redirect: {url} -> {loc}{Style.RESET_ALL}"
                    
                    if msg:
                        tqdm.write(msg)
                        self.found_urls.append(url)
                        self.save_result(f"[{status}] {url}")

            except Exception:
                pass
            finally:
                pbar.update(1)

    async def run(self):
        self.print_banner()
        
        # تجهيز الكلمات النهائية مع الامتدادات
        final_payloads = []
        print(f"{Fore.CYAN}[*] Processing wordlist & extensions...")
        
        for word in self.wordlist_data:
            final_payloads.append(word) # فحص المجلد
            for ext in self.extensions:
                final_payloads.append(f"{word}.{ext}") # فحص الملف

        total = len(final_payloads)
        print(f"{Fore.WHITE}[*] Total payloads generated: {Fore.GREEN}{total:,} items") # استخدام الفاصلة للآلاف
        print(f"{Fore.WHITE}[*] Threads: {Fore.GREEN}{self.semaphore._value}")
        print("-" * 60)
        
        connector = aiohttp.TCPConnector(limit=None, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            with tqdm(total=total, desc="Scanning", unit="req", ncols=90, 
                      bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]") as pbar:
                
                tasks = []
                for path in final_payloads:
                    tasks.append(self.scan_url(session, path, pbar))
                
                await asyncio.gather(*tasks)

        print("\n" + "=" * 60)
        print(f"{Fore.GREEN}[✔] Scan Finished by {__author__}. Found: {len(self.found_urls)}")

    def print_banner(self):
        print(Fore.RED + r"""
  ______                         _____       
 |  ____|                       |  __ \      
 | |__ _   _ _____________ _ __ | |__) |   _ 
 |  __| | | |_  /_  /_  / | '__||  ___/ | | |
 | |  | |_| |/ / / / / /| | |   | |   | |_| |
 |_|   \__,_/___/___/___|_|_|   |_|    \__, |
                                        __/ |  V 3.0
                                       |___/ 
        """ + Style.RESET_ALL)
        print(f"{Fore.WHITE}Author: {Fore.RED}{__author__}")
        print(f"{Fore.WHITE}System: {Fore.YELLOW}Intelligent Wordlist Generation")
        print("-" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{__tool_name__}")
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-w", "--wordlist", help="Path to external wordlist")
    group.add_argument("--generate", action="store_true", help="Enable Intelligent Generator")
    
    parser.add_argument("-e", "--extensions", help="Extensions (e.g. php,html,env,yml)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Threads count")
    parser.add_argument("-o", "--output", help="Save results to file")

    args = parser.parse_args()
    exts = args.extensions.split(',') if args.extensions else []
    
    # منطق اختيار الكلمات
    words_data = []
    if args.generate:
        print(f"{Fore.CYAN}[*] Initializing Smart Generator V3...")
        gen = SmartGenerator(args.url)
        words_data = gen.generate()
        print(f"{Fore.GREEN}[+] Generator created {len(words_data):,} base words (before extensions).")
    else:
        try:
            with open(args.wordlist, 'r', errors='ignore') as f:
                words_data = [line.strip() for line in f if line.strip()]
        except:
            sys.exit(f"{Fore.RED}[!] File not found.")

    scanner = FuzzerPyEngine(args.url, words_data, exts, args.threads, args.output)
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Scan Aborted.")
