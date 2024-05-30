import requests
import re
from bs4 import BeautifulSoup
import pandas as pd 
import numpy as np
import sqlite3


# 基本URLの設定
url = "https://www.anytimefitness.co.jp/kanto/tokyo/"

all_data = []

response = requests.get(url)
soup = BeautifulSoup(response.content, 'lxml')
items = soup.findAll("div", {"class": "areasort"})

for item in items:
    base_data = {}

    # 'areasort' クラスを持つ 'div' 要素内のすべての 'li' 要素を取得
    tbodys = item.findAll("li")

    for tbody in tbodys:
        data = base_data.copy()

        data["店舗名"] = tbody.select_one("p.name").get_text(strip=True) if tbody.select_one("p.name") else None
        data["住所"] = tbody.select_one("p.address").get_text(strip=True) if tbody.select_one("p.address") else None

        link_element = tbody.select_one('a', href=True)
        relative_url = link_element['href'] if link_element else None
        base_url = "https://www.anytimefitness.co.jp"
        data["リンク"] = base_url + relative_url if relative_url else None

        all_data.append(data)


df = pd.DataFrame(all_data)
df = df.dropna() # Noneデータの削除
df.reset_index(drop=True, inplace=True) # インデックスをリセット


# 郵便番号を削除する関数
def remove_postal_code(address):
    return re.sub(r'〒\d{3}[-‐]\d{4}', '', address).strip()

# 住所から郵便番号を削除
df['住所'] = df['住所'].apply(remove_postal_code)


# APIのURL
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
conn = sqlite3.connect('anytime.db')

# データフレームをSQLiteテーブルに変換
df.to_sql('anytime', conn, if_exists='replace', index=False)

conn.close()