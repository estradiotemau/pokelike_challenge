# ==========================================
# 4. O ROBÔ RASPADOR (COM CACHE DIÁRIO E DEBUG!)
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
        # TENTATIVA 1: O padrão do Streamlit Cloud (usando o que instalamos no packages.txt)
        try:
            service = Service('/usr/bin/chromedriver')
            options.binary_location = '/usr/bin/chromium'
            driver = webdriver.Chrome(service=service, options=options)
        except:
            # TENTATIVA 2: Fallback pro webdriver-manager
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
        # AGORA ELE VAI GRITAR O ERRO!
        try: driver.quit() 
        except: pass
        return None, None, f"Erro detalhado: {str(e)}"

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
        # Limpa o cache se quiser forçar o robô a rodar de novo enquanto testa
        # st.cache_data.clear() 
        
        pokes_dia, regras_dia, mensagem_robo = buscar_desafio_automatico()
        
        if pokes_dia and regras_dia:
            st.success(f"Dados obtidos! Pokémons: {', '.join(pokes_dia).title()} | Regras: {', '.join(regras_dia)}")
            
            with st.spinner("Calculando 720 possibilidades..."):
                resultado, mensagem_puzzle = resolver_puzzle(pokes_dia, regras_dia)
                
                if resultado:
                    st.success("🎉 ORDEM PERFEITA ENCONTRADA:")
                    st.info(" ➔ ".join(resultado))
                else:
                    st.error("Erro ao resolver o puzzle com os dados raspados.")
        else:
            st.error("O robô falhou em ler o site hoje.")
            # Exibe a mensagem de erro do sistema em uma caixinha preta
            st.code(mensagem_robo)

st.divider()

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
