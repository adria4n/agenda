#!/usr/bin/env python3

import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://streamxhd.sbs/eventos.json"
CDMX = ZoneInfo("America/Mexico_City")
LIMA = ZoneInfo("America/Lima")

def parse_time(time_str, timezone_str="America/Lima"):
    try:
        if "T" in time_str:
            dt = datetime.fromisoformat(time_str)
        else:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            tz = ZoneInfo(timezone_str) if timezone_str else LIMA
            dt = dt.replace(tzinfo=tz)
        return dt.astimezone(CDMX)
    except Exception as e:
        print(f"Error parseando tiempo '{time_str}': {e}")
        return None

def format_time(dt):
    if not dt:
        return ""
    return dt.strftime("%-I:%M%p")

def clean_name(name):
    return name.strip() if name else ""

def get_logo(event, league):
    for key in ["homeLogo", "awayLogo"]:
        logo = event.get(key, "")
        if logo and logo.startswith("http"):
            return logo
    return league.get("logo", "") or ""

def main():
    print("Descargando eventos...")
    try:
        with urllib.request.urlopen(URL, timeout=30) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error descargando: {e}")
        return

    hoy = datetime.now(CDMX).date()
    streams = []

    for sport in data.get("sports", []):
        for league in sport.get("leagues", []):
            league_name = league.get("name", "Sin liga")
            for event in league.get("events", []):
                dt = parse_time(event.get("time", ""), event.get("timezone", "America/Lima"))
                if not dt or dt.date() != hoy:
                    continue

                home = clean_name(event.get("homeTeam") or event.get("title", "").split(" vs ")[0])
                away = clean_name(event.get("awayTeam") or "")
                title = f"{home} vs {away}" if away else event.get("title", "Evento")
                time_str = format_time(dt)
                
                logo = get_logo(event, league)
                servers = [s for s in event.get("servers", []) if s.get("active", True)]
                
                if not servers:
                    continue
                
                for i, server in enumerate(servers):
                    server_name = server.get("name", f"Server {i+1}").strip()
                    url = server.get("url", "")
                    if not url:
                        continue
                    
                    base_nombre = f"{league_name} / {title}"
                    if time_str:
                        base_nombre += f" {time_str}"
                    
                    if len(servers) > 1:
                        nombre = f"{base_nombre} - {server_name}"
                    else:
                        nombre = base_nombre
                    
                    streams.append({
                        "nombre": nombre,
                        "logo": logo,
                        "url": url,
                        "_dt": dt
                    })

    streams.sort(key=lambda x: x["_dt"])

    for s in streams:
        s.pop("_dt", None)

    output = {
        "total": len(streams),
        "generado": datetime.now(CDMX).strftime("%Y-%m-%d %H:%M CDMX"),
        "streams": streams
    }

    with open("streams_simple.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nListo! {len(streams)} streams de hoy.")
    print("Archivo: streams_simple.json")

    print("\n--- Preview ---")
    for s in streams[:15]:
        print(f"  {s['nombre']}")

if __name__ == "__main__":
    main()
