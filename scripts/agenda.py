#!/usr/bin/env python3

import json
import urllib.request
import re
from datetime import datetime
from zoneinfo import ZoneInfo

CDMX = ZoneInfo("America/Mexico_City")
LIMA = ZoneInfo("America/Lima")
PATH = "/eventos.json"
VERI = "https://streamveri.xyz"

def obtener_dominios():
    with urllib.request.urlopen(VERI, timeout=15) as r:
        html = r.read().decode("utf-8", errors="ignore")
    dominios = re.findall(r'streamxhd\.[a-z0-9]+', html, re.I)
    bases = []
    for d in dict.fromkeys(dominios):
        bases.append(f"https://{d}")
    if not bases:
        raise Exception("No se encontraron dominios en streamveri.xyz")
    return bases

def obtener_json():
    for base in obtener_dominios():
        url = base + PATH
        try:
            print(f"Intentando {url}")
            with urllib.request.urlopen(url, timeout=15) as response:
                if response.status == 200:
                    print(f"OK: {url}")
                    return json.loads(response.read().decode())
        except Exception as e:
            print(f"Fallo {url}: {e}")
    raise Exception("Todos los dominios fallaron")

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

def get_logo(event):
    for key in ["logo", "homeLogo", "awayLogo"]:
        logo = event.get(key, "")
        if logo and logo.startswith("http"):
            return logo
    return ""

def main():
    data = obtener_json()

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
                
                logo = get_logo(event)
                homelogo = event.get("homeLogo", "") or ""
                awaylogo = event.get("awayLogo", "") or ""
                
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
                        "homelogo": homelogo,
                        "awaylogo": awaylogo,
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

    with open("agenda.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nListo! {len(streams)} streams de hoy.")
    print("Archivo: agenda.json")

    print("\n--- Preview ---")
    for s in streams[:15]:
        print(f"  {s['nombre']}")

if __name__ == "__main__":
    main()
