docker build -t streamlit .
docker run -p 8501:8501 --name container_streamlit streamlit