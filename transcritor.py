import whisper
import torch
import math
import os
import sys
from deep_translator import GoogleTranslator

# --- CONFIGURAÇÕES ---
PASTA_VIDEOS = "videos"
EXTENSOES_ACEITAS = ('.mp4', '.mkv', '.avi', '.mov', '.webm')
MODELO_WHISPER = "small" # Opções: tiny, base, small, medium, large

def format_timestamp(seconds):
    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def listar_e_escolher_video():
    # Verifica se a pasta existe
    caminho_pasta = os.path.join(os.getcwd(), PASTA_VIDEOS)
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)
        print(f"\n[AVISO] A pasta '{PASTA_VIDEOS}' não existia e foi criada.")
        print(f"-> Por favor, coloque seus arquivos de vídeo dentro da pasta '{PASTA_VIDEOS}' e rode o programa novamente.")
        return None

    # Varre a pasta procurando videos
    arquivos = [f for f in os.listdir(caminho_pasta) if f.lower().endswith(EXTENSOES_ACEITAS)]
    
    if not arquivos:
        print(f"\n[VIO] A pasta '{PASTA_VIDEOS}' está vazia ou sem vídeos compatíveis.")
        print(f"Extensões aceitas: {EXTENSOES_ACEITAS}")
        return None

    print(f"\n--- VÍDEOS ENCONTRADOS EM '{PASTA_VIDEOS}' ---")
    for i, arquivo in enumerate(arquivos):
        print(f"[{i + 1}] {arquivo}")
    print("---------------------------------------------")

    while True:
        try:
            escolha = input("Digite o NÚMERO do vídeo que deseja processar (ou 0 para sair): ")
            if escolha == '0':
                return None
            
            indice = int(escolha) - 1
            if 0 <= indice < len(arquivos):
                # Retorna o caminho completo do video
                return os.path.join(caminho_pasta, arquivos[indice])
            else:
                print("Número inválido. Tente novamente.")
        except ValueError:
            print("Por favor, digite apenas números.")

def transcrever_e_traduzir(video_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    print(f"\n--- INICIANDO PROCESSAMENTO ---")
    print(f"Arquivo: {os.path.basename(video_path)}")
    print(f"Hardware: {device.upper()}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    print(f"\nCarregando modelo '{MODELO_WHISPER}'... (Aguarde)")
    model = whisper.load_model(MODELO_WHISPER, device=device)
    
    tradutor = GoogleTranslator(source='en', target='pt')
    
    print("Fase 1/2: Ouvindo e transcrevendo (Inglês)...")
    result = model.transcribe(video_path, fp16=False, language="en")
    
    # Define o nome da legenda na mesma pasta do vídeo
    filename = os.path.splitext(video_path)[0]
    output_srt = f"{filename}_PT-BR.srt"
    
    print("Fase 2/2: Traduzindo e salvando arquivo...")
    
    with open(output_srt, "w", encoding="utf-8") as f:
        total = len(result['segments'])
        for index, segment in enumerate(result['segments']):
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            texto_ingles = segment['text'].strip()
            
            try:
                texto_traduzido = tradutor.translate(texto_ingles)
            except:
                texto_traduzido = texto_ingles
            
            f.write(f"{index + 1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{texto_traduzido}\n\n")
            
            # Mostra progresso simples
            if index % 5 == 0:
                perc = int((index / total) * 100)
                print(f"Progresso: {perc}% concluído...", end="\r")

    print(f"\n\n[CONCLUÍDO] Legenda salva em:\n-> {output_srt}")

if __name__ == "__main__":
    video_selecionado = listar_e_escolher_video()
    
    if video_selecionado:
        transcrever_e_traduzir(video_selecionado)
    else:
        print("\nPrograma encerrado.")