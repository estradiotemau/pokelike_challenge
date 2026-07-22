import streamlit as st
import requests
import itertools
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ==========================================
# 1. MOTOR DE BUSCA (PokéAPI)
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
# 2. REGRAS DO JOGO
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
    "BEATS >": lambda p1, p2: any(tipo in SUPER_EFETIVO.get(p1['Tipos'][0], []) for tipo in p2['Tipos']),
    "BEATS <": lambda p1, p2: any(tipo in SUPER_EFETIVO.get(p2['Tipos'][0], []) for tipo in p1['Tipos'])
}

# ==========================================
# 3. O RESOLUTOR
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
# 4. O ROBÔ RASPADOR (COM CACHE DIÁRIO!)
# ttl="1d" significa que ele só raspa 1 vez por dia e guarda na memória!
# ==========================================
@st.cache_data(ttl="1d", show_spinner=False)
def buscar_desafio_automatico():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://pokelike.xyz/")
        time.sleep(3)
        
        botao_diario = driver.find_element(By.XPATH, "//*[contains(text(), 'DAILY') or contains(text(), 'Daily')]")
        botao_diario.click()
        time.sleep(3)
        
        sopa = BeautifulSoup(driver.page_source, 'html.parser')
        
        pokemons = [img['alt'].lower() for img in sopa.find_all('img', class_='pc-sprite') if 'alt' in img.attrs and img['alt']]
        regras = [label.get_text(strip=True).upper().replace(">", " >").replace("<", " <").replace("=", " =").replace("  ", " ").strip() for label in sopa.find_all('span', class_='pc-link-label')]
        
        driver.quit()
        return pokemons[:6], regras[:5]
    except Exception as e:
        return None, None

# ==========================================
# 5. A INTERFACE GRÁFICA (O SITE)
# ==========================================
st.set_page_config(page_title="PokéSort Auto-Solver", page_icon="🤖", layout="centered")

st.title("🏆 PokéSort Auto-Solver")
st.write("Um bot criado para obliterar o desafio diário do Pokelike.")

st.divider()

st.subheader("🤖 Solução Automática do Dia")
if st.button("🪄 Hackear o Desafio de Hoje", type="primary", use_container_width=True):
    with st.spinner("Acordando o robô e raspando o site... (pode demorar uns 10 segs na primeira vez do dia)"):
        pokes_dia, regras_dia = buscar_desafio_automatico()
        
        if pokes_dia and regras_dia:
            st.success(f"Dados obtidos! Pokémons: {', '.join(pokes_dia).title()} | Regras: {', '.join(regras_dia)}")
            
            with st.spinner("Calculando 720 possibilidades..."):
                resultado, mensagem = resolver_puzzle(pokes_dia, regras_dia)
                
                if resultado:
                    st.success("🎉 ORDEM PERFEITA ENCONTRADA:")
                    st.info(" ➔ ".join(resultado))
                else:
                    st.error("Erro ao resolver o puzzle com os dados raspados.")
        else:
            st.error("O robô falhou em ler o site hoje. Tente usar o modo manual abaixo.")

st.divider()

# Mantemos a opção manual como backup!
with st.expander("🛠️ Ou preencha manualmente (Modo Backup)"):
    colunas_poke = st.columns(6)
    pokemons = []
    for i in range(6):
        with colunas_poke[i]:
            poke = st.text_input(f"Poke {i+1}", key=f"p_{i}")
            pokemons.append(poke)

    colunas_regras = st.columns(5)
    regras = []
    opcoes_regras = list(REGRAS_DISPONIVEIS.keys())

    for i in range(5):
        with colunas_regras[i]:
            regra = st.selectbox(f"Link {i+1}", opcoes_regras, key=f"r_{i}")
            regras.append(regra)

    if st.button("Resolver Manualmente"):
        if all(pokemons):
            resultado, mensagem = resolver_puzzle(pokemons, regras)
            if resultado:
                st.success(" ➔ ".join(resultado))
            else:
                st.error(mensagem)
