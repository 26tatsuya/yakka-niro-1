import requests
import re
from bs4 import BeautifulSoup
import pandas as pd 
import numpy as np
import sqlite3

# 基本URLの設定
url = "https://yoga-lava.com/re_search/studio.html?code=7"

all_data = []

response = requests.get(url)
soup = BeautifulSoup(response.content, 'lxml')
items = soup.findAll(class_="shopList")

for item in items:
    base_data = {}

    tbodys = item.findAll("dl")

    for tbody in tbodys:
        data = base_data.copy()

        shop_name_element = tbody.select_one('a', href=re.compile(r'^/tokyo/[^/]+/$'))
        data["店舗名"]  = shop_name_element.get_text(strip=True) if shop_name_element else None

        data["住所"]    = tbody.select_one('p').get_text(strip=True) if tbody.select_one('p') else None


        link_elements = tbody.select_one('a', href=re.compile(r'^/tokyo/[^/]+/$'))
        base_url = "https://yoga-lava.com"
        data["リンク"]  = base_url + link_elements['href']

        all_data.append(data)

df = pd.DataFrame(all_data)


# 郵便番号を削除する関数
def remove_postal_code(address):
    return re.sub(r'〒\d{3}[-‐]\d{4}', '', address).strip()

# 住所から郵便番号を削除
df['住所'] = df['住所'].apply(remove_postal_code)


# 国土地理院APIのURL
url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="

# 住所から緯度経度を取得する関数
def get_lat_lon(address):
    try:
        res = requests.get(url + address)
        res.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
        data = res.json()
        if data and len(data) > 0:
            location = data[0]['geometry']['coordinates']
            return location[1], location[0]  # 緯度、経度を返す
        else:
            return None, None
    except Exception as e:
        print(f"Error retrieving location for address {address}: {e}")
        return None, None

# 緯度経度の取得とデータフレームへの保存
df[['緯度', '経度']] = df['住所'].apply(lambda x: pd.Series(get_lat_lon(x)))


# 住所から「〇〇区」を抽出する関数
def extract_ku(address):
    match = re.search(r'東京都(\w+区)', address)
    return match.group(1) if match else None

# 新しいカラム「区」を作成
df['区'] = df['住所'].apply(extract_ku)

# データベース接続を作成
conn = sqlite3.connect('property.db')

# データフレームをSQLiteテーブルに変換
df.to_sql('LAVA', conn, if_exists='replace', index=False)

conn.close()