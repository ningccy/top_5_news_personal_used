import streamlit as st
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, DateTime, Text, desc, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import sys
import os

st.set_page_config(page_title="what's new", layout="wide")
Base = declarative_base()

try:
    if "mysql" in st.secrets:
        db_config = st.secrets["mysql"]
    else:
        db_config = {
            "user": "2wGDHtMmwyuDx8w.root",
            "password": "cShHe1LJtolQ9zoI",
            "host": "gateway01.ap-northeast-1.prod.aws.tidbcloud.com",
            "port": "4000",
            "database": "test"
        }
    DATABASE_URL = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        f"?ssl_verify_cert=true&ssl_verify_identity=true"
    )
    engine = create_engine(
 
        DATABASE_URL,
        pool_size = 10,
        max_overflow = 20,
        pool_recycle = 3600,
        connect_args = {"ssl": {"fake_flag_to_enable_tls": True}}
    )
    
    SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1;"))
        st.sidebar.success(f"✅ 雲端資料庫連線成功！")
        
except Exception as e:
    st.error(f"❌ 資料庫連線失敗：{e}")
    st.stop()

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key = True, index = True)
    title = Column(String(255))
    link = Column(String(500), unique=True)
    source = Column(String(50))
    content = Column(Text)
    sentiment_score = Column(Float)
    sentiment_textblob = Column(Float)
    importance_score = Column(Float)
    published = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)

try:
    Base.metadata.create_all(bind = engine)
    st.sidebar.info("📌 資料庫結構已完成同步")
except Exception as schema_e:
    st.sidebar.error(f"結構同步失敗：{schema_e}")

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "scr")) 
#  --------------------------------------------------
st.sidebar.title(" ")
if st.sidebar.button("💡 立即抓取最新新聞"):
    with st.spinner("FinBERT 正在深度分析中..."):
        try:
            from scr import for_news_main 
            num_imported = for_news_main.main() 
            
            st.session_state['last_count'] = num_imported if num_imported is not None else 0
            if num_imported and num_imported > 0:
                st.sidebar.success(f"新聞更新完成！共抓取 {num_imported} 則")
                st.rerun() 
            else:
                st.sidebar.warning("無新增新聞（可能皆為重複）。")
        except Exception as e:
            st.sidebar.error(f"❌ 抓取失敗：{e}")
st.divider()
# ---------------------------------------------------
def show_news_dashboard():
    st.title("📰 美股精選新聞 💰")
    db = SessionLocal()
    
    try:
        with st.sidebar:
            days = st.sidebar.slider("幾天內新聞？", 1, 30, 7)
            limit = st.sidebar.number_input("顯示數量", 5, 50, 10)
            
            st.divider()

            last_count = st.session_state.get('last_count', 0)
            total_count = db.query(NewsArticle).count()
            
            st.markdown(f"**目前資料庫總量：{total_count} 筆**")
            st.sidebar.markdown(f"**當次處理數據：{last_count} 筆**")

        now_local = datetime.now()
        time_threshold = now_local - timedelta(days = days)
        
        top_news = db.query(NewsArticle) \
            .filter(NewsArticle.created_at >= time_threshold) \
            .order_by(desc(NewsArticle.importance_score)) \
            .limit(limit).all()

        if not top_news:
            st.warning("無符合條件的新聞資料，請點擊左側「💡立即抓取」按鈕。")
        else:
            for news in top_news:
                with st.container():
                    col_score, col_main = st.columns([1.5, 6])
                    
                    with col_score:
                        imp = news.importance_score if news.importance_score is not None else 0.0
                        fb = news.sentiment_score if news.sentiment_score is not None else 0.5
                        tb = news.sentiment_textblob if news.sentiment_textblob is not None else 0.5
                        
                        st.metric("重要性", f"{imp:.2f}")
                        st.write(f"📖 **Fin:** `{fb:.2f}`")
                        st.write(f"📝 **Blob:** `{tb:.2f}`")

                    with col_main:
                        st.subheader(f"[{news.title}]({news.link})")
                        st.caption(f"來源: {news.source} | 抓取時間: {news.created_at.strftime('%m/%d %H:%M')}")
                        
                        with st.expander("🔍 內容摘要"):
                            st.write(news.content)
                            if fb > 0.6: st.success("市場情緒: Bullish")
                            elif fb < 0.4: st.error("市場情緒: Bearish")
                            else: st.info("市場情緒: Neutral")
                    st.divider() 
                    
    except Exception as e:
        st.error(f"讀取資料庫失敗：{e}")
    finally:
        db.close()

# --- 啟動入口 ---
if __name__ == "__main__":
    show_news_dashboard()
