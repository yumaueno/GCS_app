import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# アプリタイトル
st.title("Google Search Console データ分析")

# サイドバーにファイルアップロードとドメイン入力の設定
st.sidebar.header("Google Search Console 設定")
uploaded_file = st.sidebar.file_uploader(
    "サービスアカウントJSONファイルをアップロードしてください", type="json"
)
st.sidebar.markdown("※JSONファイルの取得方法は[こちら](https://www.udemy.com/course/python-gsc/?referralCode=D7A6DCFFB71D0E39E121)の「Google Search ConsoleのAPIを使うための準備」部分を参考にしてください")
SITE_URL = st.sidebar.text_input(
    "ドメインを入力してください (例: https://www.example.com)"
)

# 日付範囲の選択
end_date = st.sidebar.date_input("終了日を選択", datetime.date.today())
start_date = st.sidebar.date_input(
    "開始日を選択", end_date - datetime.timedelta(days=90)
)

# セッションステートでデータ保持
if "df" not in st.session_state:
    st.session_state.df = None

# 集計開始ボタン
if uploaded_file and SITE_URL:
    if st.sidebar.button("分析開始"):
        try:
            # JSONファイルをロードし、認証情報をセット
            json_data = json.load(uploaded_file)
            credentials = service_account.Credentials.from_service_account_info(
                json_data,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
            service = build("searchconsole", "v1", credentials=credentials)

            request = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "dimension": ["query", "page"],
                "rowLimit": 25000,
                "startRow": 0
            }

            response = service.searchanalytics().query(siteUrl = SITE_URL, body=request).execute()

            rows = response.get("rows", [])
            data = []

            for row in rows:
                query = row["keys"][0]
                page = row["keys"][1]
                clicks = row["clicks"]
                impressions = row["impressions"]
                ctr = row["ctr"]
                position = row["position"]
                data.append([query, page, clicks, impressions, ctr, position])

            df = pd.DataFrame(data, columns=["query", "page", "clicks", "impressions", "ctr", "position"])

            # セッションにデータを保存
            st.session_state.df = df

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

# データが存在する場合、表示およびフィルタリング処理を実行
if st.session_state.df is not None:
    df = st.session_state.df

    # 全件データ表示
    st.header("全データの表示")
    st.write(df)

    # スライダーでフィルタリング条件を設定
    st.header("フィルタリング条件の設定")

    # impressions の範囲を1行で表示
    st.subheader("impressions の範囲")
    col1, col2 = st.columns(2)
    with col1:
        min_impressions = st.number_input(
            "impressions 以上",
            min_value=int(df["impressions"].min()),
            max_value=int(df["impressions"].max()),
            value=int(df["impressions"].min()),
        )
    with col2:
        max_impressions = st.number_input(
            "impressions 以下",
            min_value=int(df["impressions"].min()),
            max_value=int(df["impressions"].max()),
            value=int(df["impressions"].max()),
        )

    # clicks の範囲を1行で表示
    st.subheader("clicks の範囲")
    col3, col4 = st.columns(2)
    with col3:
        min_clicks = st.number_input(
            "clicks 以上",
            min_value=int(df["clicks"].min()),
            max_value=int(df["clicks"].max()),
            value=int(df["clicks"].min()),
        )
    with col4:
        max_clicks = st.number_input(
            "clicks 以下",
            min_value=int(df["clicks"].min()),
            max_value=int(df["clicks"].max()),
            value=int(df["clicks"].max()),
        )

    
    # position の範囲を1行で表示
    st.subheader("順位 (position) の範囲")
    col5, col6 = st.columns(2)
    with col5:
        min_position = st.number_input(
            "順位 以上",
            min_value=int(df['position'].min()),
            max_value=int(df['position'].max()),
            value=int(df['position'].min())
        )
    with col6:
        max_position = st.number_input(
            "順位 以下",
            min_value=int(df['position'].min()),
            max_value=int(df['position'].max()),
            value=int(df['position'].max())
        )

    # ctr の範囲を1行で表示
    st.subheader("ctr の範囲")
    col7, col8 = st.columns(2)
    with col7:
        min_ctr = st.number_input(
            "ctr 以上",
            min_value=float(df['ctr'].min()),
            max_value=float(df['ctr'].max()),
            value=float(df['ctr'].min()),
            step=0.01
        )
    with col8:
        max_ctr = st.number_input(
            "ctr 以下",
            min_value=float(df['ctr'].min()),
            max_value=float(df['ctr'].max()),
            value=float(df['ctr'].max()),
            step=0.01
        )


    # フィルタリング条件の適用
    filtered_df = df[
        (df["impressions"] >= min_impressions)
        & (df["impressions"] <= max_impressions)
        & (df["clicks"] >= min_clicks)
        & (df["clicks"] <= max_clicks)
        & (df["position"] >= min_position)
        & (df["position"] <= max_position)
        & (df["ctr"] >= min_ctr)
        & (df["ctr"] <= max_ctr)
    ]

    # フィルタリングされたデータの表示
    st.header("フィルタリングされたデータ")
    st.write(filtered_df)