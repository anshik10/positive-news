# app.py
import streamlit as st
import requests
import os

# load keys (Streamlit will read these from secrets when deployed)
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY") or os.getenv("NEWS_API_KEY")

st.set_page_config(page_title="Positive News", layout="centered")
st.title("🌟 Positive News Generator")
st.write("Shows only uplifting news rewritten in an inspiring tone.")

if not OPENROUTER_API_KEY or not NEWS_API_KEY:
    st.error("Missing API keys. Add OPENROUTER_API_KEY and NEWS_API_KEY in Streamlit secrets (or env).")
    st.stop()

def get_news(country="in", page_size=10):
    url = "https://newsapi.org/v2/top-headlines"
    params = {"country": country, "pageSize": page_size, "apiKey": NEWS_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    return r.json().get("articles", [])

def call_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content":
             "You are a positivity filter. Answer with one line 'POSITIVE' or 'NEGATIVE'. "
             "If POSITIVE, on next lines give a 1-2 sentence uplifting rewrite of the news (keep facts)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 250
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    try:
        return resp.json()
    except:
        return {"error": "bad response", "status_code": resp.status_code, "text": resp.text}

st.sidebar.header("Options")
country = st.sidebar.selectbox("Country", ["in","us","gb","ca","au"], index=0)
count = st.sidebar.slider("How many headlines to check", 3, 15, 8)

if st.button("Fetch Positive News"):
    with st.spinner("Fetching headlines..."):
        articles = get_news(country=country, page_size=count)
        if not articles:
            st.warning("No articles found or API limit reached.")
        for a in articles:
            title = a.get("title","")
            desc = a.get("description") or ""
            source = a.get("source",{}).get("name","")
            prompt = f"TITLE: {title}\nDESC: {desc}\nSOURCE: {source}\n\nIs this POSITIVE or NEGATIVE? If POSITIVE, give a short uplifting rewrite (1-2 sentences)."
            jr = call_openrouter(prompt)
            content = ""
            try:
                content = jr.get("choices")[0]["message"]["content"].strip()
            except:
                content = str(jr)
            # check result
            if content.upper().startswith("POSITIVE"):
                # take rewrite after first line
                parts = content.splitlines()
                rewrite = "\n".join(parts[1:]).strip() or "Uplifting summary not provided."
                st.subheader(title)
                if a.get("urlToImage"):
                    st.image(a.get("urlToImage"), use_column_width=True)
                st.write(rewrite)
                st.caption(f"Source: {source}")
