import os
from openai import OpenAI
import whisper
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

PASTA_VIDEOS = 'videos'
PASTA_SAIDA = os.path.join(PASTA_VIDEOS, "resultados")
os.makedirs(PASTA_SAIDA, exist_ok=True)

modelo_whisper = whisper.load_model("base")

videos_com_erro = []

def extrair_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    # Obter a duração do vídeo em minutos
    duracao_minutos = video.duration / 60
    video.audio.write_audiofile(audio_path, codec='mp3', verbose=False, logger=None)
    return duracao_minutos

def transcrever_audio(audio_path):
    resultado = modelo_whisper.transcribe(audio_path)
    return resultado['text']

def resumir_texto(texto, duracao_minutos):
    # Formatar duração para incluir no prompt
    duracao_formatada = f"{int(duracao_minutos)} minutos" if duracao_minutos >= 1 else f"{int(duracao_minutos * 60)} segundos"
    
    prompt = (
        os.environ.get("PROMPT_ENTREVISTA") +
        f"\n\nDuração da entrevista: {duracao_formatada}\n\n" +
        f"{texto}"
    )
    resposta = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL"),
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.choices[0].message.content.strip()
    # return "Resumo desativado - OpenAI comentado"

def processar_video(video_path_relativo):
    # video_path_relativo pode ser apenas o nome do arquivo ou um caminho com subpastas
    nome_base = os.path.splitext(os.path.basename(video_path_relativo))[0]
    caminho_video = os.path.join(PASTA_VIDEOS, video_path_relativo)
    
    # Criar estrutura de pastas na saída para manter organização
    pasta_saida_video = os.path.join(PASTA_SAIDA, os.path.dirname(video_path_relativo))
    os.makedirs(pasta_saida_video, exist_ok=True)
    
    caminho_audio = os.path.join(pasta_saida_video, f"{nome_base}.mp3")
    caminho_transcricao = os.path.join(pasta_saida_video, f"{nome_base}.txt")
    caminho_resumo = os.path.join(pasta_saida_video, f"{nome_base}_resumo.txt")

    try:
        print(f"Iniciando: {video_path_relativo}")
        # Extrair áudio e obter duração
        duracao_minutos = extrair_audio(caminho_video, caminho_audio)
        texto = transcrever_audio(caminho_audio)
        with open(caminho_transcricao, 'w', encoding='utf-8') as f:
            f.write(texto)

        # Passar a duração para a função de resumo
        # resumo = resumir_texto(texto, duracao_minutos)
        # with open(caminho_resumo, 'w', encoding='utf-8') as f:
        #     f.write(resumo)

        print(f"Finalizado: {video_path_relativo}")
    except Exception as e:
        print(f"[ERRO] {video_path_relativo} - {e}")
        videos_com_erro.append(video_path_relativo)

# Permite repetir só os vídeos com erro
def carregar_erros_antigos():
    erro_txt = os.path.join(PASTA_SAIDA, 'erros.txt')
    if os.path.exists(erro_txt):
        with open(erro_txt, 'r') as f:
            return [linha.strip() for linha in f.readlines()]
    return []

def encontrar_videos_recursivamente(pasta):
    """Encontra todos os vídeos .mp4 na pasta e subpastas"""
    videos = []
    for root, dirs, files in os.walk(pasta):
        for file in files:
            if file.endswith('.mp4') and not file.startswith('.'):
                # Manter o caminho relativo à pasta de vídeos
                caminho_relativo = os.path.relpath(os.path.join(root, file), pasta)
                videos.append(caminho_relativo)
    return videos

videos_para_processar = encontrar_videos_recursivamente(PASTA_VIDEOS)

# Opção: só reprocessar vídeos com erro anterior
reprocessar_falhas = os.getenv('REPROCESSAR_FALHAS', 'false').lower() == 'true'
if reprocessar_falhas:
    videos_para_processar = carregar_erros_antigos()

for video in videos_para_processar:
    processar_video(video)

# Salva erros ao final
if videos_com_erro:
    with open(os.path.join(PASTA_SAIDA, 'erros.txt'), 'w') as f:
        for nome in videos_com_erro:
            f.write(f"{nome}\n")

print("\n--- PROCESSAMENTO CONCLUÍDO ---")
if videos_com_erro:
    print(f"{len(videos_com_erro)} vídeos com erro. Listados em: resultados/erros.txt")
else:
    print("Todos os vídeos foram processados com sucesso!")
