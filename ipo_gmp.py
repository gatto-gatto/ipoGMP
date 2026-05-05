#!/usr/bin/env python3
"""
IPO GMP Fetcher - Scrapes live IPO Grey Market Premium data from InvestorGain.com
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
import re, sys, time

URL = "https://www.investorgain.com/report/live-ipo-gmp/331/"
console = Console()


def fetch_ipo_gmp():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = None
    try:
        with console.status("[bold cyan]🚀 Fetching live IPO GMP data...", spinner="dots"):
            driver = webdriver.Chrome(options=options)
            driver.get(URL)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#reportTable tbody tr td"))
            )
            time.sleep(2)

        table_el = driver.find_element(By.ID, "reportTable")
        rows = table_el.find_elements(By.CSS_SELECTOR, "tbody tr")
        data = []
        for row in rows:
            cells = [c.text.strip() for c in row.find_elements(By.TAG_NAME, "td")]
            if cells and any(cells):
                data.append(cells)
        return data
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/]")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


def parse_name(raw):
    text = raw.split("\n")[0].strip()
    status = ""
    if text and text[-1] in "UOC":
        status = text[-1]
        text = text[:-1].strip()
    # Listed IPOs have L@price(pct%) pattern
    lm = re.search(r'L@[\d.,]+\s*\([^)]*\)', text)
    if lm:
        text = text[:lm.start()].strip()
        status = "L"
    # Detect type
    ipo_type = "Mainboard"
    for t in ["NSE SME", "BSE SME"]:
        if t in text:
            ipo_type = "SME"
            text = text.replace(t, "").strip()
    text = text.replace("IPO", "").strip()
    return text, ipo_type, status


def parse_gmp(raw):
    line = raw.split("\n")[0].strip()
    vm = re.search(r"₹([\d.,\-]+)", line)
    pm = re.search(r"\(([\-\d.]+)%\)", line)
    val = vm.group(1) if vm else "--"
    try:
        pct = float(pm.group(1)) if pm else 0.0
    except ValueError:
        pct = 0.0
    return val, pct


STATUS = {"U": ("UPCOMING", "bold yellow"), "O": ("OPEN", "bold green"),
          "C": ("CLOSED", "bold blue"), "L": ("LISTED", "bold magenta")}


def display(data):
    console.print()
    console.print(Panel(
        Text.assemble(
            ("📈 Live IPO GMP ", "bold bright_cyan"),
            ("— Grey Market Premium\n", "bold white"),
            ("Source: investorgain.com | Data is indicative only", "dim italic"),
        ), border_style="bright_blue", padding=(1, 2),
    ))

    table = Table(box=box.SIMPLE_HEAVY, header_style="bold white on #16213e",
                  border_style="dim blue", padding=(0, 1))
    table.add_column("#", style="dim", justify="right", width=3)
    table.add_column("IPO Name", min_width=20, no_wrap=True)
    table.add_column("Type", justify="center", width=6)
    table.add_column("GMP ₹", justify="right", width=8)
    table.add_column("GMP %", justify="right", width=9)
    table.add_column("Status", justify="center", width=10)

    for i, row in enumerate(data, 1):
        name, ipo_type, status = parse_name(row[0] if len(row) > 0 else "")
        gmp_val, gmp_pct = parse_gmp(row[1] if len(row) > 1 else "")

        # Style type
        type_s = "[cyan]SME[/]" if ipo_type == "SME" else "[bright_magenta]Main[/]"

        # Style GMP
        if gmp_val == "--":
            v_s, p_s = "[dim]--[/]", "[dim]0.0%[/]"
        elif gmp_pct < 0:
            v_s = f"[bold red]₹{gmp_val}[/]"
            p_s = f"[bold red]{gmp_pct}%[/]"
        elif gmp_pct == 0:
            v_s = f"[yellow]₹{gmp_val}[/]"
            p_s = f"[yellow]0.0%[/]"
        elif gmp_pct >= 30:
            v_s = f"[bold bright_green]₹{gmp_val}[/]"
            p_s = f"[bold bright_green]{gmp_pct}%[/]"
        elif gmp_pct >= 10:
            v_s = f"[bold green]₹{gmp_val}[/]"
            p_s = f"[bold green]{gmp_pct}%[/]"
        else:
            v_s = f"[green]₹{gmp_val}[/]"
            p_s = f"[green]{gmp_pct}%[/]"

        # Style status
        if status in STATUS:
            lbl, clr = STATUS[status]
            st_s = f"[{clr}]{lbl}[/]"
        else:
            st_s = "[dim]-[/]"

        table.add_row(str(i), name, type_s, v_s, p_s, st_s)

    console.print(table)
    console.print(f"\n  [bold cyan]Total IPOs:[/] {len(data)}\n")


def main():
    data = fetch_ipo_gmp()
    if not data:
        console.print("[bold yellow]⚠️  No IPO GMP data found.[/]")
        sys.exit(0)
    display(data)


if __name__ == "__main__":
    main()
