import requests

# Birleştirmek istediğin M3U dosyalarının URL'leri
m3u_urls = [
    "https://raw.githubusercontent.com/Love4vn/love4vn/refs/heads/main/Grab_VTV.m3u",
    "https://raw.githubusercontent.com/t23-02/bongda/refs/heads/main/bongda.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u",
    "http://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Love4vn/love4vn/refs/heads/main/IPTV_CXT.m3u",
]

# Çıktı dosyası adı
output_file = "yabanci.m3u"

# M3U başlığı
merged_content = "#EXTM3U\n"

for url in m3u_urls:
    try:
        print(f"İndiriliyor: {url}")
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        # Başlık satırını (eğer varsa) çıkarıyoruz
        if content.startswith("#EXTM3U"):
            content = content.split("\n", 1)[1]

        merged_content += content.strip() + "\n"

    except Exception as e:
        print(f"Hata oluştu: {url}\n{e}")

# Birleştirilmiş içeriği dosyaya yaz
with open(output_file, "w", encoding="utf-8") as f:
    f.write(merged_content)

print(f"\nBirleştirme tamamlandı: {output_file}")
