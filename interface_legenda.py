import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import whisper
import torch
import os
import math
import sys
from deep_translator import GoogleTranslator

# --- Mapeamento de Linguagens ---
LANGUAGES = {
    "Português": "pt", "Inglês": "en", "Espanhol": "es", "Francês": "fr",
    "Alemão": "de", "Italiano": "it", "Japonês": "ja", "Chinês": "zh", "Russo": "ru"
}

# --- Guia dos Modelos ---
INFO_MODELOS = {
    "tiny": "⚡ Rascunho Rápido: Baixa precisão. Instantâneo. Bom para testar se o programa funciona.",
    "base": "⏩ Básico: Bom para áudios muito limpos e claros. Pode errar pontuação.",
    "small": "✅ Recomendado (Padrão): O equilíbrio perfeito entre velocidade e precisão. Ideal para YouTube.",
    "medium": "🎬 Cinema/Séries: Alta precisão. Entende sotaques e música de fundo. (Ideal para sua RTX 3060)",
    "large": "🧠 Máxima Precisão: O modelo mais inteligente. Lento, mas pega detalhes que os outros perdem."
}

# --- Cores do Tema (Dark Mode) ---
CORES = {
    "bg": "#2b2b2b",         # Fundo Cinza Escuro
    "fg": "#ffffff",         # Texto Branco
    "accent": "#007acc",     # Azul Visual Studio
    "panel": "#333333",      # Fundo dos painéis
    "success": "#28a745",    # Verde
    "button": "#404040",     # Botão Cinza
    "button_hover": "#505050"
}

class LegendadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Legendas Pro IA")
        self.root.geometry("700x650")
        self.root.configure(bg=CORES["bg"])
        
        # Configurando Estilo (Dark Theme)
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam' permite customizar cores melhor
        
        self.configurar_estilos()

        # Variáveis
        self.video_path = tk.StringVar()
        self.device_var = tk.StringVar(value="GPU (Recomendado)")
        self.model_var = tk.StringVar(value="small")
        self.lang_origem_var = tk.StringVar(value="Inglês")
        self.lang_destino_var = tk.StringVar(value="Português")
        self.info_modelo_txt = tk.StringVar()

        self.criar_interface()
        self.atualizar_info_modelo() # Chama a primeira vez para carregar o texto

    def configurar_estilos(self):
        # Configuração geral de Frames e Labels
        self.style.configure("TFrame", background=CORES["bg"])
        self.style.configure("TLabelframe", background=CORES["bg"], foreground=CORES["fg"])
        self.style.configure("TLabelframe.Label", background=CORES["bg"], foreground=CORES["accent"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabel", background=CORES["bg"], foreground=CORES["fg"], font=("Segoe UI", 10))
        
        # Botões
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), background=CORES["button"], foreground="white", borderwidth=1)
        self.style.map("TButton", background=[("active", CORES["button_hover"])])
        
        # Botão de Ação (Verde/Azul destaque)
        self.style.configure("Accent.TButton", background=CORES["accent"], foreground="white", font=("Segoe UI", 11, "bold"))
        self.style.map("Accent.TButton", background=[("active", "#005f9e")])

        # Inputs
        self.style.configure("TEntry", fieldbackground=CORES["panel"], foreground="white")
        self.style.configure("TCombobox", fieldbackground=CORES["panel"], foreground="white", arrowcolor="white")

    def criar_interface(self):
        # Container Principal com Padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho
        lbl_titulo = tk.Label(main_frame, text="Legendas Automáticas (Whisper)", 
                              bg=CORES["bg"], fg=CORES["accent"], font=("Segoe UI", 18, "bold"))
        lbl_titulo.pack(pady=(0, 20))

        # 2. Seleção de Arquivo (Painel)
        pnl_arquivo = ttk.LabelFrame(main_frame, text=" Passo 1: Selecione o Vídeo ", padding="15")
        pnl_arquivo.pack(fill=tk.X, pady=5)
        
        frame_input = ttk.Frame(pnl_arquivo)
        frame_input.pack(fill=tk.X)
        
        self.entry_path = tk.Entry(frame_input, textvariable=self.video_path, bg=CORES["panel"], fg="white", 
                                   insertbackground="white", font=("Consolas", 10), bd=0, highlightthickness=1)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        
        btn_browse = ttk.Button(frame_input, text="📂 Procurar...", command=self.escolher_arquivo)
        btn_browse.pack(side=tk.RIGHT)

        # 3. Configurações (Grid)
        pnl_config = ttk.LabelFrame(main_frame, text=" Passo 2: Configurações ", padding="15")
        pnl_config.pack(fill=tk.X, pady=15)

        # Grid layout dentro do painel
        # Linha 1: Hardware e Modelo
        ttk.Label(pnl_config, text="Processamento:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Combobox(pnl_config, textvariable=self.device_var, values=["GPU (Recomendado)", "CPU (Lento)"], 
                     state="readonly", width=18).grid(row=0, column=1, sticky="w", padx=10)

        ttk.Label(pnl_config, text="Precisão (Modelo):").grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        combo_modelo = ttk.Combobox(pnl_config, textvariable=self.model_var, values=list(INFO_MODELOS.keys()), 
                                    state="readonly", width=10)
        combo_modelo.grid(row=0, column=3, sticky="w", padx=10)
        combo_modelo.bind("<<ComboboxSelected>>", self.atualizar_info_modelo)

        # Linha 2: Idiomas
        ttk.Label(pnl_config, text="Idioma do Vídeo:").grid(row=1, column=0, sticky="w", pady=15)
        ttk.Combobox(pnl_config, textvariable=self.lang_origem_var, values=list(LANGUAGES.keys()), 
                     state="readonly", width=18).grid(row=1, column=1, sticky="w", padx=10)

        ttk.Label(pnl_config, text="Traduzir para:").grid(row=1, column=2, sticky="w", pady=15, padx=(20, 0))
        ttk.Combobox(pnl_config, textvariable=self.lang_destino_var, values=list(LANGUAGES.keys()), 
                     state="readonly", width=18).grid(row=1, column=3, sticky="w", padx=10)

        # Label de Ajuda do Modelo (Destaque)
        lbl_info = tk.Label(pnl_config, textvariable=self.info_modelo_txt, 
                            bg=CORES["panel"], fg="#ffd700", font=("Segoe UI", 9), wraplength=550, pady=5)
        lbl_info.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        # 4. Botão Gigante
        self.btn_run = ttk.Button(main_frame, text="🚀 INICIAR PROCESSO", style="Accent.TButton", command=self.iniciar_thread)
        self.btn_run.pack(fill=tk.X, pady=10, ipady=5)

        # 5. Log
        ttk.Label(main_frame, text="Status do Processamento:").pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(main_frame, height=8, bg="black", fg="#00ff00", 
                                                  font=("Consolas", 9), state='disabled', bd=0)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def atualizar_info_modelo(self, event=None):
        modelo = self.model_var.get()
        texto = INFO_MODELOS.get(modelo, "")
        self.info_modelo_txt.set(texto)

    def log(self, mensagem):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, ">> " + mensagem + "\n")
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
        
        self.btn_run.config(state="disabled", text="Processando... (Aguarde)")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
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
            
            # Hardware
            use_gpu = "GPU" in device_choice
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            
            self.log(f"Iniciando: {os.path.basename(video_file)}")
            self.log(f"Hardware: {device.upper()}")
            if device == "cuda":
                self.log(f"GPU Detectada: {torch.cuda.get_device_name(0)}")

            # Whisper
            self.log(f"Carregando IA ({model_name})...")
            model = whisper.load_model(model_name, device=device)
            
            # Transcrição
            lang_code_src = LANGUAGES[lang_origem_nome]
            self.log(f"Ouvindo áudio em {lang_origem_nome}...")
            result = model.transcribe(video_file, fp16=False, language=lang_code_src)
            
            # Tradução e Salvamento
            lang_code_target = LANGUAGES[lang_destino_nome]
            filename = os.path.splitext(video_file)[0]
            output_srt = f"{filename}_{lang_code_target.upper()}.srt"
            
            precisa_traduzir = (lang_code_src != lang_code_target)
            tradutor = None
            if precisa_traduzir:
                self.log(f"Preparando tradutor ({lang_origem_nome} -> {lang_destino_nome})...")
                tradutor = GoogleTranslator(source=lang_code_src, target=lang_code_target)

            self.log("Gerando arquivo .srt...")
            with open(output_srt, "w", encoding="utf-8") as f:
                total_seg = len(result['segments'])
                for i, segment in enumerate(result['segments']):
                    start = self.format_timestamp(segment['start'])
                    end = self.format_timestamp(segment['end'])
                    text = segment['text'].strip()
                    
                    if precisa_traduzir:
                        try:
                            text = tradutor.translate(text)
                        except:
                            pass # Mantém original se falhar
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
                    
                    if i % 10 == 0:
                        progresso = int((i / total_seg) * 100)
                        self.log(f"Progresso: {progresso}%")

            self.log(f"SUCESSO! Arquivo salvo na pasta do vídeo.")
            messagebox.showinfo("Concluído", f"Legenda salva:\n{output_srt}")

        except Exception as e:
            self.log(f"ERRO: {str(e)}")
            messagebox.showerror("Erro", str(e))
        
        finally:
            self.btn_run.config(state="normal", text="🚀 INICIAR PROCESSO")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        caminho_base = os.path.dirname(sys.executable)
        os.environ["PATH"] += os.pathsep + caminho_base
    
    root = tk.Tk()
    app = LegendadorApp(root)
    root.mainloop()