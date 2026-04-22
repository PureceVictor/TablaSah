import chromadb
from chromadb.utils import embedding_functions

def search_chess_brain(query_text, num_results=3):
    print(f"[*] Conectare la baza de date RAG...")
    
    # Incarcam baza de date de pe disc
    client = chromadb.PersistentClient(path="./chess_rag_db")
    
    # Folosim acelasi model matematic pentru a transforma intrebarea noastra in vector
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Accesam colectia
    collection = client.get_collection(
        name="chess_master_games",
        embedding_function=sentence_transformer_ef
    )
    
    print(f"[*] Cautam in memorie dupa: '{query_text}'\n")
    
    # Facem cautarea semantica
    results = collection.query(
        query_texts=[query_text],
        n_results=num_results
    )
    
    # Afisam rezultatele frumos formatate
    for i in range(num_results):
        fen = results['metadatas'][0][i]['fen']
        # Lichess foloseste '_' in loc de spatii in URL-urile FEN
        lichess_url = f"https://lichess.org/analysis/standard/{fen.replace(' ', '_')}"
        
        print(f"--- REZULTATUL {i+1} ---")
        print(f"Explicatie din baza: {results['documents'][0][i]}")
        print(f"Mutarea jucata: {results['metadatas'][0][i]['move']}")
        print(f"Jucatori: {results['metadatas'][0][i]['white']} vs {results['metadatas'][0][i]['black']}")
        print(f"FEN: {fen}")
        print(f"Link Tabla: {lichess_url}")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    # Aici simulam ce ar cauta aplicatia ta in fundal
    # Cautam un concept clasic: sacrificiul nebunului pe h7 (Greek Gift)
    test_query = "White sacrifices the bishop on h7 to expose the black king and start a strong attack"
    
    search_chess_brain(test_query)