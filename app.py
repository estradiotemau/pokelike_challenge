import streamlit as st
import requests
import itertools
import time
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# ==========================================
# 1. MOTOR DE BUSCA (PokéAPI TURBINADO)
# ==========================================
def pegar_ficha_pokemon(nome_original):
    nome = nome_original.lower().strip()
    
    # Limpa pontuações que quebram a API
    nome_limpo = nome.replace(" ", "-").replace(".", "").replace("'", "").replace(":", "").replace("é", "e")
    
    # Dicionário salva-vidas para Pokémon com formas problemáticas
    mapa_formas = {
        "wormadam": "wormadam-plant", "deoxys": "deoxys-normal", "giratina": "giratina-altered",
        "shaymin": "shaymin-land", "basculin": "basculin-red-striped", "darmanitan": "darmanitan-standard",
        "tornadus": "tornadus-incarnate", "thundurus": "thundurus-incarnate", "landorus": "landorus-incarnate",
        "keldeo": "keldeo-ordinary", "meloetta": "meloetta-aria", "aegislash": "aegislash-shield",
        "pumpkaboo": "pumpkaboo-average", "gourgeist": "gourgeist-average", "oricorio": "oricorio-baile",
        "lycanroc": "lycanroc-midday", "wishiwashi": "wishiwashi-solo", "minior": "minior-red-meteor",
        "mimikyu": "mimikyu-disguised", "toxtricity": "toxtricity-amped", "eiscue": "eiscue-ice",
        "morpeko": "morpeko-full-belly", "urshifu": "urshifu-single-strike"
    }
    
    nome_api = mapa_formas.get(nome_limpo, nome_limpo)
    
    try:
        # Busca Tipos e Imagem
        url_principal = f"https://pokeapi.co/api/v2/pokemon/{nome_api}"
        resposta_principal = requests.get(url_principal)
        if resposta_principal.status_code != 200:
            return f"PokéAPI não encontrou o Pokémon: {nome_api}"
            
        dados_principais = resposta_principal.json()
        tipos = [tipo['type']['name'] for tipo in dados_principais['types']]
        imagem_url = dados_principais['sprites']['front_default']
        
        # Busca Geração, Cor e Evolução
        url_especie = f"https://pokeapi.co/api/v2/pokemon-species/{nome_limpo}"
        resposta_especie = requests.get(url_especie)
        if resposta_especie.status_code != 200:
            return f"PokéAPI não encontrou a espécie: {nome_limpo}"
            
        dados_especie = resposta_especie.json()
        cor = dados_especie['color']['name']
        
        geracao_romana = dados_especie['generation']['name'].split('-')[1]
        tabela_geracoes = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9}
        geracao = tabela_geracoes.get(geracao_romana, 0)
        
        url_evolucao = dados_especie['evolution_chain']['url']
        cadeia = requests.get(url_evolucao).json()['chain']
        
        estagio = 0
        if cadeia['species']['name'] != nome_limpo:
            for evolucao1 in cadeia['evolves_to']:
                if evolucao1['species']['name'] == nome_limpo:
                    estagio = 1
                    break
                for evolucao2 in evolucao1['evolves_to']:
                    if evolucao2['species']['name'] == nome_limpo:
                        estagio = 2
                        break

        return {
            "Nome": nome_original.capitalize(),
            "Tipos": tipos,
            "Geracao": geracao,
            "Estagio": estagio,
            "Cor": cor,
            "Imagem": imagem_url
        }
    except Exception as e:
        return f"Erro desconhecido ao processar {nome_original}: {str(e)}"

# ==========================================
# 2. REGRAS DO JOGO E ÍCONES
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
    "COLOR =": lambda p1, p2: p1['Cor'] == p2['Cor'],
    "COLOUR =": lambda p1, p2: p1['Cor'] == p2['Cor'],
    "BEATS >": lambda p1, p2: any(tipo in SUPER_EFETIVO.get(p1['Tipos'][0], []) for tipo in p2['Tipos']),
    "BEATS <": lambda p1, p2: any(tipo in SUPER_EFETIVO.get(p2['Tipos'][0], []) for tipo in p1['Tipos'])
}

ICONES_REGRAS = {
    "GEN >": "📘",
    "GEN <": "📘",
    "GEN =": "📘",
    "STAGE >": "🍬",
    "STAGE <": "🍬",
    "STAGE =": "🍬",
    "TYPE =": "🧬",
    "COLOR =": "🎨",
    "COLOUR =": "🎨",
    "BEATS >": "🥊",
    "BEATS <": "🥊"
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
            # Retorna a ficha completa (com foto e tudo) em vez de só o nome
            return list(ordem), "Sucesso"
            
    return None, "A PokéAPI buscou todos os dados, mas nenhuma combinação resolveu as regras."

# ==========================================
# 4. O ROBÔ RASPADOR
# ==========================================
@st.cache_data(show_spinner=False)
def buscar_desafio_automatico(data_str):
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    try:
        try:
            service = Service('/usr/bin/chromedriver')
            options.binary_location = '/usr/bin/chromium'
            driver = webdriver.Chrome(service=service, options=options)
        except:
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
        return pokemons[:6], regras[:5], "Sucesso"
        
    except Exception as e:
        try: driver.quit() 
        except: pass
        return None, None, f"Erro detalhado: {str(e)}"

# ==========================================
# 5. DESENHISTA DA INTERFACE
# ==========================================
def desenhar_resultado(resultado, regras):
    st.success("🎉 ORDEM PERFEITA ENCONTRADA:")
    
    # CSS injetado para a caixa verde neon estilo o jogo original
    st.markdown("""
        <style>
        .poke-box {
            border: 2px solid #4CAF50;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            background-color: #1E1E2E;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
        .poke-name {
            font-weight: bold;
            color: white;
            font-size: 14px;
            margin-top: -10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. Desenha a linha dos Pokémon
    cols = st.columns(6)
    for i, pokemon in enumerate(resultado):
        with cols[i]:
            st.markdown(f"""
                <div class="poke-box">
                    <img src="{pokemon['Imagem']}" width="100%">
                    <div class="poke-name">{pokemon['Nome']}</div>
                </div>
            """, unsafe_allow_html=True)
    
    # 2. Desenha a linha das Regras (emojis conectando)
    cols_regras = st.columns(6)
    for i in range(5):
        with cols_regras[i]:
            regra = regras[i]
            icone = ICONES_REGRAS.get(regra, "🔗")
            st.markdown(f"""
                <div style="text-align: right; padding-top: 5px;">
                    <div style="font-size: 26px;">{icone}</div>
                    <div style="font-size: 13px; color: #4CAF50; font-weight: bold; margin-top: -5px;">{regra}</div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# 6. O SITE PRINCIPAL
# ==========================================
st.set_page_config(page_title="PokéSort Auto-Solver", page_icon="🤖", layout="centered")

st.title("🏆 PokéSort Auto-Solver")
st.write("Um bot criado para obliterar o desafio diário do Pokelike.")
st.divider()
st.subheader("🤖 Solução Automática do Dia")

fuso_brasil = timezone(timedelta(hours=-3))
data_hoje_br = datetime.now(fuso_brasil).strftime("%Y-%m-%d")

if st.button("🪄 Hackear o Desafio de Hoje", type="primary", use_container_width=True):
    with st.spinner("Acordando o robô e raspando o site... (pode demorar uns 10 segs)"):
        pokes_dia, regras_dia, mensagem_robo = buscar_desafio_automatico(data_hoje_br)
        
        if pokes_dia and regras_dia:
            st.success(f"Dados obtidos! Pokémons: {', '.join(pokes_dia).title()} | Regras: {', '.join(regras_dia)}")
            
            with st.spinner("Calculando 720 possibilidades..."):
                resultado, mensagem_puzzle = resolver_puzzle(pokes_dia, regras_dia)
                
                if resultado:
                    desenhar_resultado(resultado, regras_dia)
                else:
                    st.error(f"Erro ao resolver: {mensagem_puzzle}")
        else:
            st.error("O robô falhou em ler o site hoje.")
            st.code(mensagem_robo)

st.divider()

with st.expander("🛠️ Ou preencha manualmente (Modo Backup)"):
    colunas_poke = st.columns(6)
    pokemons_manual = []
    for i in range(6):
        with colunas_poke[i]:
            poke = st.text_input(f"Poke {i+1}", key=f"p_{i}")
            pokemons_manual.append(poke)

    colunas_regras = st.columns(5)
    regras_manual = []
    opcoes_regras = list(REGRAS_DISPONIVEIS.keys())

    for i in range(5):
        with colunas_regras[i]:
            regra = st.selectbox(f"Link {i+1}", opcoes_regras, key=f"r_{i}")
            regras_manual.append(regra)

    if st.button("Resolver Manualmente"):
        if all(pokemons_manual):
            with st.spinner("Buscando dados e resolvendo..."):
                resultado, mensagem = resolver_puzzle(pokemons_manual, regras_manual)
                if resultado:
                    desenhar_resultado(resultado, regras_manual)
                else:
                    st.error(mensagem)
        else:
            st.warning("Preencha o nome dos 6 Pokémon primeiro!")
