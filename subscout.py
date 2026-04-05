#!/usr/bin/env python3
"""
SubScout - Subdomain discovery tool with rich CLI interface
"""
import argparse
import sys
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

console = Console()

BANNER = """
[bold cyan]
  ███████╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ ██╗   ██╗████████╗
  ██╔════╝██║   ██║██╔══██╗██╔════╝██╔════╝██╔═══██╗██║   ██║╚══██╔══╝
  ███████╗██║   ██║██████╔╝███████╗██║     ██║   ██║██║   ██║   ██║   
  ╚════██║██║   ██║██╔══██╗╚════██║██║     ██║   ██║██║   ██║   ██║   
  ███████║╚██████╔╝██████╔╝███████║╚██████╗╚██████╔╝╚██████╔╝   ██║   
  ╚══════╝ ╚═════╝ ╚══════╝ ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   
[/bold cyan]
[dim]Subdomain Scanner by arthenox[/dim]
"""

def get_crtsh(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return set()
        data = response.json()
        subs = set()
        for entry in data:
            name = entry.get('name_value', '')
            if name:
                for sub in name.split('\n'):
                    sub = sub.strip().lower()
                    if sub.endswith(domain) and sub != domain:
                        subs.add(sub)
        return subs
    except:
        return set()

def get_hackertarget(domain):
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return set()
        subs = set()
        for line in response.text.splitlines():
            if ',' in line:
                sub = line.split(',')[0].strip().lower()
                if sub.endswith(domain):
                    subs.add(sub)
        return subs
    except:
        return set()

def get_wayback(domain):
    url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return set()
        data = response.json()
        subs = set()
        for entry in data[1:]:
            if entry:
                url = entry[0]
                match = re.search(r'https?://([^/]+)', url)
                if match:
                    sub = match.group(1).lower()
                    if sub.endswith(domain):
                        subs.add(sub)
        return subs
    except:
        return set()

def get_subdomains(domain, sources, verbose=False):
    all_subs = set()
    source_functions = {
        'crtsh': get_crtsh,
        'hackertarget': get_hackertarget,
        'wayback': get_wayback
    }
    to_run = [(name, source_functions[name]) for name in sources if name in source_functions]
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Fetching subdomains...", total=len(to_run))
        for name, func in to_run:
            if verbose:
                console.print(f"[dim]Querying {name}...[/dim]")
            try:
                result = func(domain)
                all_subs.update(result)
                if verbose:
                    console.print(f"[green]✓ {name}: {len(result)} subdomains[/green]")
            except Exception as e:
                if verbose:
                    console.print(f"[red]✗ {name}: failed - {str(e)}[/red]")
            progress.advance(task)
    return all_subs

def check_alive(subdomain):
    """Check if a subdomain responds to HTTP/HTTPS."""
    for scheme in ('https', 'http'):
        try:
            resp = requests.get(f"{scheme}://{subdomain}", timeout=5, allow_redirects=True)
            if resp.status_code < 500:
                return True
        except requests.exceptions.RequestException:
            continue
    return False

def check_alive_bulk(subdomains, max_workers=10):
    """Check multiple subdomains in parallel."""
    alive = set()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Checking live hosts...", total=len(subdomains))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_sub = {executor.submit(check_alive, sub): sub for sub in subdomains}
            for future in as_completed(future_to_sub):
                sub = future_to_sub[future]
                try:
                    if future.result():
                        alive.add(sub)
                except:
                    pass
                progress.advance(task)
    return alive

def display_results(domain, subdomains, output_file=None, alive=None):
    console.print(Panel(f"[bold]Target: {domain}[/bold] | [green]Found {len(subdomains)} subdomains[/green]"))
    table = Table(title="Discovered Subdomains", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim")
    table.add_column("Subdomain", style="cyan")
    if alive is not None:
        table.add_column("Status", justify="center")
    table.add_column("Length", justify="right", style="green")
    for idx, sub in enumerate(sorted(subdomains), 1):
        row = [str(idx), sub]
        if alive is not None:
            if sub in alive:
                row.append("[green]✅ alive[/green]")
            else:
                row.append("[red]❌ dead[/red]")
        row.append(str(len(sub)))
        table.add_row(*row)
    console.print(table)
    if output_file:
        with open(output_file, 'w') as f:
            for sub in sorted(subdomains):
                f.write(sub + '\n')
        console.print(f"[green]✓ Results saved to {output_file}[/green]")
    if alive is not None and alive:
        alive_file = output_file.replace('.txt', '_alive.txt') if output_file else 'alive_subdomains.txt'
        with open(alive_file, 'w') as f:
            for sub in sorted(alive):
                f.write(sub + '\n')
        console.print(f"[green]✓ Alive subdomains saved to {alive_file}[/green]")

def main():
    parser = argparse.ArgumentParser(
        description="SubScout - Subdomain discovery tool with rich CLI interface",
        epilog="Example: python subscout.py example.com -s crtsh hackertarget -o subs.txt --alive"
    )
    parser.add_argument("domain", help="Target domain (e.g., example.com)")
    parser.add_argument("-s", "--sources", nargs="+", default=['crtsh', 'hackertarget'],
                        choices=['crtsh', 'hackertarget', 'wayback'],
                        help="Data sources to use (default: crtsh hackertarget)")
    parser.add_argument("-o", "--output", help="Save results to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("--alive", action="store_true", help="Check which subdomains are live")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()
    if args.no_color:
        console.no_color = True
    console.print(BANNER)

    subdomains = get_subdomains(args.domain, args.sources, args.verbose)

    if not subdomains:
        console.print("[red]❌ No subdomains found.[/red]")
        sys.exit(1)

    alive = None
    if args.alive:
        console.print("[cyan]🔍 Checking live subdomains...[/cyan]")
        alive = check_alive_bulk(subdomains, max_workers=20)

    display_results(args.domain, subdomains, args.output, alive)

if __name__ == "__main__":
    main()
