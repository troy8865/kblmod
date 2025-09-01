import requests
import os
import re
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()

def dlhd():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Eseguendo dlhd...")

    LINK_DADDY = os.getenv("LINK_DADDY", "https://daddylive.sx").strip()
    JSON_FILE = "daddyliveSchedule.json"
    OUTPUT_FILE = "dlhd.m3u"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    def get_stream_from_channel_id(channel_id):
        return f"{LINK_DADDY}/stream/stream-{channel_id}.php"

    # 24/7 kanallar
    try:
        url = f"{LINK_DADDY}/24-7-channels.php"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        channels_247 = []

        grid_items = soup.find_all("div", class_="grid-item")
        for div in grid_items:
            a = div.find("a", href=True)
            if not a: continue
            href = a["href"].strip().replace(" ", "").replace("//", "/")
            name = a.find("strong").get_text(strip=True) if a.find("strong") else a.get_text(strip=True)
            if name == "LA7d HD+ Italy": name = "Canale 5 Italy"
            if name == "Sky Calcio 7 (257) Italy": name = "DAZN"
            match = re.search(r'stream-(\d+)\.php', href)
            if not match: continue
            channel_id = match.group(1)
            channels_247.append((name, get_stream_from_channel_id(channel_id)))

        # Duplicati
        name_counts = {}
        for name, _ in channels_247: name_counts[name] = name_counts.get(name,0)+1
        final_channels = []
        name_counter = {}
        for name, url in channels_247:
            if name_counts[name] > 1:
                if name not in name_counter: name_counter[name]=1; final_channels.append((name,url))
                else: name_counter[name]+=1; final_channels.append((f"{name} ({name_counter[name]})",url))
            else: final_channels.append((name,url))
        channels_247 = sorted(final_channels,key=lambda x:x[0].lower())
        print(f"Trovati {len(channels_247)} canali 24/7")
    except Exception as e:
        print(f"Errore 24/7: {e}")
        channels_247 = []

    # Live eventi
    live_events=[]
    if os.path.exists(JSON_FILE):
        try:
            now=datetime.now()
            yesterday_date=(now - timedelta(days=1)).date()
            with open(JSON_FILE,"r",encoding="utf-8") as f: data=json.load(f)
            categorized_channels={}
            for date_key,sections in data.items():
                date_part=date_key.split(" - ")[0]
                try: date_obj=parser.parse(date_part,fuzzy=True).date()
                except: continue
                process_this_date=date_obj==now.date() or date_obj==yesterday_date
                early_morning_check=date_obj==yesterday_date
                if not process_this_date: continue
                for category_raw,event_items in sections.items():
                    category=re.sub(r'<[^>]+>','',category_raw).strip()
                    if category.lower()=="tv shows": continue
                    if category not in categorized_channels: categorized_channels[category]=[]
                    for item in event_items:
                        time_str=item.get("time","00:00")
                        event_title=item.get("event","Evento")
                        try:
                            t_obj=datetime.strptime(time_str,"%H:%M").time()
                            dt=datetime.combine(date_obj,t_obj)
                            if early_morning_check:
                                if not(datetime.strptime("00:00","%H:%M").time()<=t_obj<=datetime.strptime("04:00","%H:%M").time()): continue
                            else:
                                if now-dt>timedelta(hours=2): continue
                            time_formatted=dt.strftime("%H:%M")
                        except: time_formatted=time_str
                        for ch in item.get("channels",[]):
                            channel_id=ch.get("channel_id","")
                            tvg_name=f"{event_title} ({time_formatted})"
                            categorized_channels.setdefault(category,[]).append({"tvg_name":tvg_name,"channel_id":channel_id})
            for category,channels in categorized_channels.items():
                for ch in channels:
                    try:
                        stream=get_stream_from_channel_id(ch["channel_id"])
                        if stream: live_events.append((f"{category} | {ch['tvg_name']}",stream))
                    except: continue
            print(f"Trovati {len(live_events)} eventi live")
        except Exception as e: print(f"Errore eventi live: {e}")

    # M3U
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        if live_events:
            f.write('#EXTINF:-1 group-title="Live Events",DADDYLIVE\nhttps://example.com.m3u8\n\n')
            for name,url in live_events: f.write(f'#EXTINF:-1 group-title="Live Events",{name}\n{url}\n\n')
        if channels_247:
            for name,url in channels_247: f.write(f'#EXTINF:-1 group-title="DLHD 24/7",{name}\n{url}\n\n')
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Creato file {OUTPUT_FILE}")

if __name__=="__main__":
    dlhd()