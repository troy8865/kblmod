import requests
import yaml
import sys
import re

# --- Yardımcı Fonksiyonlar ---

def load_config(config_path='config.yml'):
    """
    config.yml dosyasını okur ve ayarları bir sözlük olarak döndürür.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"HATA: Yapılandırma dosyası bulunamadı: '{config_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"HATA: Yapılandırma dosyası okunurken bir hata oluştu: {e}")
        sys.exit(1)

def fetch_playlist(url):
    """
    Verilen URL'den M3U listesinin içeriğini indirir.
    """
    try:
        print(f"Kaynak liste indiriliyor: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        # Kaynak dosyanın UTF-8 olduğundan emin olalım
        response.encoding = 'utf-8'
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"HATA: Kaynak liste indirilemedi: {e}")
        sys.exit(1)

def parse_source_playlist(source_content):
    """
    Kaynak M3U içeriğini analiz eder ve yapılandırılmış bir kanal listesi döndürür.
    Bu fonksiyon, formatlama hatalarına karşı daha dayanıklıdır.
    """
    print("\n--- Kaynak Liste Analiz Ediliyor (Geliştirilmiş Yöntem) ---")
    channels = []
    lines = source_content.splitlines()
    
    # Geçici olarak bir önceki #EXTINF satırını saklamak için
    last_extinf = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('#EXTINF:'):
            # Bir kanal bilgi satırı bulduk, bunu sakla
            last_extinf = line
        elif last_extinf and not line.startswith('#'):
            # Bu satır bir URL ve bir önceki satır #EXTINF bilgisi içeriyor.
            # Bu, geçerli bir kanal demektir.
            
            # Grup adını bul
            group_title = "GRUPSUZ KANALLAR"
            match = re.search(r'group-title=(["\'])(.*?)\1', last_extinf, re.IGNORECASE)
            if match:
                title = match.group(2).strip()
                if title:
                    group_title = title
            
            # Kanal objesini listeye ekle
            channels.append({
                'group': group_title,
                'extinf': last_extinf,
                'url': line
            })
            
            # Bu bilgiyi kullandığımız için sıfırla, böylece aynı kanalı tekrar eklemeyiz
            last_extinf = None

    print(f"\nAnaliz tamamlandı. Toplam {len(channels)} kanal bulundu.")
    if len(channels) == 0:
        print("UYARI: Kaynak listeden hiç kanal ayrıştırılamadı. Lütfen kaynak URL'yi ve içeriğini kontrol edin.")
    return channels

def build_new_playlist(channels, base_url):
    """
    Yapılandırılmış kanal listesini kullanarak yeni M3U içeriğini oluşturur.
    Grupları sıralar ve Türk gruplarını başa alır.
    """
    if not channels:
        return "#EXTM3U\n# UYARI: İşlenecek hiç kanal bulunamadı."

    print("\n--- Yeni Liste Oluşturuluyor ve Sıralanıyor ---")
    
    # Kanalları önce grup adına, sonra kanal adına göre sırala
    channels.sort(key=lambda x: (x['group'].lower(), x['extinf'].lower()))

    turkish_channels = []
    other_channels = []

    for channel in channels:
        group_lower = channel['group'].lower()
        if 'türk' in group_lower or 'turk' in group_lower:
            turkish_channels.append(channel)
        else:
            other_channels.append(channel)

    print(f"Türk kanalları içeren gruplar başa alınıyor.")
    
    output_lines = ['#EXTM3U']
    
    # Önce Türk kanallarını ekle
    for channel in turkish_channels:
        output_lines.append(channel['extinf'])
        new_url = f"{base_url.rstrip('/')}/{channel['url']}/index.m3u8"
        output_lines.append(new_url)
        
    # Sonra diğer kanalları ekle
    for channel in other_channels:
        output_lines.append(channel['extinf'])
        new_url = f"{base_url.rstrip('/')}/{channel['url']}/index.m3u8"
        output_lines.append(new_url)
        
    return "\n".join(output_lines)

def save_playlist(content, output_file):
    """
    Oluşturulan yeni M3U içeriğini dosyaya kaydeder.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\nİşlem başarıyla tamamlandı!")
        print(f"Yeni liste '{output_file}' adıyla kaydedildi.")
    except IOError as e:
        print(f"HATA: Sonuç dosyası yazılamadı: {e}")
        sys.exit(1)

# --- Ana Fonksiyon ---
def main():
    config = load_config()
    source_content = fetch_playlist(config['source_playlist_url'])
    channels_list = parse_source_playlist(source_content)
    new_playlist_content = build_new_playlist(channels_list, config['base_url'])
    save_playlist(new_playlist_content, config['output_file'])

if __name__ == "__main__":
    main()