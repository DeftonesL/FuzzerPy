# FuzzerPy v7.0.0

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat&logo=python)
![AsyncIO](https://img.shields.io/badge/AsyncIO-High%20Performance-green?style=flat)
![License](https://img.shields.io/badge/License-MIT-orange?style=flat)

**FuzzerPy** is a high-performance, asynchronous directory and file reconnaissance tool written in Python. It is designed for security professionals and Red Teamers to discover hidden paths on web servers with maximum efficiency.

Unlike traditional scanners, FuzzerPy features a **Context-Aware Wordlist Generator**, which analyzes the target domain to dynamically create potential path combinations, reducing reliance on static wordlists.

## Key Features

* **High Concurrency:** Built on `aiohttp` and `asyncio` to handle thousands of requests per second.
* **Context-Aware Generation:** Automatically generates a targeted wordlist based on the domain name, common naming conventions, and years (e.g., `admin2024`, `example_dev`).
* **Smart Retry System:** Automatically retries failed requests to ensure accuracy in unstable network conditions.
* **Flexible Output:**
    * **Standard Mode:** Displays only valid results (clean output).
    * **Verbose Mode:** Displays a real-time progress bar with active statistics.
* **Extension Fuzzing:** Supports multiple file extensions simultaneously.
* **Resource Control:** Limit wordlist size and control thread count.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YourUsername/FuzzerPy.git](https://github.com/YourUsername/FuzzerPy.git)
    cd FuzzerPy
    ```

2.  **Install dependencies:**
    ```bash
    pip install aiohttp colorama tqdm
    ```
---
## Usage
    
### Basic Usage (Auto-Generation)
FuzzerPy will analyze the target URL and generate a wordlist automatically.
```bash
python fuzzerpy.py -u [http://example.com](http://example.com) --generate
```
---
## Options

| Argument | Description |
| :--- | :--- |
| `-u`, `--url` | Target URL (e.g., http://example.com) |
| `-w`, `--wordlist` | Path to an external wordlist file |
| `--generate` | Enable the Context-Aware Wordlist Generator |
| `-l`, `--limit` | Limit the number of generated words (e.g., 5000) |
| `-e`, `--extensions` | Comma-separated list of extensions (e.g., php,html) |
| `-t`, `--threads` | Number of concurrent threads (Default: 50) |
| `-v`, `--verbose` | Enable verbose mode (Progress bar) |
| `-o`, `--output` | File path to save the results |

## Integrity Check
The tool includes a basic author integrity check. Modification of the source headers may prevent the tool from executing.

## Disclaimer
This tool is developed for **educational and authorized security testing purposes only**. The author is not responsible for any misuse or damage caused by this tool. Ensure you have proper authorization before scanning any target.

---
**Developed by Saleh Al-Otaibi**
