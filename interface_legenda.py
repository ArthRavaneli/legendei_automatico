import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import whisper
import torch
import os
import math
import sys
from deep_translator import GoogleTranslator

# --- Mapeamento de Linguagens (Nome -> Código ISO) ---
LANGUAGES = {
    "Português": "pt",
    "Inglês": "en",
    "Espanhol": "es",
    "Francês": "fr",
    "Alemão": "de",
    "Italiano": "it",
    "Japonês": "ja",
    "Chinês": "zh",
    "Russo": "ru"
}

class LegendadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Legendas IA - Whisper")
        self.root.geometry("600x550")
        self.root.resizable(False, False)

        # Variáveis de Controle
        self.video_path = tk.StringVar()
        self.status_var = tk.StringVar(value="Aguardando...")
        self.device_var = tk.StringVar(value="GPU (Recomendado)")
        self.model_var = tk.StringVar(value="small")
        self.lang_origem_var = tk.StringVar(value="Inglês")
        self.lang_destino_var = tk.StringVar(value="Português")

        self.criar_interface()

    def criar_interface(self):
        # Frame Principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Seleção de Arquivo
        ttk.Label(main_frame, text="Selecione o Vídeo:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        self.entry_path = ttk.Entry(file_frame, textvariable=self.video_path, width=50)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_browse = ttk.Button(file_frame, text="Procurar...", command=self.escolher_arquivo)
        btn_browse.pack(side=tk.RIGHT)

        # 2. Configurações de Hardware e Modelo
        opts_frame = ttk.LabelFrame(main_frame, text="Configurações de Processamento", padding="10")
        opts_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

        # Hardware
        ttk.Label(opts_frame, text="Processador:").grid(row=0, column=0, sticky="w", padx=5)
        combo_device = ttk.Combobox(opts_frame, textvariable=self.device_var, values=["GPU (Recomendado)", "CPU (Lento)"], state="readonly")
        combo_device.grid(row=0, column=1, padx=5, pady=5)

        # Modelo
        ttk.Label(opts_frame, text="Precisão (Modelo):").grid(row=0, column=2, sticky="w", padx=5)
        combo_model = ttk.Combobox(opts_frame, textvariable=self.model_var, values=["tiny", "base", "small", "medium", "large"], state="readonly", width=10)
        combo_model.grid(row=0, column=3, padx=5, pady=5)

        # 3. Configurações de Idioma
        lang_frame = ttk.LabelFrame(main_frame, text="Configurações de Idioma", padding="10")
        lang_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        # Origem
        ttk.Label(lang_frame, text="Idioma do Vídeo:").grid(row=0, column=0, sticky="w", padx=5)
        combo_origem = ttk.Combobox(lang_frame, textvariable=self.lang_origem_var, values=list(LANGUAGES.keys()), state="readonly")
        combo_origem.grid(row=0, column=1, padx=5, pady=5)

        # Destino
        ttk.Label(lang_frame, text="Traduzir para:").grid(row=0, column=2, sticky="w", padx=5)
        combo_destino = ttk.Combobox(lang_frame, textvariable=self.lang_destino_var, values=list(LANGUAGES.keys()), state="readonly")
        combo_destino.grid(row=0, column=3, padx=5, pady=5)

        # 4. Botão de Ação
        self.btn_run = ttk.Button(main_frame, text="INICIAR TRANSCRIÇÃO", command=self.iniciar_thread)
        self.btn_run.grid(row=4, column=0, columnspan=2, sticky="ew", pady=15)

        # 5. Log de Saída
        ttk.Label(main_frame, text="Log de Processamento:").grid(row=5, column=0, sticky="w")
        self.log_area = scrolledtext.ScrolledText(main_frame, height=10, width=65, state='disabled', font=("Consolas", 9))
        self.log_area.grid(row=6, column=0, columnspan=2, pady=(5, 0))

    def log(self, mensagem):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, mensagem + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def escolher_arquivo(self):
        filename = filedialog.askopenfilename(
            title="Selecione o vídeo",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.mkv *.avi *.mov *.webm"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            self.video_path.set(filename)

    def iniciar_thread(self):
        if not self.video_path.get():
            messagebox.showwarning("Atenção", "Selecione um vídeo primeiro!")
            return
        
        # Desabilita botão para evitar cliques duplos
        self.btn_run.config(state="disabled")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        # Roda o processo pesado em segundo plano para não travar a janela
        threading.Thread(target=self.processar_video, daemon=True).start()

    def format_timestamp(self, seconds):
        hours = math.floor(seconds / 3600)
        seconds %= 3600
        minutes = math.floor(seconds / 60)
        seconds %= 60
        milliseconds = round((seconds - math.floor(seconds)) * 1000)
        seconds = math.floor(seconds)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def processar_video(self):
        try:
            video_file = self.video_path.get()
            model_name = self.model_var.get()
            device_choice = self.device_var.get()
            lang_origem_nome = self.lang_origem_var.get()
            lang_destino_nome = self.lang_destino_var.get()
            
            # 1. Definição de Hardware
            use_gpu = "GPU" in device_choice
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            
            self.log(f"--- Configuração ---")
            self.log(f"Arquivo: {os.path.basename(video_file)}")
            self.log(f"Hardware Selecionado: {device.upper()}")
            if device == "cpu" and use_gpu:
                self.log("AVISO: GPU solicitada mas não encontrada. Usando CPU.")

            # 2. Carregar Whisper
            self.log(f"Carregando modelo '{model_name}'... (Isso pode demorar)")
            model = whisper.load_model(model_name, device=device)
            
            # 3. Transcrever
            lang_code_src = LANGUAGES[lang_origem_nome]
            self.log(f"Transcrevendo áudio em {lang_origem_nome}...")
            result = model.transcribe(video_file, fp16=False, language=lang_code_src)
            
            # 4. Traduzir e Salvar
            lang_code_target = LANGUAGES[lang_destino_nome]
            filename = os.path.splitext(video_file)[0]
            output_srt = f"{filename}_{lang_code_target.upper()}.srt"
            
            self.log(f"Iniciando tradução para {lang_destino_nome}...")
            
            # Se origem e destino forem iguais, não usa o Google Translator
            precisa_traduzir = (lang_code_src != lang_code_target)
            tradutor = None
            if precisa_traduzir:
                tradutor = GoogleTranslator(source=lang_code_src, target=lang_code_target)

            with open(output_srt, "w", encoding="utf-8") as f:
                total_seg = len(result['segments'])
                for i, segment in enumerate(result['segments']):
                    start = self.format_timestamp(segment['start'])
                    end = self.format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    if precisa_traduzir:
                        try:
                            text = tradutor.translate(text)
                        except Exception as e:
                            print(f"Erro tradução: {e}")
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
                    
                    if i % 5 == 0:
                        progresso = int((i / total_seg) * 100)
                        self.log(f"Processando: {progresso}%")

            self.log(f"CONCLUÍDO! Legenda salva em:\n{output_srt}")
            messagebox.showinfo("Sucesso", "Legenda gerada com sucesso!")

        except Exception as e:
            self.log(f"ERRO FATAL: {str(e)}")
            messagebox.showerror("Erro", str(e))
        
        finally:
            self.btn_run.config(state="normal")

if __name__ == "__main__":
    # Verifica FFmpeg na pasta local (para versão portátil)
    if getattr(sys, 'frozen', False):
        caminho_base = os.path.dirname(sys.executable)
        os.environ["PATH"] += os.pathsep + caminho_base
    
    root = tk.Tk()
    app = LegendadorApp(root)
    root.mainloop()