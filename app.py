import streamlit as st
import pymongo
import certifi
from datetime import datetime, timedelta

st.set_page_config(
    page_title=" 美股新聞精選 ", 
    layout="wide"
)

# 連線 MongoDB，當你在 Streamlit Cloud 部署時，要在 Settings -> Secrets 設定 MONGO_URI
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())

try:
    client = init_connection()
    db = client.finance_robot  # 資料庫名稱
    collection = db.articles   # 集合名稱
except Exception as e:
    st.error(f"connect to DB is faild: {e}")

with st.sidebar:
    st.title("控制面板")
    st.write("這是一個自動化機器人，每天自動抓取並評分美股新聞。")
    
    # 讓使用者選擇要看幾天內的新聞
    days = st.slider("顯示幾天內的新聞？", 1, 7, 1)
    limit_count = st.number_input("顯示數量", 5, 50, 10)
    
    st.divider()
    st.caption("開發者：ning")
    st.caption("技術棧：Python, MongoDB, GitHub Actions, Streamlit")

st.title(" 每日美股精選新聞 ")
st.markdown(f"** The Time is：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 計算時間範圍
time_threshold = datetime.now() - timedelta(days=days)

# 從 MongoDB 撈取資料：按重要性分數排序
query = {"created_at": {"$gte": time_threshold}}
top_news = list(collection.find(query).sort("importance_score", -1).limit(limit_count))

# 渲染新聞列表
if not top_news:
    st.warning("There are currently no news articles matching in the DB. Please check if the robot is functioning correctly.")
else:
    for news in top_news:
        with st.container():
            # 左邊放分數，右邊放內容
            col_score, col_content = st.columns([1, 6])
            
            with col_score:
                score = news.get('importance_score', 0)
                st.metric(label="important", value=f"{score:.2f}")
            
            with col_content:
                # 標題與連結
                st.subheader(f"[{news.get('title', '無標題')}]({news.get('link', '#')})")
                
                # 顯示標籤 (來源、情緒)
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**來源：** `{news.get('source', '未知')}`")
                
                # 情緒顯示
                sent = news.get('sentiment_score', 0.5)
                emoji = "正向" if sent > 0.6 else "中性" if sent > 0.4 else "負向"
                c2.markdown(f"**情緒分析：** {emoji} ({sent:.2f})")
                
                # 抓取時間
                fetch_time = news.get('created_at', datetime.now()).strftime('%m/%d %H:%M')
                c3.markdown(f"**抓取時間：** {fetch_time}")
                
                # 文章摘要
                with st.expander("查看新聞內容摘要"):
                    st.write(news.get('content', '暫無內文'))
            
            st.divider()
