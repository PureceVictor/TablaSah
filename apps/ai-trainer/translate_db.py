import json
import time
import torch
import re
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


def fix_chess_jargon(text):
    """
    Corecteaza ramanerile de jargon si notatiile algebrice ne-traduse.
    Include curatare pentru Germana, Rusa (Cirilice + Transliterari NLLB) si Spaniola.
    """
    fixes = [
        # ==========================================
        # 1. GERMANA (DE)
        # ==========================================
        (r'\b(Laeufer|Läufer)\b', 'bishop', re.IGNORECASE),
        (r'\bSpringer\b', 'knight', re.IGNORECASE),
        (r'\bTurm\b', 'rook', re.IGNORECASE),
        (r'\bDame\b', 'queen', re.IGNORECASE),
        (r'\bKönig\b', 'king', re.IGNORECASE),
        (r'\bBauer\b', 'pawn', re.IGNORECASE),
        (r'\b(Weiss|Weiß)\b', 'White', re.IGNORECASE),
        (r'\bSchwarz\b', 'Black', re.IGNORECASE),
        (r'\b(Felder|Feld)\b', 'square', re.IGNORECASE),
        
        # Notatie Germana -> Engleza (ex: Lg2 -> Bg2)
        (r'\bL([a-h][1-8])\b', r'B\1', 0), # Läufer -> Bishop
        (r'\bS([a-h][1-8])\b', r'N\1', 0), # Springer -> Knight
        (r'\bT([a-h][1-8])\b', r'R\1', 0), # Turm -> Rook
        (r'\bD([a-h][1-8])\b', r'Q\1', 0), # Dame -> Queen

        # ==========================================
        # 2. RUSA (RU) - Cirilice si Transliterari
        # ==========================================
        # Transliterari pe care NLLB le lasa des in pace
        (r'\b(Ferz|Ферзь)\b', 'queen', re.IGNORECASE),
        (r'\b(Ladya|Ладья)\b', 'rook', re.IGNORECASE),
        (r'\b(Slon|Слон)\b', 'bishop', re.IGNORECASE),
        (r'\b(Kon|Конь)\b', 'knight', re.IGNORECASE),
        (r'\b(Korol|Король)\b', 'king', re.IGNORECASE),
        (r'\b(Peshka|Пешка)\b', 'pawn', re.IGNORECASE),
        (r'\b(Belye|Белые|Belyi)\b', 'White', re.IGNORECASE),
        (r'\b(Chernye|Черные|Chernyi)\b', 'Black', re.IGNORECASE),
        
        # Notatie Rusa Cirilica -> Engleza (Atentie, caracterele din stanga sunt CIRILICE)
        (r'\bС([a-h][1-8])\b', r'B\1', 0),  # Слон -> Bishop
        (r'\bК([a-h][1-8])\b', r'N\1', 0),  # Конь -> Knight
        (r'\bЛ([a-h][1-8])\b', r'R\1', 0),  # Ладья -> Rook
        (r'\bФ([a-h][1-8])\b', r'Q\1', 0),  # Ферзь -> Queen
        (r'\bКр([a-h][1-8])\b', r'K\1', 0), # Король -> King

        # ==========================================
        # 3. SPANIOLA (ES)
        # ==========================================
        (r'\bAlfil\b', 'bishop', re.IGNORECASE),
        (r'\bCaballo\b', 'knight', re.IGNORECASE),
        (r'\bTorre\b', 'rook', re.IGNORECASE),
        (r'\b(Dama|Reina)\b', 'queen', re.IGNORECASE),
        (r'\bRey\b', 'king', re.IGNORECASE),
        (r'\bPe[oó]n\b', 'pawn', re.IGNORECASE),
        (r'\bBlanco\b', 'White', re.IGNORECASE),
        (r'\bNegro\b', 'Black', re.IGNORECASE),
        (r'\bCasilla\b', 'square', re.IGNORECASE),
        
        # Notatie Spaniola -> Engleza
        (r'\bA([a-h][1-8])\b', r'B\1', 0), # Alfil -> Bishop
        (r'\bC([a-h][1-8])\b', r'N\1', 0), # Caballo -> Knight
        # IGNORAM intentionat R (Rey) pentru a nu corupe R (Rook) din engleza.
    ]
    
    fixed_text = text
    # Rulam textul prin toata "masina de spalat"
    for pattern, replacement, flags in fixes:
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=flags)
        
    # Extra curatare: stergem spatiile duble care ar putea aparea
    return " ".join(fixed_text.split())   

def translate_database(input_path, output_path, batch_size=32):
    print(f"[*] Incalzim motorul AI...")
    
    # Verificam ca hardware-ul e gata de lupta
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("[!] ATENTIE: CUDA nu a fost detectat! Traducerea pe procesor va dura saptamani. Opreste scriptul!")
        return
    else:
        print(f"[*] Placa video detectata! Trecem pe {torch.cuda.get_device_name(0)}")

    # Incarcam modelul NLLB de la Meta (se va descarca automat la prima rulare - ~2.5 GB)
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, use_safetensors=True).to(device)

    print(f"[*] Incepem curatarea fisierului: {input_path}")
    
    start_time = time.time()
    total_processed = 0
    total_translated = 0
    
    batch_lines = []
    batch_texts = []
    
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
                
            total_processed += 1
            
            # Daca e deja in engleza, o salvam direct si trecem mai departe
            if data.get("lang") == "en":
                outfile.write(json.dumps(data) + "\n")
                continue
                
            # Daca nu e in engleza sau e necunoscuta, o pregatim pentru traducere
            batch_lines.append(data)
            batch_texts.append(data["comment"])
            
            # Cand s-a umplut pachetul (32 de texte), il trimitem pe placa video
            if len(batch_texts) >= batch_size:
                _translate_and_save_batch(tokenizer, model, device, batch_texts, batch_lines, outfile)
                total_translated += len(batch_texts)
                
                # Curatam pachetul pentru urmatoarea tura
                batch_texts = []
                batch_lines = []
                
            if total_processed % 1000 == 0:
                elapsed = time.time() - start_time
                print(f"[+] Linii verificate: {total_processed:,} | Traduse pe GPU: {total_translated:,} | Timp: {elapsed:.2f}s")

        # Traducem si resturile care au ramas in ultimul pachet (sub 32)
        if batch_texts:
            _translate_and_save_batch(tokenizer, model, device, batch_texts, batch_lines, outfile)
            total_translated += len(batch_texts)

    final_time = time.time() - start_time
    print(f"\n[V] Misiune indeplinita in {final_time:.2f} secunde!")
    print(f"Total linii trecute prin filtru: {total_processed:,}")
    print(f"Total comentarii straine traduse in engleza: {total_translated:,}")

def _translate_and_save_batch(tokenizer, model, device, texts, original_data_list, outfile):
    """Functie auxiliara care face matematica grea pe GPU."""
    # eng_Latn este codul pentru Engleza
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
    
    # Generam traducerea
    with torch.no_grad():
        translated_tokens = model.generate(
            **inputs, 
            forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn"),
            max_length=128
        )
    
    # Decodam rezultatul in text inapoi
    translated_texts = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
    
    # Actualizam dictionarele si le scriem in fisier
    for i, data in enumerate(original_data_list):
        raw_translation = translated_texts[i]
        cleaned_translation = fix_chess_jargon(raw_translation)
        
        data["comment"] = cleaned_translation
        data["lang"] = "en_translated" 
        outfile.write(json.dumps(data) + "\n")

if __name__ == "__main__":
    # Pune numele fisierului generat de tine azi
    INPUT_FILE = "training_data_multilingual.jsonl"
    OUTPUT_FILE = "training_data_english_only.jsonl"
    
    translate_database(INPUT_FILE, OUTPUT_FILE, batch_size=32)