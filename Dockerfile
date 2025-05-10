FROM python:3.10-slim

# Instalar ffmpeg e dependências
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Criar pasta do app
WORKDIR /app

# Copiar arquivos do projeto
COPY . /app

# Instalar dependências
RUN pip install moviepy==1.0.3
RUN pip install -r requirements.txt
# RUN pip install --no-cache-dir moviepy==1.0.3
# RUN pip install --no-cache-dir -r requirements.txt

# Comando padrão (pode mudar se quiser executar manualmente)
CMD ["python", "process_videos.py"]

# 1. Construir a imagem
# docker build -t process-videos .

# 2. Rodar o container (mapeando a pasta com os vídeos)
# docker run -v "C:\Users\conta\OneDrive\Documents\workspace\_oismaelash\interviews-resume\videos":/app/videos --env-file .env process-videos
