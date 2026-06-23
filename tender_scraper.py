import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import json
from google import genai
from google.genai import types

# API KEY
client = genai.Client(api_key="PLACE YOUR API KEY HERE")

profil_klasoru = os.path.join(os.getcwd(), "Bot_Profili")
yedek_dosya = "veri_yedek.json" # Backup json file

options = uc.ChromeOptions()
options.add_argument(f"--user-data-dir={profil_klasoru}")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-popup-blocking")

driver = uc.Chrome(options=options, version_main=149) ## IMPORTANT: As Chrome updates, you must update this value to match your current browser version (e.g., 149, 150).
veri_listesi = []

# Continue from the completed part (checkpoint)
if os.path.exists(yedek_dosya):
    try:
        with open(yedek_dosya, "r", encoding="utf-8") as f:
            veri_listesi = json.load(f)
        print(f"\nÖnceki seansından kalan {len(veri_listesi)} ihale verisi yüklendi.")
    except:
        pass

# AI Prompt
system_prompt = """
Sen bir veri düzenleme asistanısın. Sana verilen ihale başlığı ve detay metninden şu anahtarlara sahip bir JSON dizisi (Array of Objects) oluşturmalısın:
"İhale Kategorisi", "İhaleyi Veren Kamu Kurumu", "İhale Adı", "Konum", "İhale Durumu", "Tarih", "İhale Fiyatı", "İhaleye Giren Şirket", "Paydaşlar", "Paydaşlık Biçimi".

KURALLAR:
1. SADECE 'İhale Adı' değerindeki Türkçe ve şapkalı karakterleri İngilizce karakterlere dönüştür (ç->c, ğ->g, ı->i, ö->o, ş->s, ü->u, Ç->C, Ğ->G, İ->I, Ö->O, Ş->S, Ü->U, â->a, Â->A, î->i, Î->I, û->u, Û->U). Diğer hiçbir alana dokunma.
2. İş ortaklığı/konsorsiyum (örn: X Şirketi-Y Şirketi) varsa, her şirketi JSON dizisinde ayrı bir obje (ayrı satır) olarak oluştur. İhaleyi bölüp farklı kısımlarını alanları değil, aynı ihaleye bölmeden ortaklaşa girenleri paydaş say. 'Paydaşlar' kısmına diğer ortağın adını, 'Paydaşlık Biçimi'ne ise ortaklığın tipini yaz.
3. Metinde yer alan "Aboneye Özel" vb. site uyarılarını ASLA veri olarak alma. "İhale Durumu" sadece mantıklı süreçler (Sonuçlandı, İptal, vs.) olmalıdır. Eğer bir bilgi yoksa veya paywall engeli varsa o alanlara boşluk bırakmak yerine sadece "-" karakterini koy.
4. Çıktı SADECE geçerli bir JSON dizisi (Array) olmalıdır. Altına veya üstüne başka hiçbir açıklama ekleme.
"""

try:
    login_url = "https://yatirimlar.com/login"
    driver.get(login_url)
    driver.maximize_window()

    print("\nTarayıcı açıldı, lütfen giriş yapınız.")
    input("Girişten sonra ENTER'a basarak işleme başlayabiliriz...")
    print("\nScraping'e başlıyoruz...")

    aranacak_kategoriler = ["Etüt", "Yapım", "Makine", "İşletme", "Yurt Dışı"]

    ana_sekme = driver.window_handles[0]
    driver.execute_script("window.open('about:blank', '_blank');")
    time.sleep(1)
    detay_sekmesi = driver.window_handles[-1] 

    for kat_kelime in aranacak_kategoriler:
        driver.switch_to.window(ana_sekme)
        print(f"\n--- Sıradaki: {kat_kelime} İhaleleri ---")
        
        driver.get("https://yatirimlar.com/")
        time.sleep(2)

        edergi_linki = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'E-DERGİ') or contains(text(), 'E-Dergi')]"))
        )
        driver.execute_script("arguments[0].click();", edergi_linki)
        time.sleep(3)

        dergi_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "selectDergi"))
        )
        Select(dergi_dropdown).select_by_value("1161") # Magazine Issue Number (1791) [Magazine Issue Number = Option Value + 630]
        time.sleep(4) 

        ilk_filtre_linki = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='#collapseFilter']"))
        )
        driver.execute_script("arguments[0].click();", ilk_filtre_linki)
        time.sleep(2) 

        kategori_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "kat")) 
        )
        select_kat = Select(kategori_dropdown)
        
        kat_bulundu = False
        for option in select_kat.options:
            if kat_kelime.lower() in option.text.lower():
                select_kat.select_by_value(option.get_attribute("value"))
                kat_bulundu = True
                print(f"'{option.text}' seçildi ")
                break
                
        if not kat_bulundu:
            print(f"Bu dergide '{kat_kelime}' ile ilgili bir kategori bulunamadı, diğerine geçiliyor...")
            continue

        time.sleep(1)

        mavi_filtre_butonu = driver.find_element(By.XPATH, "//button[contains(text(), 'Filtrele') and not(ancestor::a)]")
        driver.execute_script("arguments[0].click();", mavi_filtre_butonu)
        print("Arama başlatıldı, sonuçlar alınıyor...")

        sayfa_sayisi = 1
        
        while True:
            driver.switch_to.window(ana_sekme) 
            print(f"\n--- {kat_kelime} İhaleleri / {sayfa_sayisi}. sayfanın içindeyiz ---")
            
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h4 a.title"))
                )
            except Exception:
                print(f"Bu sayfada {kat_kelime} ihalesi bulunamadı veya sona gelindi")
                break

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            ihale_linkleri = []
            
            for a in soup.select('h4 a.title'):
                if 'href' in a.attrs:
                    link = a['href']
                    if not link.startswith("http"):
                        link = "https://yatirimlar.com" + link
                    if link not in ihale_linkleri:
                        ihale_linkleri.append(link)

            print(f"Toplam {len(ihale_linkleri)} ihale bulundu. AI ile analiz ediliyor...")
            
            for i, link in enumerate(ihale_linkleri):
                driver.switch_to.window(detay_sekmesi)
                driver.get(link)
                
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".post_details_block"))
                    )
                except:
                    continue
                
                detay_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                baslik = detay_soup.find('h2', class_='title').text.strip() if detay_soup.find('h2', class_='title') else "-"
                post_block = detay_soup.find(class_='post_details_block')
                tam_metin = post_block.get_text(separator=' ').strip() if post_block else "-"
                
                kategoriler = [li.text.strip() for li in detay_soup.select('ul.authar-info li span.post-category')]
                varsayilan_kategori = f"{kat_kelime.title()} İhaleleri"
                ihale_kategorisi = kategoriler[0] if len(kategoriler) > 0 else varsayilan_kategori

                # --- AI Integration ---
                istek_metni = f"{system_prompt}\n\nİhale Kategorisi: {ihale_kategorisi}\nİhale Başlığı: {baslik}\nİhale Metni: {tam_metin}"
                
                basarili = False
                deneme = 0
                max_deneme = 5
                
                while not basarili and deneme < max_deneme:
                    try:
                        response = client.models.generate_content(
                            # AI Model Name
                            model='gemini-2.5-flash', 
                            contents=istek_metni,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            )
                        )
                        ai_verisi = json.loads(response.text)
                        
                        if isinstance(ai_verisi, list):
                            veri_listesi.extend(ai_verisi)
                        else:
                            veri_listesi.append(ai_verisi)
                            
                        # CHECKPOINT
                        with open(yedek_dosya, "w", encoding="utf-8") as f:
                            json.dump(veri_listesi, f, ensure_ascii=False, indent=4)
                            
                        print(f"{i+1}. ihale deftere (ve yedeğe) yazıldı. ")
                        basarili = True  
                        
                    except Exception as e:
                        deneme += 1
                        bekleme_suresi = deneme * 5 
                        if deneme < max_deneme:
                            print(f"{i+1}. ihalede takılındı (Nedeni: {e}). {bekleme_suresi} saniye bekleyip tekrar deneniyor... ({deneme}/{max_deneme})")
                            time.sleep(bekleme_suresi)
                
                if not basarili:
                    print(f" {i+1}. ihale {max_deneme} denemeye rağmen aşılamadı, atlanıyor.")
                
                time.sleep(2)

            driver.switch_to.window(ana_sekme)
            time.sleep(2)
            
            try:
                sonraki_butonu = driver.find_element(By.XPATH, "//a[contains(@class, 'page-link') and text()='Sonraki']")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sonraki_butonu)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", sonraki_butonu)
                time.sleep(1)
                sayfa_sayisi += 1
                
            except Exception:
                print(f"\n{kat_kelime} sayfaları bitti.")
                break 

except Exception as e:
    print(f"\nBir problemle karşılaşıldı: {e} \nşu ana kadarki veriler '{yedek_dosya}' içine kayıtlı tutuluyor.")

finally:
    if veri_listesi:
        df = pd.DataFrame(veri_listesi)
        df.to_excel("yatirimlar-1791.xlsx", index=False) # Final excel files name (1791)
        print(f"\nToplam {len(veri_listesi)} teklif satırı Excel'e eklendi!")
    else:
        print("\nİşlem bitti fakat kaydedilecek veri bulunamadı.")
    
    try:
        driver.quit()
    except:
        pass
