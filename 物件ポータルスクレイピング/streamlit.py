import os
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static

# セッション状態の初期化
if 'show_all' not in st.session_state:
    st.session_state['show_all'] = False #初期状態は地図状態の物件のみを表示

# 地図上以外の物件も表示するボタンの状態を切り替える関数
def toggle_show_all():
    st.session_state['show_all'] = not st.session_state['show_all']

# SQLiteからデータを読み込む関数
db_path = 'property.db'
query = 'SELECT * FROM SUUMOHOMES'
def read_data_from_sqlite(db_path='property.db', query='SELECT * FROM SUUMOHOMES'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    # SQLiteの結果をDataFrameに変換
    rows = pd.DataFrame(rows,columns=[desc[0] for desc in c.description])
    return rows

# 地図を作成、マーカーを追加する関数
def create_map(filtered_rows):
    # 地図の初期設定
    map_center = [filtered_rows['緯度'].mean(), filtered_rows['経度'].mean()]
    m = folium.Map(location = map_center, zoom_start=12)

    #マーカーを追加
    for idx, row in filtered_rows.iterrows():
        if (filtered_rows['緯度'].notnull()).any() and (filtered_rows['経度'].notnull()).any():
            # ポップアップに表示するHTMLコンテンツを作成
            popup_html = f"""
            <b>名称:</b> {row['名称']}<br>
            <b>アドレス:</b> {row['アドレス']}<br>
            <b>家賃:</b> {row['家賃']}<br>
            <a href="{row['物件詳細URL']}" target="_blank">物件詳細</a>
            """

            # HTMLをポップアップに設定
            popup = folium.Popup(popup_html, max_width=400)
            folium.Marker(
                [row['緯度'], row['経度']],
                popup = popup
            ).add_to(m)
    
    return m

# 検索結果を表示する関数
def display_search_results(filtered_rows):
    # 物件番号を含む新しい列を作成
    filtered_rows['物件番号'] = range(1, len(filtered_rows)+1)
    filtered_rows['物件詳細URL'] = '[リンク](' + filtered_rows['物件詳細URL'] + ')'
    display_columns = ['物件番号','名称','アドレス','階数', '家賃', '間取り','物件詳細URL']
    filtered_rows_display = filtered_rows[display_columns]
    st.markdown(filtered_rows_display.to_html(escape=False, index=False), unsafe_allow_html=True)

# メインのアプリケーション
def main():
    rows = read_data_from_sqlite()

    # StreamlitのUI要素（スライダー、ボタンなど）の各表示設定
    st.title('賃貸物件情報の可視化')

    # エリアと家賃フィルターバーを1:2の割合で分割
    col1, col2 = st.columns([1,2])

    with col1:
        # エリア選択
        area = st.radio('■ エリア選択', ["港区","渋谷区","品川区","大田区"])
    
    with col2:
        # 家賃範囲選択のスライダーをfloat型せ設定し、小数点第一位まで表示
        price_min, price_max = st.slider(
            '■ 家賃範囲（万円）',
            min_value=float(1),
            max_value=float(rows['家賃'].max()),
            value=(float(rows['家賃'].min()), float(rows['家賃'].max())),
            step=0.1,
            format='%.1f'
        )

    with col2:
        # 間取り選択のデフォルト値をすべてに設定
        type_options = st.multiselect('■ 間取り選択', rows['間取り'].unique(), default=rows['間取り'].unique())
    
    # フィルタリング/フィルタリングされたデータフレームの件数を取得
    filtered_rows = rows[(rows['区'].isin([area])) & (rows['間取り'].isin(type_options))]
    filtered_rows = filtered_rows[(filtered_rows['家賃'] >= price_min) & (filtered_rows['家賃'] <= price_max)]
    filtered_count = len(filtered_rows)

    # 'latitude'と'longitude'列を数値型に変換し、NaN値を含む行を削除
    filtered_rows['緯度'] = pd.to_numeric(filtered_rows['緯度'], errors='coerce')
    filtered_rows['経度'] = pd.to_numeric(filtered_rows['経度'], errors='coerce')
    filtered_rows2 = filtered_rows.dropna(subset=['緯度', '経度'])


    # 検索ボタン/ フィルタリングされたデータフレーム件数を表示
    col2_1, col2_2 = st.columns([1,2])

    with col2_2:
        st.write(f"物件検索数: {filtered_count}件 / 全{len(rows)}件")
    
    # 検索ボタン
    if col2_1.button('検索&更新', key='search_button'):
        # 検索ボタンが押された場合、セッションステートに結果を保存
        st.session_state['filtered_rows'] = filtered_rows
        st.session_state['filtered_rows2'] = filtered_rows2
        st.session_state['search_clicked'] = True
    
    # streamlitに地図を表示
    if st.session_state.get('search_clicked', False):
        m = create_map(st.session_state.get('filtered_rows2', filtered_rows2))
        folium_static(m)

    # 地図の下にラジオボタンを配置し、選択したオプションに応じて表示を切り替える
    show_all_option = st.radio(
        "表示オプションを選択してください:",
        ('地図上の検索物件のみ', 'すべての検索物件'),
        index=0 if not st.session_state.get('show_all', False) else 1,
        key='show_all_option'
    )

    # ラジオボタンの選択に応じてセッションステートを更新
    st.session_state['show_all'] = (show_all_option == 'すべての検索物件')

    # 検索結果の表示
    if st.session_state.get('search_clicked', False):
        if st.session_state['show_all']:
            display_search_results(st.session_state.get('filtered_rows', filtered_rows)) #全データ
        else:
            display_search_results(st.session_state.get('filtered_rows2', filtered_rows2)) #地図上の物件のみ

# アプリケーションの実行
if __name__ == "__main__":
    if 'search_clicked' not in st.session_state:
        st.session_state['search_clicked'] = False
    if 'show_all' not in st.session_state:
        st.session_state['show_all'] = False
    main()