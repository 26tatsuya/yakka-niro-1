import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 環境変数から認証情報を取得
API_KEY = os.getenv("Google_geocoding_API")

base_url = "https://www.homes.co.jp/chintai/tokyo/minato-city/list/?page={}"
max_page = 5
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

all_data = []

for page in range(1, max_page + 1):
    url = base_url.format(page)
    response = requests.get(url, headers=headers) 
    soup = BeautifulSoup(response.content, 'lxml')
    items = soup.findAll("div", {"class": "mod-mergeBuilding--rent--photo"})

    print("page", page, "items", len(items))

    for item in items:
        base_data = {}
        base_data["名称"] = item.find(class_="bukkenName").get_text(strip=True) if item.find(class_="bukkenName") else None
        base_data["アドレス"] = next((td.find_next_sibling('td').get_text(strip=True) for td in item.find_all('th') if td.get_text(strip=True) == '所在地'), None)
        base_data["アクセス"] = item.find("td", class_="traffic").get_text(strip=True) if item.find("td", class_="traffic") else ', '.join(span.get_text(strip=True) for span in item.find_all("span", class_="prg-stationText"))
        module_body = item.find('div', class_='moduleBody')
        if module_body:
            construction_th = module_body.find('th', string='築年数/階数')
            if construction_th:
                base_data["築年数"] = construction_th.find_next_sibling('td').get_text(strip=True).split(' ')[0]
                base_data["構造"] = construction_th.find_next_sibling('td').get_text(strip=True).split(' ')[2]

        rooms = item.find_all(class_="unitListBody prg-unitListBody")
        for room in rooms:
            data = base_data.copy()
            
            # 当該部屋の階数
            floor_number_td = room.find(class_="roomKaisuu")
            data["階数"] = floor_number_td.get_text(strip=True) if floor_number_td else None

            # 賃料と管理費を分けて取得
            rent_price_label = room.select_one("span.priceLabel")
            rent_price = rent_price_label.get_text(strip=True) if rent_price_label else None
            rent_admin = rent_price_label.next_sibling.strip().replace("/", "").replace(",", "") if rent_price_label else None
            data["家賃"] = rent_price
            data["管理費"] = rent_admin

            # 敷金と礼金を分けて取得
            price = room.select_one("td.price")
            br_tag = price.find('br').next_sibling.strip()
            depo = br_tag.split("/")[0]
            key = br_tag.split("/")[1]
            data["敷金"] = depo
            data["礼金"] = key

            # 間取りと占有面積を分けて取得
            layout = room.select_one("td.layout")
            room_type = layout.contents[0].strip() if layout.contents else None
            room_area = layout.find('br').next_sibling.strip().replace('m²', 'm2') if layout.find('br') else None
            data["間取り"] = room_type
            data["面積"] = room_area

            property_image_element = item.select_one(".bukkenPhoto .photo img")
            data["物件画像URL"] = property_image_element["data-original"] if property_image_element else None

            # 間取り画像URL
            floor_plan_image_element = item.select_one(".floarPlanPic img")
            data["間取画像URL"] = floor_plan_image_element["data-original"] if floor_plan_image_element else None

            # 物件詳細URL
            property_link_element = item.select_one("a[href*='/chintai/room']")
            data["物件詳細URL"] = property_link_element['href'] if property_link_element else None


            all_data.append(data)

df = pd.DataFrame(all_data)

# 住所の標準化関数
def standardize_address(address):
    # 数字を半角から全角に変換
    address = re.sub(r'1', '１', address)
    address = re.sub(r'2', '２', address)
    address = re.sub(r'3', '３', address)
    address = re.sub(r'4', '４', address)
    address = re.sub(r'5', '５', address)
    address = re.sub(r'6', '６', address)
    address = re.sub(r'7', '７', address)
    address = re.sub(r'8', '８', address)
    address = re.sub(r'9', '９', address)
    address = re.sub(r'0', '０', address)
    
    # 「丁目」以降を削除
    address = re.sub(r'丁目.*', '', address)
    address = re.sub(r'-.*', '', address)
    
    return address

# 標準化した住所を新しいカラムに追加
df['アドレス'] = df['アドレス'].apply(standardize_address)

#数字を除去した住所をアドレス_数字除去に格納
def remove_numbers(address):
    # 数字を削除
    address_no_numbers = re.sub(r'[0-9０-９]', '', address)
    return address_no_numbers

# 数字を削除した住所を新しいカラムに追加
df['アドレス_数字除去'] = df['アドレス'].apply(remove_numbers)


# 基本URLと最大ページ数の設定
base_url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&pc=30&smk=&po1=25&po2=99&shkr1=03&shkr2=03&shkr3=03&shkr4=03&sc=13103&sc=13113&sc=13109&sc=13111&ta=13&cb=0.0&ct=9999999&et=9999999&mb=0&mt=9999999&cn=30&fw2="
max_page = 5  # 最大ページ数

all_data = []

for page in range(1, max_page + 1):
    url = base_url.format(page)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    items = soup.findAll("div", {"class": "cassetteitem"})


    print("page", page, "items", len(items))

    for item in items:
        base_data = {}
        base_data["名称"]     = item.find("div", {"class": "cassetteitem_content-title"}).get_text(strip=True) if item.find("div", {"class": "cassetteitem_content-title"}) else None
        base_data["カテゴリ"] = item.find("div", {"class": "cassetteitem_content-label"}).span.get_text(strip=True) if item.find("div", {"class": "cassetteitem_content-label"}) else None
        base_data["アドレス"] = item.find("li", {"class": "cassetteitem_detail-col1"}).get_text(strip=True) if item.find("li", {"class": "cassetteitem_detail-col1"}) else None
        
        # 駅のアクセス情報をまとめて取得
        base_data["アクセス"] = ", ".join([station.get_text(strip=True) for station in item.findAll("div", {"class": "cassetteitem_detail-text"})])

        construction_info = item.find("li", {"class": "cassetteitem_detail-col3"}).find_all("div") if item.find("li", {"class": "cassetteitem_detail-col3"}) else None
        base_data["築年数"] = construction_info[0].get_text(strip=True) if construction_info and len(construction_info) > 0 else None
        base_data["構造"] = construction_info[1].get_text(strip=True) if construction_info and len(construction_info) > 1 else None

        tbodys = item.find("table", {"class": "cassetteitem_other"}).findAll("tbody")

        for tbody in tbodys:
            data = base_data.copy()
            # 階数情報の正確な取得
            floor_info = tbody.find_all("td")[2].get_text(strip=True) if len(tbody.find_all("td")) > 2 else None
            data["階数"]   = floor_info
            data["家賃"]   = tbody.select_one(".cassetteitem_price--rent").get_text(strip=True) if tbody.select_one(".cassetteitem_price--rent") else None
            data["管理費"] = tbody.select_one(".cassetteitem_price--administration").get_text(strip=True) if tbody.select_one(".cassetteitem_price--administration") else None
            data["敷金"]   = tbody.select_one(".cassetteitem_price--deposit").get_text(strip=True) if tbody.select_one(".cassetteitem_price--deposit") else None
            data["礼金"]   = tbody.select_one(".cassetteitem_price--gratuity").get_text(strip=True) if tbody.select_one(".cassetteitem_price--gratuity") else None
            data["間取り"] = tbody.select_one(".cassetteitem_madori").get_text(strip=True) if tbody.select_one(".cassetteitem_madori") else None
            data["面積"]   = tbody.select_one(".cassetteitem_menseki").get_text(strip=True) if tbody.select_one(".cassetteitem_menseki") else None

            # 物件画像・間取り画像・詳細URLの取得を最後に行う
            property_image_element = tbody.find(class_="cassetteitem_object-item")
            data["物件画像URL"] = property_image_element.img["rel"] if property_image_element and property_image_element.img else None

            floor_plan_image_element = tbody.find(class_="casssetteitem_other-thumbnail")
            data["間取画像URL"] = floor_plan_image_element.img["rel"] if floor_plan_image_element and floor_plan_image_element.img else None

            property_link_element = tbody.select_one("a[href*='/chintai/jnc_']")
            data["物件詳細URL"] = "https://suumo.jp" +property_link_element['href'] if property_link_element else None ## 不動産サイトから詳細URLリンクを読み解き作成

            all_data.append(data)

df2 = pd.DataFrame(all_data)

#数字を除去した住所をアドレス_数字除去に格納
def remove_numbers(address):
    # 数字を削除
    address_no_numbers = re.sub(r'[0-9０-９]', '', address)
    return address_no_numbers

# 数字を削除した住所を新しいカラムに追加
df2['アドレス_数字除去'] = df2['アドレス'].apply(remove_numbers)

df2_cleaned = df2.drop(columns=['カテゴリ'])

df_merged = pd.concat([df, df2_cleaned], ignore_index=True)

# 重複削除
df_deduplicated = df_merged.drop_duplicates(subset=['築年数', '構造', '階数', '家賃', '面積', 'アドレス_数字除去'])

# 削除前後の行数を比較
original_count = len(df_merged)
deduplicated_count = len(df_deduplicated)
duplicates_removed = original_count - deduplicated_count

# 結果の表示
print(f"\n削除された重複レコード数: {duplicates_removed}")

df_deduplicated = df_deduplicated.drop(columns=['アドレス_数字除去'])

# 「家賃」列から万円を削除してobject→floatに変換
# 変換後に再度データを格納
def extract_number(x):
    try:
        return float(x.split('万円')[0].replace(',',''))
    except:
        return np.nan

df_deduplicated['家賃'] = df_deduplicated['家賃'].apply(extract_number).astype(float)

# 東京都を削除して新しい列を作成
df_deduplicated['アドレス_修正'] = df_deduplicated['アドレス'].str.replace('東京都', '')

# 区の後の文字を削除して新しい列を作成
df_deduplicated['区'] = df_deduplicated['アドレス_修正'].str.split('区', expand=True)[0]+ '区'

# df_deduplicatedから[アドレス_修正]を削除
df_deduplicated = df_deduplicated.drop(columns=['アドレス_修正'])

# Google geocoding APIを使って「名称」（物件名）から緯度経度を算出
def get_geocode_from_name(name):
    address = name.replace(" ", "+")  # 空白をプラスに置き換える
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data["status"] == "OK":
        location = data["results"][0]["geometry"]["location"]
        lat = location["lat"]
        lng = location["lng"]
        return lat, lng
    else:
        return None, None


# 緯度経度の取得と格納
df_deduplicated['緯度'] = df_deduplicated['名称'].apply(lambda x: get_geocode_from_name(x)[0])
df_deduplicated['経度'] = df_deduplicated['名称'].apply(lambda x: get_geocode_from_name(x)[1])

# データベース接続を作成
conn = sqlite3.connect('property.db')

# データフレームをSQLiteテーブルに変換
df_deduplicated.to_sql('SUUMOHOMES', conn, if_exists='replace', index=False)

conn.close()