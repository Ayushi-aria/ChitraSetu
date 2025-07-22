mkdir -p ~/.streamlit/
echo "\[server]\n\
port=$Port\n\
enableCORS= false\n\
headless=true\n\
\n\
"> ~/.streamlit/config.toml