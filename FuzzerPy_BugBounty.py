"""
FuzzerPy - Bug Bounty Safe Edition
Modified for compliance with bug bounty program rules
Maximum 100 requests/second with safety features

Based on FuzzerPy v7.0.0 by Saleh Al-Otaibi
Bug Bounty Modifications by Bug Hunter
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

__version__ = "7.1.0-bugbounty"
__tool_name__ = "FuzzerPy Bug Bounty Edition"

init(autoreset=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "BugBountyResearch/1.0 (Security Testing)" 
]

class SmartGenerator:
    """Context-aware wordlist generator"""
    def __init__(self, target_url, limit=None, bug_bounty_mode=True):
        self.target_domain = self.extract_domain_name(target_url)
        self.limit = limit
        self.bug_bounty_mode = bug_bounty_mode
        
        if bug_bounty_mode:
            self.cores = [
                "error_log", "debug", "backup", "test", "temp",
                "config", "conf", "settings", ".env",
                "admin", "administrator", "cpanel", "dashboard",
                "api", "v1", "v2", "graphql", "rest",
                "dev", "staging", "test", "demo",
                "db", "database", "sql", "dump",
                "old", "bak", "backup", "save"
            ]
        else:
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
        print(f"{Fore.CYAN}[INFO] Generating bug bounty focused wordlist for: {Fore.WHITE}{self.target_domain}")
        wordlist = set()
        wordlist.update(self.cores)
        wordlist.add(self.target_domain)

        for core in self.cores[:10]:  
            for year in self.years[-3:]:  
                wordlist.add(f"{core}{year}")
                wordlist.add(f"{core}-{year}")

        combinations = itertools.product(self.cores[:15], self.separators, self.modifiers[:5])
        for core, sep, mod in combinations:
            wordlist.add(f"{core}{sep}{mod}")

        for core in self.cores[:10]:
            wordlist.add(f"{self.target_domain}_{core}")
            wordlist.add(f"{self.target_domain}-{core}")

        final_list = list(wordlist)
        random.shuffle(final_list)
        
        if self.limit and self.limit > 0:
            final_list = final_list[:self.limit]
        
        print(f"{Fore.GREEN}[INFO] Generated {len(final_list)} unique paths")
        return final_list


class RateLimiter:
    """
    Rate limiter to ensure compliance with bug bounty rules
    Maximum 100 requests per second
    """
    def __init__(self, max_per_second=90):  
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_request_time = 0
        self.lock = asyncio.Lock()
        self.request_count = 0
        self.start_time = time.time()
    
    async def wait(self):
        """Wait if necessary to maintain rate limit"""
        async with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()
            self.request_count += 1
    
    def get_current_rate(self):
        """Get current requests per second"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.request_count / elapsed
        return 0


class FuzzerPyBugBountyEngine:
    """
    Bug Bounty Safe Scanner
    - Rate limited to 100 req/sec maximum
    - Longer timeouts
    - Respectful error handling
    - Stops on repeated failures
    """
    def __init__(self, target, wordlist_data, extensions, max_rate=90, 
                 verbose=False, output_file=None, stop_on_errors=10):
        self.target = target.rstrip('/')
        self.wordlist_data = wordlist_data
        self.extensions = extensions
        self.rate_limiter = RateLimiter(max_per_second=max_rate)
        self.verbose = verbose
        self.output_file = output_file
        self.stop_on_errors = stop_on_errors
        self.found_urls = []
        self.stats = {
            'total': 0, 
            200: 0, 
            403: 0, 
            302: 0, 
            404: 0,
            'errors': 0,
            'consecutive_errors': 0
        }
        self.timeout = aiohttp.ClientTimeout(total=10, sock_connect=5)  
        self.max_retries = 1  
        self.should_stop = False

    def get_random_agent(self):
        return random.choice(USER_AGENTS)

    def log_result(self, msg, pbar=None):
        if self.verbose and pbar:
            tqdm.write(msg)
        else:
            print(msg)

    def save_file(self, line):
        if self.output_file:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(line + '\n')

    async def scan_url(self, session, path, pbar=None):
        """Scan a single URL with rate limiting"""
        if self.should_stop:
            if pbar:
                pbar.update(1)
            return
        
        await self.rate_limiter.wait()
        
        url = f"{self.target}/{path}"
        headers = {
            'User-Agent': self.get_random_agent(),
            'Accept': '*/*'
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                async with session.get(url, headers=headers, 
                                     allow_redirects=False, 
                                     timeout=self.timeout) as response:
                    status = response.status
                    self.stats['total'] += 1
                    self.stats['consecutive_errors'] = 0  
                    msg = ""
                    
                    if status == 200:
                        size = len(await response.read())
                        msg = f"{Fore.GREEN}[200] OK: {url} ({size} bytes){Style.RESET_ALL}"
                        self.stats[200] += 1
                        self.found_urls.append(url)
                        self.save_file(f"[200] {url}")
                    elif status == 403:
                        msg = f"{Fore.YELLOW}[403] Forbidden: {url}{Style.RESET_ALL}"
                        self.stats[403] += 1
                        self.found_urls.append(url)
                        self.save_file(f"[403] {url}")
                    elif status in [301, 302, 307, 308]:
                        loc = response.headers.get('Location', 'Unknown')
                        msg = f"{Fore.BLUE}[{status}] Redirect: {url} -> {loc}{Style.RESET_ALL}"
                        self.stats[302] += 1
                        self.found_urls.append(url)
                        self.save_file(f"[{status}] {url} -> {loc}")
                    elif status == 404:
                        self.stats[404] += 1
                    
                    if msg:
                        self.log_result(msg, pbar)
                        if pbar and self.verbose:
                            rate = self.rate_limiter.get_current_rate()
                            pbar.set_postfix({
                                'Found': len(self.found_urls),
                                'Rate': f'{rate:.1f}/s'
                            }, refresh=False)
                    break
                    
            except asyncio.TimeoutError:
                self.stats['errors'] += 1
                self.stats['consecutive_errors'] += 1
                if attempt == self.max_retries:
                    if self.verbose:
                        self.log_result(f"{Fore.RED}[TIMEOUT] {url}{Style.RESET_ALL}", pbar)
            except aiohttp.ClientError as e:
                self.stats['errors'] += 1
                self.stats['consecutive_errors'] += 1
                if attempt == self.max_retries:
                    if self.verbose:
                        self.log_result(f"{Fore.RED}[ERROR] {url}: {str(e)[:50]}{Style.RESET_ALL}", pbar)
            except Exception as e:
                self.stats['errors'] += 1
                self.stats['consecutive_errors'] += 1
                break
        
        if self.stats['consecutive_errors'] >= self.stop_on_errors:
            self.should_stop = True
            print(f"\n{Fore.RED}[WARNING] {self.stop_on_errors} consecutive errors detected!")
            print(f"{Fore.RED}[WARNING] Stopping scan to avoid overloading target.{Style.RESET_ALL}")
        
        if pbar:
            pbar.update(1)

    async def run(self):
        """Main scanning loop"""
        self.print_banner()
        
        final_payloads = []
        for word in self.wordlist_data:
            final_payloads.append(word)
            for ext in self.extensions:
                final_payloads.append(f"{word}.{ext}")
        
        total_reqs = len(final_payloads)
        
        print(f"{Fore.WHITE}[INFO] Target: {Fore.GREEN}{self.target}")
        print(f"{Fore.WHITE}[INFO] Total Payloads: {Fore.GREEN}{total_reqs:,}")
        print(f"{Fore.WHITE}[INFO] Max Rate: {Fore.GREEN}{self.rate_limiter.max_per_second} req/sec")
        print(f"{Fore.WHITE}[INFO] Timeout: {Fore.GREEN}{self.timeout.total}s")
        print(f"{Fore.YELLOW}[INFO] Bug Bounty Safe Mode: ENABLED")
        if not self.verbose:
            print(f"{Fore.YELLOW}[INFO] Output Mode: Hits only")
        print("-" * 60)

        connector = aiohttp.TCPConnector(
            limit=100,  
            ttl_dns_cache=300,
            ssl=False
        )
        
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                with tqdm(total=total_reqs, disable=not self.verbose,
                         desc="Scanning", unit="req", ncols=100,
                         bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} {postfix}") as pbar:
                    
                    tasks = []
                    for path in final_payloads:
                        if self.should_stop:
                            break
                        task = asyncio.create_task(self.scan_url(session, path, pbar))
                        tasks.append(task)
                    
                    await asyncio.gather(*tasks, return_exceptions=True)
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Scan interrupted by user{Style.RESET_ALL}")
            self.should_stop = True
        
        duration = time.time() - start_time
        self.print_summary(duration, total_reqs)

    def print_summary(self, duration, total_planned):
        """Print scan summary"""
        print("\n" + Fore.WHITE + "=" * 60)
        print(f"{Fore.CYAN}SCAN REPORT{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Duration: {duration:.2f}s | Avg Rate: {self.stats['total']/duration if duration > 0 else 0:.1f} req/sec")
        print(f"{Fore.WHITE}Completed: {self.stats['total']:,}/{total_planned:,}")
        print(f"{Fore.GREEN}200 OK: {self.stats[200]} | {Fore.YELLOW}403 Forbidden: {self.stats[403]}")
        print(f"{Fore.BLUE}Redirects: {self.stats[302]} | {Fore.WHITE}404: {self.stats[404]}")
        print(f"{Fore.RED}Errors: {self.stats['errors']}")
        print(f"{Fore.CYAN}Total Found: {len(self.found_urls)}")
        print(Fore.WHITE + "=" * 60)
        
        if self.found_urls:
            print(f"\n{Fore.GREEN}[+] Found URLs:{Style.RESET_ALL}")
            for url in self.found_urls[:20]:  
                print(f"  • {url}")
            if len(self.found_urls) > 20:
                print(f"  ... and {len(self.found_urls) - 20} more")

    def print_banner(self):
        """Print tool banner"""
        print(Fore.CYAN + rf"""
  ______                         _____       
 |  ____|                       |  __ \      
 | |__ _   _ _____________ _ __ | |__) |   _ 
 |  __| | | |_  /_  /_  / | '__||  ___/ | | |
 | |  | |_| |/ / / / / /| | |   | |   | |_| |
 |_|   \__,_/___/___/___|_|_|   |_|    \__, |
   Bug Bounty Safe Edition             __/ |
                                       |___/  v{__version__}
        """ + Style.RESET_ALL)
        print(f"{Fore.WHITE}Modified for Bug Bounty Compliance")
        print(f"{Fore.GREEN}✓ Rate Limited (Max 100 req/sec)")
        print(f"{Fore.GREEN}✓ Respectful Scanning")
        print(f"{Fore.GREEN}✓ Auto-stop on Errors")
        print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"{__tool_name__} - Bug Bounty Compliant Scanner"
    )
    parser.add_argument("-u", "--url", required=True, help="Target URL")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-w", "--wordlist", help="Path to wordlist file")
    group.add_argument("--generate", action="store_true", 
                      help="Generate bug bounty focused wordlist")
    
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Enable verbose output with progress bar")
    parser.add_argument("-l", "--limit", type=int, 
                       help="Limit wordlist size (useful for testing)")
    parser.add_argument("-e", "--extensions", default="",
                       help="File extensions (comma separated). Example: php,asp,bak,old")
    parser.add_argument("-r", "--rate", type=int, default=90,
                       help="Max requests per second (default: 90, max: 100)")
    parser.add_argument("-o", "--output", 
                       help="Output file for found URLs")
    parser.add_argument("--stop-on-errors", type=int, default=10,
                       help="Stop after N consecutive errors (default: 10)")

    args = parser.parse_args()
    
    if args.rate > 100:
        print(f"{Fore.RED}[ERROR] Rate limit cannot exceed 100 req/sec per bug bounty rules")
        print(f"{Fore.YELLOW}[INFO] Setting rate to 90 req/sec (safe default)")
        args.rate = 90
    
    exts = [e.strip() for e in args.extensions.split(',') if e.strip()]
    
    words_data = []
    if args.generate:
        gen = SmartGenerator(args.url, limit=args.limit, bug_bounty_mode=True)
        words_data = gen.generate()
    else:
        try:
            with open(args.wordlist, 'r', errors='ignore', encoding='utf-8') as f:
                content = [line.strip() for line in f if line.strip()]
                if args.limit and args.limit > 0:
                    random.shuffle(content)
                    words_data = content[:args.limit]
                else:
                    words_data = content
            print(f"{Fore.GREEN}[INFO] Loaded {len(words_data)} words from {args.wordlist}")
        except FileNotFoundError:
            sys.exit(f"{Fore.RED}[ERROR] Wordlist file not found: {args.wordlist}")
        except Exception as e:
            sys.exit(f"{Fore.RED}[ERROR] Failed to load wordlist: {e}")

    scanner = FuzzerPyBugBountyEngine(
        target=args.url,
        wordlist_data=words_data,
        extensions=exts,
        max_rate=args.rate,
        verbose=args.verbose,
        output_file=args.output,
        stop_on_errors=args.stop_on_errors
    )
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[INFO] Scan interrupted by user.")
    except Exception as e:
        print(f"\n{Fore.RED}[ERROR] Unexpected error: {e}")
