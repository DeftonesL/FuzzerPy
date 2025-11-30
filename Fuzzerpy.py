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
import time
from urllib.parse import urlparse
from colorama import Fore, Style, init
from tqdm.asyncio import tqdm

__author__ = "Saleh Al-Otaibi"
__version__ = "7.0.0"
__tool_name__ = "FuzzerPy"

init(autoreset=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

class SmartGenerator:
    def __init__(self, target_url, limit=None):
        self.target_domain = self.extract_domain_name(target_url)
        self.limit = limit
        self.cores = [
            "admin", "login", "user", "api", "v1", "v2", "staging", "dev", "test",
            "prod", "backup", "db", "sql", "config", "conf", "settings", "install",
            "assets", "static", "images", "js", "css", "dashboard", "panel", "cpanel",
            "manager", "portal", "secure", "auth", "account", "member", "root", "system"
        ]
        self.years = [str(y) for y in range(2020, 2027)]
        self.separators = ["", "-", "_", "."]
        self.modifiers = ["bak", "old", "new", "temp", "save", "copy", "zip", "rar"]

    def extract_domain_name(self, url):
        try:
            domain = urlparse(url).netloc
            name = domain.split('.')
            if 'www' in name: name.remove('www')
            return name[0]
        except:
            return "site"

    def generate(self):
        print(f"{Fore.CYAN}[INFO] Analyzing target context: {Fore.WHITE}{self.target_domain}")
        wordlist = set()
        wordlist.update(self.cores)
        wordlist.add(self.target_domain)

        for core in self.cores:
            for year in self.years:
                wordlist.add(f"{core}{year}")
                wordlist.add(f"{core}-{year}")

        combinations = itertools.product(self.cores, self.separators, self.modifiers)
        for core, sep, mod in combinations:
            wordlist.add(f"{core}{sep}{mod}")

        for core in self.cores:
            wordlist.add(f"{self.target_domain}_{core}")
            wordlist.add(f"{self.target_domain}-{core}")

        final_list = list(wordlist)
        random.shuffle(final_list)
        
        if self.limit and self.limit > 0:
            final_list = final_list[:self.limit]
        return final_list

class FuzzerPyEngine:
    def __init__(self, target, wordlist_data, extensions, threads, verbose=False, output_file=None):
        self.target = target.rstrip('/')
        self.wordlist_data = wordlist_data
        self.extensions = extensions
        self.semaphore = asyncio.Semaphore(threads)
        self.verbose = verbose
        self.output_file = output_file
        self.found_urls = []
        self.stats = {'total': 0, 200: 0, 403: 0, 302: 0, 'errors': 0}
        self.timeout = aiohttp.ClientTimeout(total=5, sock_connect=3)
        self.max_retries = 2
        
        if __author__ != "Saleh Al-Otaibi":
            sys.exit("[ERROR] Integrity Check Failed.")

    def get_random_agent(self):
        return random.choice(USER_AGENTS)

    def log_result(self, msg, pbar=None):
        if self.verbose and pbar:
            tqdm.write(msg)
        else:
            print(msg)

    def save_file(self, line):
        if self.output_file:
            with open(self.output_file, 'a') as f:
                f.write(line + '\n')

    async def scan_url(self, session, path, pbar=None):
        url = f"{self.target}/{path}"
        headers = {'User-Agent': self.get_random_agent()}
        
        async with self.semaphore:
            for attempt in range(self.max_retries + 1):
                try:
                    async with session.get(url, headers=headers, allow_redirects=False, timeout=self.timeout) as response:
                        status = response.status
                        self.stats['total'] += 1
                        msg = ""
                        
                        if status == 200:
                            msg = f"{Fore.GREEN}[200] OK: {url}{Style.RESET_ALL}"
                            self.stats[200] += 1
                        elif status == 403:
                            msg = f"{Fore.YELLOW}[403] Forbidden: {url}{Style.RESET_ALL}"
                            self.stats[403] += 1
                        elif status in [301, 302]:
                            loc = response.headers.get('Location', 'Unknown')
                            msg = f"{Fore.BLUE}[{status}] Redirect: {url} -> {loc}{Style.RESET_ALL}"
                            self.stats[302] += 1
                        
                        if msg:
                            self.found_urls.append(url)
                            self.log_result(msg, pbar)
                            self.save_file(f"[{status}] {url}")
                            if pbar and self.verbose:
                                pbar.set_postfix({'Found': len(self.found_urls)}, refresh=False)
                        break 
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    if attempt == self.max_retries:
                        self.stats['errors'] += 1
                except Exception:
                    break
            
            if pbar:
                pbar.update(1)

    async def run(self):
        self.print_banner()
        final_payloads = []
        for word in self.wordlist_data:
            final_payloads.append(word)
            for ext in self.extensions:
                final_payloads.append(f"{word}.{ext}")
        
        total_reqs = len(final_payloads)
        print(f"{Fore.WHITE}[INFO] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[INFO] Total Payloads: {Fore.GREEN}{total_reqs:,}")
        if not self.verbose:
            print(f"{Fore.YELLOW}[INFO] Output Mode: Standard (Hits only)")
        print("-" * 60)

        connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, ssl=False)
        start_time = time.time()

        async with aiohttp.ClientSession(connector=connector) as session:
            with tqdm(total=total_reqs, disable=not self.verbose, 
                      desc="Scanning", unit="req", ncols=90, 
                      bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} {postfix}") as pbar:
                tasks = []
                for path in final_payloads:
                    tasks.append(self.scan_url(session, path, pbar))
                await asyncio.gather(*tasks)

        duration = time.time() - start_time
        self.print_summary(duration, total_reqs)

    def print_summary(self, duration, total_planned):
        print("\n" + Fore.WHITE + "=" * 60)
        print(f"{Fore.CYAN}SCAN REPORT | {Fore.WHITE}Duration: {duration:.2f}s")
        print(f"{Fore.WHITE}Requests: {self.stats['total']:,}/{total_planned:,} | {Fore.RED}Failed: {self.stats['errors']}")
        print(f"{Fore.GREEN}200 OK: {self.stats[200]} | {Fore.YELLOW}403 Forbidden: {self.stats[403]} | {Fore.BLUE}Redirects: {self.stats[302]}")
        print(Fore.WHITE + "=" * 60)

    def print_banner(self):
        print(Fore.RED + rf"""
  ______                         _____       
 |  ____|                       |  __ \      
 | |__ _   _ _____________ _ __ | |__) |   _ 
 |  __| | | |_  /_  /_  / | '__||  ___/ | | |
 | |  | |_| |/ / / / / /| | |   | |   | |_| |
 |_|   \__,_/___/___/___|_|_|   |_|    \__, |
                                        __/ |
                                       |___/  v{__version__}
        """ + Style.RESET_ALL)
        print(f"{Fore.WHITE}Author: {__author__}")
        print("-" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{__tool_name__} - High Performance Web Scanner")
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-w", "--wordlist", help="Path to external wordlist")
    group.add_argument("--generate", action="store_true", help="Use context-aware wordlist generator")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose progress bar")
    parser.add_argument("-l", "--limit", type=int, help="Limit the size of generated wordlist")
    parser.add_argument("-e", "--extensions", help="File extensions (comma separated)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Number of concurrent threads")
    parser.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()
    exts = args.extensions.split(',') if args.extensions else []
    
    words_data = []
    if args.generate:
        gen = SmartGenerator(args.url, limit=args.limit)
        words_data = gen.generate()
    else:
        try:
            with open(args.wordlist, 'r', errors='ignore') as f:
                content = [line.strip() for line in f if line.strip()]
                if args.limit and args.limit > 0:
                     random.shuffle(content)
                     words_data = content[:args.limit]
                else:
                    words_data = content
        except:
            sys.exit(f"{Fore.RED}[ERROR] Wordlist file not found.")

    scanner = FuzzerPyEngine(args.url, words_data, exts, args.threads, args.verbose, args.output)
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        print(Fore.RED + "\n[INFO] Scan interrupted by user.")
        scanner.print_summary(0, 0)
