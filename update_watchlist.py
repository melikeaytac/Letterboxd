import requests
from bs4 import BeautifulSoup
import time
import csv
import json
import re
import os

def scrape_and_update(username):
    csv_filename = f"{username}_watchlist_detayli.csv"
    js_filename = "movies-data.js"
    
    # 1. ESKİ JS VERİLERİNİ SÖZLÜK (DICTIONARY) OLARAK OKU
    # Böylece eski özetleri ve kelimeleri asla kaybetmeyiz
    old_js_data = {}
    if os.path.exists(js_filename):
        with open(js_filename, 'r', encoding='utf-8') as f:
            js_content = f.read().replace('window.MOVIES =', '').strip()
            if js_content.endswith(';'):
                js_content = js_content[:-1]
            try:
                js_movies = json.loads(js_content)
                for m in js_movies:
                    title = m.get('title', '')
                    if title:
                        old_js_data[title] = m
            except Exception as e:
                print("JS okuma hatası:", e)

    print(f"Hafıza yüklendi: Sistemdeki JS dosyasında {len(old_js_data)} film var.")
    print("Letterboxd taranıyor (Silinenler ayıklanacak, yeniler eklenecek)...\n")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    page = 1
    new_js_movies = []
    new_csv_rows = []
    
    scraped_titles = set()
    yeni_eklenen_sayisi = 0

    while True:
        url = f"https://letterboxd.com/{username}/watchlist/page/{page}/"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            break
            
        soup = BeautifulSoup(response.text, "html.parser")
        lazy_posters = soup.find_all('div', attrs={"data-component-class": "LazyPoster"})
        
        if not lazy_posters:
            break 
            
        for comp in lazy_posters:
            raw_title = comp.get('data-item-name')
            if not raw_title:
                continue
            
            # Yılı ve Temiz İsmi Ayır
            match = re.search(r'(.*)\s\((\d{4})\)$', raw_title)
            if match:
                title = match.group(1).strip()
                year = match.group(2)
            else:
                title = raw_title.strip()
                year = "Bilinmiyor"

            scraped_titles.add(title)
            
            # Afiş URL'sini çöz
            img_url = "Afiş Bulunamadı"
            poster_data = comp.get('data-resolvable-poster-path')
            if poster_data:
                try:
                    data = json.loads(poster_data)
                    uid = data.get('postered', {}).get('uid', '').replace('film:', '')
                    slug = data.get('posteredBaseLink', '').strip('/').split('/')[-1]
                    cache_key = data.get('cacheBustingKey', '')
                    if uid and slug:
                        dir_path = "/".join(list(uid))
                        img_url = f"https://a.ltrbxd.com/resized/film-poster/{dir_path}/{uid}-{slug}-0-250-0-375-crop.jpg?v={cache_key}"
                except Exception:
                    pass
            
            # 1. YENİ CSV İÇİN LİSTEYE EKLE
            new_csv_rows.append([raw_title, img_url])

            # 2. YENİ JS İÇİN KONTROL ET VE EKLE
            if title in old_js_data:
                # Film zaten varsa eski bilgileri (kelime, özet) koru
                movie_obj = old_js_data[title]
                movie_obj['index'] = len(new_js_movies) + 1 # İndeksi sıraya göre düzelt
                movie_obj['posterUrl'] = img_url # Afiş linki değişmişse diye güncelle
                new_js_movies.append(movie_obj)
            else:
                # Tamamen yeni filmse
                new_js_movies.append({
                    "index": len(new_js_movies) + 1,
                    "title": title,
                    "year": year,
                    "keyword": "yeni film",
                    "summary": "yeni eklendi",
                    "posterUrl": img_url
                })
                yeni_eklenen_sayisi += 1
                print(f"  + YENİ EKLENDİ: {title} ({year})")
        
        page += 1
        time.sleep(1)

    # Letterboxd'da OLMAYAN ama sende OLAN filmleri tespit et (SİLİNENLER)
    silinenler = set(old_js_data.keys()) - scraped_titles

    # 4. GÜNCEL DOSYALARI KAYDETME (Tam üzerine yazma)
    # CSV Kayıt
    with open(csv_filename, "w", encoding="utf-8-sig", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Film Adı", "Poster URL"])
        for row in new_csv_rows:
            writer.writerow(row)

    # JS Kayıt
    with open(js_filename, "w", encoding="utf-8") as file:
        js_content = "window.MOVIES = " + json.dumps(new_js_movies, ensure_ascii=False, indent=2) + ";"
        file.write(js_content)
    
    print(f"\nSistem Senkronize Edildi!")
    print(f"Güncel Toplam Film: {len(new_js_movies)}")
    print(f"Eklenen: {yeni_eklenen_sayisi}")
    print(f"Silinen/İzlenen: {len(silinenler)}")
    
    if silinenler:
        print("Çıkarılan Filmler:", ", ".join(silinenler))

# Betiği başlat
scrape_and_update(username="tanjutan")