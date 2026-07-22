import streamlit as st
import requests
import itertools

# ==========================================
# 1. O NOSSO MOTOR DE BUSCA
# ==========================================
def pegar_ficha_pokemon(nome):
    nome = nome.lower().strip()
    try:
        url_principal = f"https://pokeapi.co/api/v2/pokemon/{nome}"
        resposta_principal = requests.get(url_principal).json()
        tipos = [tipo['type']['name'] for tipo in resposta_principal['types']]
        
        url_especie = f"https://pokeapi.co/api/v2/pokemon-species/{nome}"
        resposta_especie = requests.get(url_especie).json()
        
        geracao_romana = resposta_especie['generation']['name'].split('-')[1]
        tabela_geracoes = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}
        geracao = tabela_geracoes.get(geracao_romana, 0)
        
        url_evolucao = resposta_especie['evolution_chain']['url']
        resposta_evolucao = requests.get(url_evolucao).json()
        cadeia = resposta_evolucao['chain']
        
        estagio = 0
        if cadeia['species']['name'] != nome:
            for evolucao1 in cadeia['evolves_to']:
                if evolucao1['species']['name'] == nome:
                    estagio = 1
                    break
                for evolucao2 in evolucao1['evolves_to']:
                    if evolucao2['species']['name'] == nome:
                        estagio = 2
                        break

        return {"Nome": nome.capitalize(), "Tipos": tipos, "Geracao": geracao, "Estagio": estagio}
    except Exception as e:
        return f"Erro ao buscar {nome}"

# ==========================================
# 2. AS REGRAS MATEMÁTICAS
# ==========================================
SUPER_EFETIVO = {
    'normal': [], 'fire': ['grass', 'ice', 'bug', 'steel'], 'water': ['fire', 'ground', 'rock'],
    'electric': ['water', 'flying'], 'grass': ['water', 'ground', 'rock'], 'ice': ['grass', 'ground', 'flying', 'dragon'],
    'fighting': ['normal', 'ice', 'rock', 'dark', 'steel'], 'poison': ['grass', 'fairy'],
    'ground': ['fire', 'electric', 'poison', 'rock', 'steel'], 'flying': ['grass', 'fighting', 'bug'],
    'psychic': ['fighting', 'poison'], 'bug': ['grass', 'psychic', 'dark'], 'rock': ['fire', 'ice', 'flying', 'bug'],
    'ghost': ['psychic', 'ghost'], 'dragon': ['dragon'], 'dark': ['psychic', 'ghost'],
    'steel': ['ice', 'rock', 'fairy'], 'fairy': ['fighting', 'dragon', 'dark']
}

REGRAS_DISPONIVEIS = {
    "GEN >": lambda p1, p2: p1['Geracao'] > p2['Geracao'],
    "GEN <": lambda p1, p2: p1['Geracao'] < p2['Geracao'],
    "GEN =": lambda p1, p2: p1['Geracao'] == p2['Geracao'],
    "STAGE >": lambda p1, p2: p1['Estagio'] > p2['Estagio'],
    "STAGE <": lambda p1, p2: p1['Estagio'] < p2['Estagio'],
    "STAGE =": lambda p1, p2: p1['Estagio'] == p2['Estagio'],
    "TYPE =": lambda p1, p2: bool(set(p1['Tipos']) & set(p2['Tipos'])),
    "BEATS >": lambda p1, p2: any(tipo in SUPER_EFETIVO.get(p1['Tipos'][0], []) for tipo in p2['Tipos'])
}

# ==========================================
# 3. O CÉREBRO (RESOLUTOR)
# ==========================================
def resolver_puzzle(nomes_pokemons, regras_escolhidas):
    fichas = []
    for nome in nomes_pokemons:
        ficha = pegar_ficha_pokemon(nome)
        if isinstance(ficha, str):
            return None, ficha
        fichas.append(ficha)
        
    todas_as_ordens = list(itertools.permutations(fichas))
    
    for ordem in todas_as_ordens:
        deu_match = True
        for i in range(5):
            if not REGRAS_DISPONIVEIS[regras_escolhidas[i]](ordem[i], ordem[i+1]):
                deu_match = False
                break 
        if deu_match:
            return [p['Nome'] for p in ordem], "Sucesso"
            
    return None, "Nenhuma combinação bateu."

# ==========================================
# 4. A INTERFACE GRÁFICA (O SITE)
# ==========================================

# Configurações da página
st.set_page_config(page_title="PokéSort Solver", page_icon="🎮", layout="centered")

st.title("🏆 PokéSort Solver")
st.write("Digite os 6 Pokémon misturados e escolha as regras para encontrar a ordem correta!")

# Criando 6 colunas para digitar os nomes dos Pokémon
st.subheader("1. Digite os Pokémon da tela:")
colunas_poke = st.columns(6)
pokemons = []
for i in range(6):
    with colunas_poke[i]:
        poke = st.text_input(f"Poke {i+1}", key=f"p_{i}")
        pokemons.append(poke)

# Criando 5 colunas para escolher as regras
st.subheader("2. Escolha as regras (os links):")
colunas_regras = st.columns(5)
regras = []
opcoes_regras = list(REGRAS_DISPONIVEIS.keys())

for i in range(5):
    with colunas_regras[i]:
        regra = st.selectbox(f"Link {i+1}", opcoes_regras, key=f"r_{i}")
        regras.append(regra)

st.divider()

# O Botão Mágico
if st.button("🪄 Resolver Puzzle!", use_container_width=True):
    # Verifica se os 6 campos foram preenchidos
    if all(pokemons):
        with st.spinner("Analisando 720 possibilidades..."):
            resultado, mensagem = resolver_puzzle(pokemons, regras)
            
            if resultado:
                st.success("Encontramos a ordem perfeita!")
                st.info(" ➔ ".join(resultado))
            else:
                st.error(mensagem)
    else:
        st.warning("Por favor, preencha o nome dos 6 Pokémon antes de clicar.")
