import streamlit as st
import pickle
from googlesearch import search
import pandas as pd
import requests
import json
from difflib import get_close_matches
from bs4 import BeautifulSoup

# ------------------------ Fetch Poster from OMDb API ------------------------
def fetch_poster(movie_title):
    api_key = 'ced4ff18'  # Your OMDb API key
    url = f"http://www.omdbapi.com/?t={movie_title}&apikey={api_key}"
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        return data.get('Poster', "https://via.placeholder.com/300x450.png?text=No+Poster")
    except Exception as e:
        print(f"OMDb error: {e}")
        return "https://via.placeholder.com/300x450.png?text=Error"

# ------------------------ Google Search for OTT Platforms ------------------------
def find_platform_google(movie_name):
    query = f"{movie_name} where to watch"
    try:
        results = list(search(query, num_results=5))
    except Exception as e:
        print(f"Search error: {e}")
        return ["Search failed"]

    platforms = []
    for url in results:
        url = url.lower()
        if "netflix" in url:
            platforms.append("Netflix")
        elif "primevideo" in url or "prime" in url:
            platforms.append("Prime Video")
        elif "hotstar" in url or "disneyplus" in url:
            platforms.append("Disney+ Hotstar")
        elif "sonyliv" in url:
            platforms.append("SonyLIV")
        elif "justwatch" in url:
            platforms.append("JustWatch")

    return list(set(platforms)) if platforms else ["Not found"]

# ------------------------ Recommendation Logic ------------------------
def recommend(movie):
    movie_index = movies_list[movies_list['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(
        list(enumerate(distances)), reverse=True, key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_platforms = []
    recommended_posters = []

    for i in movie_list:
        movie_title = movies_list.iloc[i[0]].title
        recommended_movies.append(movie_title)
        recommended_posters.append(fetch_poster(movie_title))
        platform_info = find_platform_google(movie_title)
        recommended_platforms.append(", ".join(platform_info))

    return recommended_movies, recommended_platforms, recommended_posters

# ------------------------ YouTube History HTML to JSON ------------------------
def convert_html_to_json(html_file):
    soup = BeautifulSoup(html_file, 'html.parser')
    items = soup.find_all('div', class_='content-cell')

    history_list = []
    for item in items:
        text = item.get_text()
        if "Watched" in text:
            title_line = text.split('\n')[0].replace("Watched ", "")
            history_list.append({"title": title_line.strip()})

    return history_list

# ------------------------ YouTube History Processing ------------------------
def extract_movies_from_youtube(file):
    try:
        if file.name.endswith('.html'):
            data = convert_html_to_json(file)
        else:
            data = json.load(file)

        titles = []
        for entry in data:
            title = entry.get("title", "")
            if any(word in title.lower() for word in ["movie", "film", "official trailer", "netflix", "prime"]):
                titles.append(title)
        return titles
    except Exception as e:
        st.error(f"Failed to process YouTube history: {e}")
        return []

def match_titles_to_movies(youtube_titles, movie_titles):
    matched_movies = []
    for yt_title in youtube_titles:
        match = get_close_matches(yt_title, movie_titles, n=1, cutoff=0.6)
        if match:
            matched_movies.append(match[0])
    return list(set(matched_movies))

def get_history_based_recommendations(youtube_file):
    yt_titles = extract_movies_from_youtube(youtube_file)
    matched_movies = match_titles_to_movies(yt_titles, movies_list['title'].values)
    all_recommended = set()

    for movie in matched_movies[:3]:
        recs, _, _ = recommend(movie)
        all_recommended.update(recs)

    return list(all_recommended)[:5]

# ------------------------ Load Data ------------------------
movie_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies_list = pd.DataFrame(movie_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# ------------------------ Streamlit UI ------------------------
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender System with OTT Info + Posters")

selected_movie_name = st.selectbox(
    "Enter a movie to get recommendations:",
    movies_list['title'].values
)

platform_links = {
    "Netflix": "https://www.netflix.com",
    "Prime Video": "https://www.primevideo.com",
    "Disney+ Hotstar": "https://www.hotstar.com",
    "SonyLIV": "https://www.sonyliv.com",
    "JustWatch": "https://www.justwatch.com/in"
}

if st.button('Recommend'):
    st.subheader(f"Movies similar to **{selected_movie_name}**:")
    recommendations, platforms, posters = recommend(selected_movie_name)

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.image(posters[i], use_container_width=True)
            st.markdown(f"**{recommendations[i]}**")
            platform_names = platforms[i].split(", ")
            linked_platforms = [f"[{p}]({platform_links.get(p.strip(), '#')})" if platform_links.get(p.strip()) else p for p in platform_names]
            st.markdown(f"📺 *OTT Platform:* {' | '.join(linked_platforms)}", unsafe_allow_html=True)

# ------------------------ YouTube History Upload ------------------------
st.subheader("📤 Upload Your YouTube Watch History")
st.markdown("""
[🔗 Click here to open Google Takeout](https://takeout.google.com/)  
Go to: YouTube and YouTube Music → Only select *Watch history* → Create export
""", unsafe_allow_html=True)

youtube_file = st.file_uploader("Upload `watch-history.json` or `watch-history.html`", type=["json", "html"])

if youtube_file:
    history_recs = get_history_based_recommendations(youtube_file)
    if history_recs:
        st.subheader("🎥 Recommended Movies Based on Your YouTube History")
        hist_cols = st.columns(5)
        for idx, movie in enumerate(history_recs):
            with hist_cols[idx]:
                poster = fetch_poster(movie)
                st.image(poster, use_container_width=True)
                st.markdown(f"**{movie}**")
    else:
        st.info("No movie-related content found in your watch history.")