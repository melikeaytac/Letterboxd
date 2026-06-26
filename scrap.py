import requests
from bs4 import BeautifulSoup
import time
import csv
import json

def scrape_watchlist(username, start_page, end_page):
    movies = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    print(f"{username} kullanıcısının watchlist'i ({start_page}-{end_page}. sayfalar) çekiliyor...\n")

    for page in range(start_page, end_page + 1):
        url = f"https://letterboxd.com/{username}/watchlist/page/{page}/"
        print(f"[{page}/{end_page}] Taranıyor: {url}")
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Hata: Sayfa {page} alınamadı! (Durum Kodu: {response.status_code})")
            break
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Sadece filmleri barındıran LazyPoster kapsayıcılarını buluyoruz
        lazy_posters = soup.find_all('div', attrs={"data-component-class": "LazyPoster"})
        
        if not lazy_posters:
            print("Bu sayfada film bulunamadı, listenin sonuna gelinmiş olabilir.")
            break 
            
        for comp in lazy_posters:
            title = comp.get('data-item-name')
            if not title:
                continue
            
            img_url = "Afiş Bulunamadı"
            
            # ASIL SİHİR BURADA: Letterboxd'ın gizlediği JSON formatındaki veriyi çekiyoruz
            poster_data = comp.get('data-resolvable-poster-path')
            
            if poster_data:
                try:
                    # Gizli veriyi Python sözlüğüne çevir
                    data = json.loads(poster_data)
                    
                    # Film ID'sini al (Örn: "film:41925" -> "41925")
                    uid = data.get('postered', {}).get('uid', '').replace('film:', '')
                    
                    # Film URL adını (slug) al (Örn: "/film/bad-biology/" -> "bad-biology")
                    slug = data.get('posteredBaseLink', '').strip('/').split('/')[-1]
                    
                    # Önbellek anahtarını al
                    cache_key = data.get('cacheBustingKey', '')
                    
                    if uid and slug:
                        # Letterboxd resim algoritması: ID'nin her rakamını slash ile ayır (41925 -> 4/1/9/2/5)
                        dir_path = "/".join(list(uid))
                        
                        # Hiçbir siteye istek atmadan GERÇEK resmi biz kendimiz string olarak birleştiriyoruz!
                        img_url = f"https://a.ltrbxd.com/resized/film-poster/{dir_path}/{uid}-{slug}-0-250-0-375-crop.jpg?v={cache_key}"
                except Exception as e:
                    pass
            
            movies.append({"title": title, "poster_url": img_url})
        
        # Sadece sayfa geçişlerinde ufak bir bekleme (Sunucuyu yormamak için)
        time.sleep(1)

    print(f"\nİşlem tamamlandı! Toplam {len(movies)} film çekildi.")
    
    # CSV Dosyasına Yazma
    dosya_adi = f"{username}_watchlist_detayli.csv"
    with open(dosya_adi, "w", encoding="utf-8-sig", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Film Adı", "Poster URL"]) 
        for movie in movies:
            writer.writerow([movie["title"], movie["poster_url"]])
            
    print(f"Veriler '{dosya_adi}' dosyasına kusursuz kaydedildi!")

# Betiği başlatıyoruz
scrape_watchlist(username="tanjutan", start_page=1, end_page=22)