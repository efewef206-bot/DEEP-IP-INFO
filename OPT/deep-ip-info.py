import requests
import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

class DeepIPGatherer:
    def __init__(self):
        self.base_url_ipapi = "http://ip-api.com/json/"
        self.base_url_ipinfo = "https://ipinfo.io"

    def get_public_ip(self) -> str:
        """Fetches the current public IP if none is provided."""
        try:
            response = requests.get("http://ip-api.com/json/", timeout=5)
            data = response.json()
            if data['status'] == 'success':
                return data['query']
        except Exception as e:
            console.print(f"[bold red]Error fetching public IP: {e}[/bold red]")
        return None

    def gather_ip_data(self, ip_address: str = None) -> dict:
        """
        Gathers deep information for a given IP.
        If ip_address is None, it gathers data for the current machine's public IP.
        """

        if not ip_address:
            console.print("[bold yellow]Resolving Public IP...[/bold yellow]")
            ip_address = self.get_public_ip()
            if not ip_address:
                return {}

        console.print(f"[bold cyan]🔍 Gathering Deep Info for IP: {ip_address}[/bold cyan]")

        # 1. Fetch detailed data from ip-api (Free, no key required)
        try:
            response = requests.get(f"{self.base_url_ipapi}{ip_address}?fields=query,status,country,regionName,city,zip,lat,lon,isp,org,as,reverse,mobile,proxy,hosting", timeout=10)
            data = response.json()

            if data['status'] != 'success':
                console.print(f"[bold red]Failed: {data.get('message', 'Unknown error')}[/bold red]")
                return {}

        except Exception as e:
            console.print(f"[bold red]API Error: {e}[/bold red]")
            return {}

        # 2. Enhance with additional tech details (Optional enrichment)
        # We parse the 'as' field to get ASN name and number if available in format "AS12345 Name"
        as_parts = data.get('as', '').split()
        asn_num = as_parts[0] if as_parts else "N/A"
        asn_name = " ".join(as_parts[1:]) if len(as_parts) > 1 else "Unknown ASN"

        enriched_data = {
            "ip": ip_address,
            "status": data.get('status'),
            "geolocation": {
                "country": data.get('country', 'N/A'),
                "region": data.get('regionName', 'N/A'),
                "city": data.get('city', 'N/A'),
                "zip": data.get('zip', 'N/A'),
                "coordinates": f"{data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}"
            },
            "network": {
                "isp": data.get('isp', 'N/A'),
                "org": data.get('org', 'N/A'),
                "asn_number": asn_num,
                "asn_name": asn_name,
                "connection_type": data.get('mobile') and 'Mobile' or (data.get('proxy') and 'Proxy') or (data.get('hosting') and 'Hosting') or 'Corporate/Residential'
            },
            "security_flags": {
                "is_proxy": bool(data.get('proxy')),
                "is_mobile": bool(data.get('mobile')),
                "is_hosting": bool(data.get('hosting')),
                "has_reverse_dns": True if data.get('reverse') and data['reverse'] != ip_address else False,
                "reverse_dns": data.get('reverse', 'N/A')
            }
        }

        return enriched_data

    def display_results(self, data: dict):
        """Formats and displays the gathered data in a professional UI."""

        if not data:
            console.print("[bold red]No data to display.[/bold red]")
            return

        # Create Rich Text for better formatting
        geo = data['geolocation']
        net = data['network']
        sec = data['security_flags']

        content = f"""
[bold]🌍 Geolocation[/bold]
Country : {geo['country']} | Region: {geo['region']}
City    : {geo['city']}      | Zip   : {geo['zip']}
Coords  : [cyan]{geo['coordinates']}[/cyan]

[bold]📡 Network &amp; Infrastructure[/bold]
ISP     : [green]{net['isp']}[/green]
Org     : {net['org']}
ASN     : {net['asn_number']} ({net['asn_name']})
Type    : {net['connection_type']}

[bold]🔒 Security &amp; Flags[/bold]
Proxy   : {'[red]Yes[/red]' if sec['is_proxy'] else '[green]No[/green]'}
Mobile  : {'[red]Yes[/red]' if sec['is_mobile'] else '[green]No[/green]'}
Hosting : {'[red]Yes[/red]' if sec['is_hosting'] else '[green]No[/green]'}
Reverse DNS: {sec['reverse_dns']}
        """

        panel = Panel(
            content,
            title=f"[bold white on blue] Deep IP Report: {data['ip']} [/bold white on blue]",
            border_style="blue",
            padding=(1, 2)
        )

        console.print(panel)

        # Save to JSON file locally for persistence
        self.save_to_file(data)

    def save_to_file(self, data: dict):
        """Saves the gathered data to deep_ip_report.json."""
        filename = "deep_ip_report.json"
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"[bold green]✅ Report saved to {filename}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to save report: {e}[/bold red]")

def main():
    console.print("[bold underline]Starting Deep IP Gatherer...[/bold underline]")

    gatherer = DeepIPGatherer()

    # Ask user if they want to enter a custom IP or use auto-detect
    choice = console.input("\n[bold]Enter IP Address (press Enter for auto-detect): [/bold]")
    ip_to_gather = choice.strip() if choice else None

    data = gatherer.gather_ip_data(ip_address=ip_to_gather)
    gatherer.display_results(data)

if __name__ == "__main__":
    main()
