import ollama
from coach_core import ChessCoachCore

def genereaza_lectie(fen):
    print("\n[LLM] Initiem modulul de generare a lectiei...")
    
    # Instantiem nucleul care contine atat Stockfish cat si RAG-ul
    coach = ChessCoachCore()
    
    # 1. Extragem datele VALIDATE
    analiza, rezultate_rag = coach.consult(fen)
    
    if analiza is None:
        print("[!] Eroare la analiza pozitiilor.")
        return
        
    best_move = analiza['best_move']
    evaluare = analiza['evaluation']
    
    # 2. Construim contextul din baza de date
    rag_context = ""
    if rezultate_rag and rezultate_rag['documents'][0]:
        for i, doc in enumerate(rezultate_rag['documents'][0]):
            rag_context += f"- Fragment istoric validat: {doc}\n"
    else:
        rag_context = "Nu s-au gasit meciuri istorice valide. Trebuie sa te bazezi pe principiile generale ale structurii curente."

    # 3. PROMPT ENGINEERING (Aici controlam halucinatiile)
    prompt = f"""Ești un antrenor de șah de elită. Explică-i elevului tău de ce următoarea mutare este cea mai bună.
Vorbește la per tu, fii direct, scurt, și folosește un ton încurajator. Trebuie să răspunzi EXCLUSIV în limba română.

DATE FIXE (Nu inventa mutări și nu contrazice matematica):
- Mutarea corectă calculată de motor: {best_move}
- Evaluarea poziției: {evaluare} (pozitiv înseamnă avantaj alb, negativ avantaj negru)
- Ce au zis alți maeștri despre poziții similare:
{rag_context}

Sarcina ta: Formulează o explicație de 2-3 paragrafe clare. Explică planul din spatele mutării {best_move}, integrând organic comentariile maeștrilor pentru a-i arăta elevului contextul strategic. Transformă acele fragmente istorice într-o lecție coerentă."""

    print("\n[*] Antrenorul gandeste raspunsul final (procesare 100% locala)...\n")
    print("=" * 60)
    
    # 4. Apelul catre LLM-ul local
    try:
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt}
        ])
        print(response['message']['content'])
    except Exception as e:
        print(f"[!] Eroare la conectarea cu Ollama. Asigura-te ca ai rulat 'ollama run llama3' in alt terminal. Detalii: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Testam exact pe pozitia care ne-a dat batai de cap
    test_fen = "r1b1k2r/pp2bppp/1qn1p3/3pP3/3P4/P1N1PN2/1P1QB1PP/R3K2R w KQkq - 1 12"
    genereaza_lectie(test_fen)