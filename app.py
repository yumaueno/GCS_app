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
domain = st.sidebar.text_input(
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
if uploaded_file and domain:
    if st.sidebar.button("分析開始"):
        try:
            # JSONファイルをロードし、認証情報をセット
            json_data = json.load(uploaded_file)
            credentials = service_account.Credentials.from_service_account_info(
                json_data,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
            service = build("searchconsole", "v1", credentials=credentials)

            # データ取得関数
            def get_search_analytics(service, site_url, start_date, end_date):
                request = {
                    "startDate": str(start_date),
                    "endDate": str(end_date),
                    "dimensions": ["query", "page"],
                    "rowLimit": 25000,
                }
                response = (
                    service.searchanalytics()
                    .query(siteUrl=site_url, body=request)
                    .execute()
                )
                return response

            # データをAPIから取得
            data = get_search_analytics(service, domain, start_date, end_date)

            # データ整形
            if "rows" in data:
                rows = data["rows"]
                query_data = []
                for row in rows:
                    query = row["keys"][0]
                    page = row["keys"][1]
                    clicks = row["clicks"]
                    impressions = row["impressions"]
                    ctr = row["ctr"]
                    position = row["position"]
                    query_data.append([query, page, clicks, impressions, ctr, position])

                df = pd.DataFrame(
                    query_data,
                    columns=[
                        "Query",
                        "Page",
                        "Clicks",
                        "Impressions",
                        "CTR",
                        "Position",
                    ],
                )

                # #がついているURLは除外
                df = df[~df["Page"].str.contains("#")]

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

    # Impressions の範囲を1行で表示
    st.subheader("Impressions の範囲")
    col1, col2 = st.columns(2)
    with col1:
        min_impressions = st.number_input(
            "Impressions 以上",
            min_value=int(df["Impressions"].min()),
            max_value=int(df["Impressions"].max()),
            value=int(df["Impressions"].min()),
        )
    with col2:
        max_impressions = st.number_input(
            "Impressions 以下",
            min_value=int(df["Impressions"].min()),
            max_value=int(df["Impressions"].max()),
            value=int(df["Impressions"].max()),
        )

    # Clicks の範囲を1行で表示
    st.subheader("Clicks の範囲")
    col3, col4 = st.columns(2)
    with col3:
        min_clicks = st.number_input(
            "Clicks 以上",
            min_value=int(df["Clicks"].min()),
            max_value=int(df["Clicks"].max()),
            value=int(df["Clicks"].min()),
        )
    with col4:
        max_clicks = st.number_input(
            "Clicks 以下",
            min_value=int(df["Clicks"].min()),
            max_value=int(df["Clicks"].max()),
            value=int(df["Clicks"].max()),
        )

    
    # Position の範囲を1行で表示
    st.subheader("順位 (Position) の範囲")
    col5, col6 = st.columns(2)
    with col5:
        min_position = st.number_input(
            "順位 以上",
            min_value=int(df['Position'].min()),
            max_value=int(df['Position'].max()),
            value=int(df['Position'].min())
        )
    with col6:
        max_position = st.number_input(
            "順位 以下",
            min_value=int(df['Position'].min()),
            max_value=int(df['Position'].max()),
            value=int(df['Position'].max())
        )

    # CTR の範囲を1行で表示
    st.subheader("CTR の範囲")
    col7, col8 = st.columns(2)
    with col7:
        min_ctr = st.number_input(
            "CTR 以上",
            min_value=float(df['CTR'].min()),
            max_value=float(df['CTR'].max()),
            value=float(df['CTR'].min()),
            step=0.01
        )
    with col8:
        max_ctr = st.number_input(
            "CTR 以下",
            min_value=float(df['CTR'].min()),
            max_value=float(df['CTR'].max()),
            value=float(df['CTR'].max()),
            step=0.01
        )


    # フィルタリング条件の適用
    filtered_df = df[
        (df["Impressions"] >= min_impressions)
        & (df["Impressions"] <= max_impressions)
        & (df["Clicks"] >= min_clicks)
        & (df["Clicks"] <= max_clicks)
        & (df["Position"] >= min_position)
        & (df["Position"] <= max_position)
        & (df["CTR"] >= min_ctr)
        & (df["CTR"] <= max_ctr)
    ]

    # フィルタリングされたデータの表示
    st.header("フィルタリングされたデータ")
    st.write(filtered_df)