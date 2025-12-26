# -*- coding: utf-8 -*-
"""Script de Fine-Tuning QLoRA (Unsloth + Qwen3)
Adaptado para usar dataset local e formato de dados já conversacional.
"""

# Importações principais
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template, standardize_data_formats, train_on_responses_only
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
import torch
torch._dynamo.config.disable = True
import os, re
from pathlib import Path
from transformers import TextStreamer, GenerationConfig
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DE CAMINHOS E MODELO ---
# Usar variáveis de ambiente com fallbacks
LORA_ADAPTER_PATH = os.getenv(
    'LORA_ADAPTER_PATH',
    str(Path(__file__).parent.parent / 'lora_model_qwen3_medquad')
)
LORA_ADAPTER_PATH = os.path.abspath(os.path.expanduser(LORA_ADAPTER_PATH))

MODEL_BASE = os.getenv('MODEL_BASE', 'unsloth/Qwen3-1.7B')

# Dataset path
DATASET_PATH = os.getenv(
    'DATASET_PATH',
    str(Path(__file__).parent.parent / 'dataset_medquad_ft.jsonl')
)
DATASET_PATH = os.path.abspath(os.path.expanduser(DATASET_PATH))

# Configurações de treinamento (com fallbacks)
LORA_R = int(os.getenv('LORA_R', '16'))
LORA_ALPHA = int(os.getenv('LORA_ALPHA', '16'))
LORA_DROPOUT = float(os.getenv('LORA_DROPOUT', '0'))
LEARNING_RATE = float(os.getenv('LEARNING_RATE', '2e-4'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '2'))  # Mínimo 2 para padding-free training
GRADIENT_ACCUMULATION_STEPS = int(os.getenv('GRADIENT_ACCUMULATION_STEPS', '4'))
# MAX_STEPS: se não definido, usa 60. Se definido como vazio ou "None", usa None para treino completo
max_steps_env = os.getenv('MAX_STEPS', '60')
MAX_STEPS = int(max_steps_env) if max_steps_env and max_steps_env.lower() != 'none' else None
MAX_SEQ_LENGTH = int(os.getenv('MAX_SEQ_LENGTH', '2048'))


# ==============================================================================
# 🎯 CORREÇÃO CRÍTICA PARA WINDOWS (Erro de Multiprocessamento/RuntimeError)
# Todo o código principal deve ser envolvido neste bloco.
# ==============================================================================
if __name__ == '__main__':
    
    # --- CARREGAR MODELO E TOKENIZER ---
    print(f"Loading Model: {MODEL_BASE}")
    
    # 🎯 CORREÇÃO CRÍTICA PARA ERRO DE VRAM/DISPATCH
    # Adicionando device_map="auto" para garantir que o modelo seja carregado
    # corretamente na GPU, evitando dispatch para CPU ou disco.
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = MODEL_BASE,
        max_seq_length = MAX_SEQ_LENGTH,
        load_in_4bit = True, # QLoRA: 4 bit quantization
        load_in_8bit = False,
        full_finetuning = False,
        device_map = "auto", 
    )

    # --- CONFIGURAR PEFT/LoRA ---
    print("Configuring LoRA adapter...")
    model = FastLanguageModel.get_peft_model(
        model,
        r = LORA_R,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = LORA_ALPHA,
        lora_dropout = LORA_DROPOUT,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        use_rslora = False,
        loftq_config = None,
    )

    # --- PREPARAÇÃO DOS DADOS (SIMPLIFICADA) ---

    # 1. Carregar Template de Chat (Qwen-3)
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "qwen3-instruct",
    )

    # 2. 🎯 Carregar o seu dataset local
    print(f"[STATUS] Carregando dataset local: {DATASET_PATH}")
    
    # Adicionado num_proc=1 para desabilitar o multiprocessamento na tokenização,
    # que é a fonte do RuntimeError no Windows.
    dataset = load_dataset("json", data_files=DATASET_PATH, split = "train", num_proc=1)

    # 3. Converter dataset para formato Qwen3 (se necessário)
    print("[STATUS] Convertendo dataset para formato Qwen3...")
    def convert_to_qwen3_format(example):
        """Converte formato '### Pergunta: ... ### Resposta: ...' para formato Qwen3"""
        text = example.get("text", "")
        
        # Extrair pergunta e resposta do formato atual
        if "### Pergunta:" in text and "### Resposta:" in text:
            parts = text.split("### Resposta:")
            pergunta = parts[0].replace("### Pergunta:", "").strip()
            resposta = parts[1].strip() if len(parts) > 1 else ""
            
            # Formato Qwen3: <start_of_turn>user\n{pergunta}<end_of_turn>\n<start_of_turn>model\n{resposta}<end_of_turn>
            formatted_text = f"<start_of_turn>user\n{pergunta}<end_of_turn>\n<start_of_turn>model\n{resposta}<end_of_turn>"
            return {"text": formatted_text}
        else:
            # Se já estiver no formato correto, retorna como está
            return {"text": text}
    
    dataset = dataset.map(convert_to_qwen3_format, num_proc=1)
    print(f"[STATUS] Dataset convertido. Total de exemplos: {len(dataset)}")

    # --- TREINAR O MODELO ---
    print("\n" + "="*60)
    print("[STATUS] CONFIGURANDO TREINAMENTO LoRA...")
    print("="*60)

    # Cria o diretório de salvamento, se não existir
    os.makedirs(LORA_ADAPTER_PATH, exist_ok=True)

    # Preparar argumentos do SFTConfig
    sft_config_args = {
        "output_dir": LORA_ADAPTER_PATH, # Onde logs e checkpoints serão salvos
        "dataset_text_field": "text", # Usa a coluna 'text' pré-formatada
        "per_device_train_batch_size": BATCH_SIZE,
        "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
        "warmup_steps": 5,
        "learning_rate": LEARNING_RATE,
        "logging_steps": 10,
        "optim": "adamw_8bit",
        "weight_decay": 0.001,
        "lr_scheduler_type": "linear",
        "seed": 3407,
        "report_to": "none",
        "fp16": not torch.cuda.is_bf16_supported(), # Ajuste automático para tipo de precisão
        "bf16": torch.cuda.is_bf16_supported(),
    }
    
    # Adicionar max_steps apenas se não for None (para evitar erro de comparação)
    if MAX_STEPS is not None:
        sft_config_args["max_steps"] = MAX_STEPS
        print(f"[INFO] Treinamento limitado a {MAX_STEPS} steps")
    else:
        print("[INFO] Treinamento completo (sem limite de steps)")

    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        eval_dataset = None,
        args = SFTConfig(**sft_config_args),
    )

    # --- MÁSCARA PARA TREINAR APENAS NAS RESPOSTAS (Melhora a precisão) ---
    trainer = train_on_responses_only(
        trainer,
        # Padrões de início de turno (ajustados para o seu formato)
        instruction_part = "<start_of_turn>user\n",
        response_part = "<start_of_turn>model\n",
    )

    # 6. INICIAR TREINAMENTO!
    print("\n" + "="*60)
    print("[STATUS] INICIANDO TREINAMENTO LoRA...")
    print("="*60)

    trainer_stats = trainer.train()

    # --- SALVAR MODELO ---
    model.save_pretrained(LORA_ADAPTER_PATH) # Salvamento do adaptador LoRA
    tokenizer.save_pretrained(LORA_ADAPTER_PATH)
    print("\n[STATUS] Adaptador LoRA e Tokenizer salvos em:", LORA_ADAPTER_PATH)


    # --- INFERÊNCIA DE TESTE ---
    print("\n"+"="*60)
    print("TESTE DE INFERÊNCIA APÓS TREINAMENTO")
    print("="*60)

    # Exemplo de pergunta médica para testar o domínio treinado (MedQuAD)
    messages = [
        {"role" : "user", "content" : "O que é Leucemia Linfoblástica Aguda em Adultos (LLA) e quais são os seus principais sintomas? Responda em Português."},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize = False,
        add_generation_prompt = True,
    )

    # Geração de texto
    # Configuração de geração para melhor controle
    generation_config = GenerationConfig(
        max_new_tokens = 256,
        temperature = 0.7,
        top_p = 0.8,
        top_k = 20,
        do_sample = True,
        pad_token_id = tokenizer.eos_token_id, # Importante para Qwen
        eos_token_id = tokenizer.eos_token_id,
    )

    _ = model.generate(
        **tokenizer(text, return_tensors = "pt").to("cuda"),
        generation_config = generation_config,
        streamer = TextStreamer(tokenizer, skip_prompt = True),
    )

    # --- AVALIAÇÃO DO TESTE ---
    print("\n"+"="*60)
    print("AVALIAÇÃO DO TESTE DE INFERÊNCIA")
    print("="*60)
    print("O teste de inferência (acima) deve mostrar uma resposta **direta e informativa** sobre a LLA, de preferência em **Português** (como solicitado no prompt), refletindo o conhecimento do dataset MedQuAD.")
    print("Se a resposta for coerente, precisa e no idioma correto, o fine-tuning foi bem-sucedido.")