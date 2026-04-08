from scipy.stats import pearsonr
import pandas as pd

def main(input_file="minha_amostra_bancada.txt", ref_dir="ref/"):

    # 1. Carrega sua amostra real
    amostra_real = pd.read_csv(input_file, sep='\t', names=['theta', 'int'])
    amostra_int_norm = (amostra_real['int'] - amostra_real['int'].min()) / amostra_real['int'].max()

    # 2. Dicionário com suas referências candidatas
    candidatos = {
        "Hematita": f"{ref_dir}/ref_hematita.txt",
        "Magnetita": f"{ref_dir}/ref_magnetita.txt",
        "Goethita": f"{ref_dir}/ref_goethita.txt",
        "Wustita": f"{ref_dir}/ref_wustita.txt"
    }

    # 3. Testa uma por vez e guarda o Score
    ranking = {}
    for nome, arquivo_ref in candidatos.items():
        ref_df = pd.read_csv(arquivo_ref, sep='\t', names=['theta', 'int'])
        ref_int_norm = (ref_df['int'] - ref_df['int'].min()) / ref_df['int'].max()
        
        # Calcula a similaridade estatística
        score, _ = pearsonr(amostra_int_norm, ref_int_norm)
        ranking[nome] = score

    # 4. Exibe os resultados ordenados (do melhor para o pior)
    print("--- RANKING DE FASES (Score de Similaridade) ---")
    for nome, score in sorted(ranking.items(), key=lambda x: x[1], reverse=True):
        print(f"{nome}: {score:.2%}")