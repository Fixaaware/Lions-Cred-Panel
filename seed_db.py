"""
seed_db.py  –  Importa todos os clientes do histórico de conversa para o banco Lions Cred.
Regras:
  • Deduplicação por CPF (INSERT OR IGNORE)
  • Nomes "duplicados" (ex: "João Silva João Silva") são reduzidos à primeira metade
  • Observação "Rogério: CURVAS NÃO FAZER" adicionada quando presente no cabeçalho
  • CPFs inválidos / muito curtos são armazenados como estão (não bloqueados)
"""

import os, re, sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "lions_cred.db")

# ──────────────────────────────────────────────────────────────
RAW = """
[18/12/2025 23:47] Rogério: 31013027817
KELIANE BARROS PEREIRA
[18/12/2025 23:47] Rogério: 33131326859
FERNANDA MARUSO PASSOS HERMENEGILDO
[18/12/2025 23:52] magrelo: 37047915800
Vinicius Pereira prata
[18/12/2025 23:56] Rogério: RP2 SISTEMA RAIMUNDO	Adriana Aparecida Inácio	191.285.088-58
Rodrigo da Silva Silva	44999961278
Felipe Silva leite	48081424814
Thaina Gabrielle Barzague dos Santos	458.431.218-44
Brisa Souza Pinho	05131688698
Viviane Michele Alves de Souza	27709991840
Lidia Maria Simões da Silva	08872089670
Gislene Miranda da Silva Barros	39959083810
Rafael cristiano herrera	36159714856
Marcelo da Silva Petena	29699969873
Samira vitória cruz santos	44546429827
Guilherme Altair da Silva	45204657886
Pedro Severino de Souza nascimento	242.364.588-02
Ewerton da Silva Pereira	372.295.748-62
Izabel Cristina Alves	29048304806
Fabiana Santos da Silva	29535692860
Juliana Santos de Lima Pontes	32523323885
Cristiano Ferreira	16643413854
Julia Patti Viana cury	36622551898
Flavia Carolina dos Santos Marinho	38609199894
ISABEL CRISTINA OLIVEIRA DI PARDO	30760584877
WILLIANE LAIS GOMES APPOLINARIO	49282254810
GESSICA ANGELICE DOS SANTOS MATIAS	09445906403
Marli Aparecida Nascimento	08110180833
Juliana da Silva Souza	39546859818
Levi Otaviano Alaerse	26447547807
Angela Roberta da Silva	45447552800
GABRIEL LEITE DOS SANTOS	39513552802
Jaqueline Tambalo De Andrade	51484915828
Petrônio Ferreira do Nascimento Júnior	44147363822
Sthefany Peixoto Moura Paiva Silva	46776650870
Elaine Cristina Gomes dias	21865864870
Fernanda Bernardino	28969914846
Mariana Maria da Silva	36289468839
Vanessa Cristina da Silva Pinheiro	29628392824
Lucas Gouveia Silva Paiva	13996710292
Tamires dos Santos Barros	35622918847
Cristiane Pereira da Silva	33950705813
Alexandra Gonzalez	30918230837
Gabriela Mitie Tanno	406.466.628-30
Reginaldo Faustino Da Silva	31283938855
Bianca Pereira Lima	58679683833
Aline Ramaldes da Silva	23038795828
Vania Rodrigues dos santos	27385100864
Elaine Michely Pereira do Rego	28151673877
Zélia Maria Rocha Santos	25631245817
Elaine ricz da silva	29252006800
Bruno Laragnoit Xavier Melo	35709938840
Amanda Shizuka	48386851813
Thiago dos santos Camilo	49648028842
Franklin Kelvin frança	10783175930
Abel Lima da Silva	51407654896
Dailza da conceição Araújo	37080054818
Zélia felipe	41412935806
Jenniffer vieira da Silva	37395863895
Carolina de Campos Borges	215.763.538-69
Jefferson Luiz Prata	071.942.918-86
Jonathan Pereira de Moura	392.939.288-76
Daiana Cristina de Almeida	33932711807
Daniela Carolina Paixão	270.179.788-89
João Paulo Siqueira rosa	33794097823
Maria Ferreira de Amorim Sousa	16384507811
Andréa Barboza Fonseca	14887574886
Vitória poma Claudino da Silva	52699626830
Cláudia Cristiane conceição	13362099840
Mário Silvio de castro junior	27806119876
Márcia Aparecida rodrigues	36961261876
Bruna Cristina Ribeiro	36278798808
Dayane Bibiano da Silva	35088679866
Priscila Ingrid Ferreira da Silva	39905750727
Eduardo Vieira Carvalho	38077275826
Ricardo Cavalcanti de Lima	29858155840
Claudio Roschel	33264542870
Kelly Faria Emidio	45015101880
Graziela Alves do Couto Meira	36181301801
Adriano Batista dos santos	18571463875
WILDER GABRIEL CAFARCCHIO DE RESENDE	430.676.258-03
JEAN ALVES PEREIRA	40436043866
Antonia Eliete Silva Góes	16226994835
Fátima de Souza Viana	264.923.418-05
Silvana Aparecida da Cunha	30567409830
Leonardo Nazario	42555177892
Moisés pinto Silveira	28811033837
Giselia Maria Sobrinho	32911046846
Rebeca dos Santos Melo	480.973.438-27
Mônica Maria Souza	40715073818
Gustavo Teixeira Santos	527.842.108-80
Bruna Caroline Andres Costa Santos	429.341.408-81
Nilson Carlos Falchi Ribeiro	381.405.918-23
de Sousa Lima	427.664.588-32
Jacqueline Borges da Silva Santos	22743896833
Rubens Cardoso Neto	29824768866
Pâmela Letícia Lima carneiro de Oliveira	47971798806
Leticia de Oliveira	564.230.828-98
Ariane dias santos	44876460817
Carlos Henrique Nunes	36927875883
Adelita Luiz	29233837882
eleuterio vitorino	354.977.278-59
Marcia Rodrigues Sousa Ferreira	35600735880
Ricardo de araujo valhas	33307456814
Emerson Silva de Melo	39105178894
Cecília Inês buzunas pimenta	032.752.048-58
Aline Maria Ferreira do Nascimento	38331743822
Tatiana pereira Caetano	27774161848
Camila Cristina Costa da Silva	34014177890
Luiza Eliana Mendonça	15420377861
Monica de Oliveira	255.825.328-03
Ruana Beatriz Lopes	50212607820
[18/12/2025 23:56] Rogério: CURVAS NÃO FAZER	Vinicius Mancini Salles	23739724846
Alessandra Matos de Souza	10418035598
Henrique Camilo Rodrigues da Silva	38600709830
Edimara Ferreira Batista	31796082856
Natasha ferreira	36154906811
Erica Regina de Paula Lima	30839633866
aparecida oliveira	28147187890
Wesley bermudes	39837550899
Lucilene dos Santos Silva	42506086897
Graziele Cristina Machado	22729182802
Fernando Braz de Meneses	18050249816
Valdir Silva	44183328802
Vinícius madeira	41548088854
Cristiane trazzi	15608430808
Stefany silva	34983478884
Denner Rodrigues	15573174614
Abia Souza	35782928859
Rosemeire Rodrigues	28469105884
Kathleen Barbosa	51497162866
Fernanda Gualberto Bulie	44414500000
Yara Rosa de Oliveira	33783213851
Daiane corteiz	35677649856
Wellington pereira	33710435846
maria Silva	33789836800
Sidnei oliveira	39292454854
Jéssica Souza	47334513851
Tatiane Santos Ribeiro	21808175840
Roberta Soares santos	30389611832
Everton Pereira da Silva	39883193840
Eudu das dores dos santos	11694255859
Fábio Araújo André de Souza	29425264830
Bruna dos Santos de Jesus	49875249882
jesulino Souza	049.228.158-05
Pedro Souza	242.364.588-02
Dayane Souza Ângelo	34643271833
Jorge Luis Moreira dos Santos	33698099829
Luiz Cláudio Pereira dos Santos	63043858549
Ederson Almeida dos Santos	31038262810
Larissa Silva Pires de Moraes	47395104803
José Pereira de Souza	33989445820
Rafaela Cruz de Almeida da Silva	33831611882
Brenda Santana de Oliveira Alves	41730432875
Rafael da Silva	40107766841
Everton da Silva Santos	44102833838
Cíntia Daiane dos Santos	40138280819
Letícia Alves	47021183828
Ariane Ferreira Lima	43252607816
Mariana Stanich torres	49059501802
Rosimeire santos	329.519.598-69
Claudia Maria de Rezende	21849578877
Fernanda Marçal dias	27169253801
Carla Patrícia Moreira Vieira	70835829391
Jéssica Meira Rodrigues	10295586630
Mariana Vasques De Oliveira	45098203805
Tatiana Araújo de Almeida	22334077844
Amanda Silva França	46425521899
Bruna Almeida de Oliveira	46662394807
Jeniffer Nogueira Gomes	45502008130
Felipe Rodrigues de Paula	47764942804
Sheila da Silva Brito	38252935800
Cláudia Monalisa Ramos Ordalio	36294346819
Anderson Pergentino da Silva	26883772804
Gabriel Fernandes Bomfim	24167007827
Ludimila Teixeira	49417308874
Camila Rangel da Silva	37646032832
Sueli Dos Santos Silva	09534191850
Gabriella Pereira Dos Santos	49530015836
Josiani Abad Fernandes do Nascimento	43770656881
Bruno randelle bezerra costa	60116356367
Wilton César Júlio	31239035837
Bruna Veloso da silva melo	45659937837
Glecio Rogério manoel da silva	37506656809
Matheus Henrique da Silva Conceição	48498625866
Tatiane Alves de Souza	42379868883
Thabata Cristina Ferreira Ribeiro da Silva	33544683865
Ana Lucia leao de souza	12302710746
Pamela Gomes	36050295824
Amanda pequeno de lima	46951801894
Tatiana Santos da Silva	40982737807
Priscila Gonçalves Baptista Plínio	36259567804
Giovanne Sanches	50980867878
Isabela Vieira Rodrigues	46628340821
Tércio Unger Correa	21243173858
Bruna Caroline Jesus de Campos	40724732861
Renato Ribeiro Radi	32983337863
Ana Teresa Souza	30140211802
Ellen ines mateus do vale	36822125825
Jaqueline Santos Alves	37479197829
Laryssa Ferreira Mendes	42367365865
Silvana Cardoso Neves	37931233899
Jasmine Cristina da Silva Lima	42147264806
Josinara da Silva	06297017417
Luciana de Lima Ferreira	25183234817
Marcelo Costa Conrado dos santos	29220516845
Giulia Rodrigues de Paula	35907264829
Izete Ferreira da Silva	32062456808
Fabricia Barbosa Palma	44518856805
Fabiana Madalena da Silva	27299524899
Mara Ligia da Conceição	30465363806
Ariane Larissa da Silva	43125200890
Denise Aparecida Vieira	34464526802
Rosângela ModL 013	22477976877
Alessandra Galassi	22368959840
Paloma Macedo	39190514831
Yan Gabriel dos Santos	49105052882
Sérgio Roberto da Silva	26548864840
Camila de Araujo Silva Borges	33851538838
Tatiane Rosa dos Santos	31165689871
Rubislene Alves Santos	07540453664
Bruna Sousa Santos	54640783809
Wagner Luiz Mello Penna	34373423806
Ceres Maiara Saldanha de Lima	37845561835
Pamela Ferreira Nascimento Gomes	36628075800
Débora Monteiro Fernandez Garcia	44207658874
Daniele leite	29155056830
Diego Queiroz	41529992842
Tamirez Correa Silva Nery	46864553833
William oliveira	39109163840
Eduardo Souza	51992749884
Bruna Almeida	39983656809
Fernanda Oliveira da Silva	36251857846
Márcio ferreira	04873120829
Marcos de Oliveira Pereira	33516862858
jesulino Souza dup	04922815805
Carina santos	03848348500
Alessandro santos	39533365846
Marcos Silva	36697336803
Amanda Silva	42183228806
Camila santos	38549257869
Gisele galleti	36263859814
Arielson santos	47951620858
Paulo Nunes	46727562890
Taiara Ribeiro do Nascimento	49289852819
Lucas Ferreira dos Santos	49648919844
[18/12/2025 23:57] Rogério: CURVAS NÃO FAZER	Valdineia Alves Rodrigues Ferreira	36195311880
Edilson Carlos Costa	29486473803
Milene Sara Fischer de Oliveira	40730574806
Maria Eduarda Santiago lima	41559820802
Brenda Emanuele Rodrigues Borba	50732835895
Pedro José dos Santos neto	44796490850
Antonia Izadora Freitas Martins	47436723847
Elton Lina dos santos	09567948828
Luciene Magalhães Pinto	22577195818
Tainã Mayara Rocha de lima	41507784856
Isabel Emilly de Souza	48256526890
Beatriz Fernandes de Matos	44227411874
Kátia alessandrina Cardoso	33491184886
Wellington Fernando Sales	44567845803
Felipe Alves Sousa	43712721854
Caroline Silva Souza	42040237895
Lucineide marques soares	17991598845
Carina Alexandra Castor Correa	30221853839
Kamilly Marques	51669734889
elivelton aparecido baia góis	43207688845
Tiago Alves da Silva	39621037832
KEVIN HENRIQUE DE OLIVEIRA GONÇALVES	49167997805
Anderson da Silva oliveira	38918328850
Iago carriel leite de oliveira	44058176857
Larissa violante Ferreira Tenório	39892630807
Tatiane Alves de sousa	423.798.688-83
Simone maria dos Santos	286.368.948-75
Martins de Sá	45409223861
Anderson Henrique de melo	50693857803
André Rodrigues da Silva	33436605824
Guilherme Teixeira de Lima	42975876882
Luciana Cordeiro	30287267857
Jorge Luís Sansigolo Ribeiro	22185850814
Jéssica Letícia Zanqui Moreno	41121196829
Aretha Michele Bueno de Sant Ana dos santos	310.459.618-25
Péricles Ribeiro Miguel	47096601821
Joyce Caroline Ferreira da Silva França	702.499.814-83
Ederson bonifácio Catarino	48964974816
Rafaelle Moreirw Franca	60507474317
Lucas Gomes de Santana	480.537.478-09
Isabella Carvalho Luciano	443.276.088-58
Denise Andrade Ramos	36935969808
Ana Beatriz da Silva Peixoto	47706571882
Bruna Paulino lima	47406096810
Tathiana Vieira do Amaral	316.912.178-24
Luciana Aparecida Sigoli	28985189808
Ricardo Barbosa Vicente	38253708874
Luan da Silva carneiro	44808299895
Jeferson Gonçalves tome	118.570.976-29
Luciana santana Sousa Anhaia	33351556888
Luiz Carlos Miranda Junior	37046350817
Sara Araújo da Silva	22663652822
Vanessa Angélica Moraes da Silva	31858259851
Suzana Cavalcanti de Moura	325.776.608-47
Gabriele dos santos Silveira	37344871882
Gustavo Borges da Silva	38248351858
Luciano Carvalho Viana	26415777807
Néiane Borges santos	35672135808
Alexsandro de Jesus	04432647590
Amanda dias da paz	491.069.508-76
Michael Marcelino Teixeira	43914980818
LUCAS dos Santos Jorge	42013818890
Thales Antônio de Almeida	39748873854
Ketlyn Priscila Clemente Utrilha	46817208874
Elyone Alves silva	06424650458
Victor de Oliveira Souza	42871207879
Gabriel de Camargo Galli	43237879878
Erik evangelista de Almeida	55682517890
Andre Luis Santos jacintho	406.331.818-46
Rodrigo brito	377.375.448-52
Alexandre Teixeira Venturoso	30891143807
Tiago Pereira Tilhaqui	32280711893
[18/12/2025 23:58] Rogério: RP1 SISTEMA YAGO	Fernando Galtarossa	39290132825
Thamires Maria de Oliveira Silva	40035257873
Joyce de Souza Andrade	49500795817
Vanderson Coutinho Castelo Branco	64914216
David Willian do Nascimento	41310068801
Márcia Cristina da Silva Félix	34509986840
Felipe Araujo Fernandes	48259692830
Charles ferreira	40407264809
Thiago Andrade	36272025890
Silvana Scheid	72841796000
ARIANE MATOS DA SILVA	44663981860
Wellington Oliveira	46174304825
Wesley de Oliveira Santos	38108477808
Gilmar Santos da Silva	39136356883
Danielle Elisa Lopes	35449720858
Letícia Aparecida da Conceição	38671568830
Ezequiel belan junior	28872418852
Daniela de souza	36431033876
Gustavo de Souza Oliveira	398.586.968-50
Ana Carolina de Paula	31562314874
Clarisse Aparecida Sales da Silva	23083299800
Anderson da Silva	226.483.668-73
Lorayne Carolina De melo	444.606.798-25
Janeze Nepolucena	04466751812
Frederico Viccino de Santana	43648172875
Elaina Ferreira Miguel de Moraes	28247069881
Tiago Rogério Moraes de Prado	30923737820
Mariana teles da silva	37283997873
Michele monteiro dos santos	31949669874
Ana Maria da Silva Barreto	15335342846
Ezequiel Alan Viera Alves	44367923827
Matheus Henrique Bassi dos Santos	45677784800
Priscila Siqueira Oliveira Silva	37597199880
Geovani Cardoso dos santos	42693151805
Paulo Ricardo da Silva	32703668848
Jair Thome Moreno	31166223884
Ana Paula dos Santos monteiro	28018492867
Rafaela richetti Nascimento Rodrigues	39307747806
Thais Cristina Alves Santos	39933204840
Thaina Silva Santos	47406742894
Sergio Yoshiaki konaka	24842031875
Romário da Silva Nascimento	38394825850
Jackeline Pereira Rodrigues	36235430809
Aline Abreu de Oliveira	38811543886
Itala Nand Pereira silva	05598029510
Michely Regina Nascimento Silva Barbosa	31596813865
Natalia Fernanda de Souza Santos	44246319821
Mariana Alves de Carvalho	23196805867
Camila Rodrigues Da Silva	41145277888
Alessandra Cuba Rueda	25663876804
Ana Paula Paulino	13201807877
Tatiana Prestes de Albuquerque Florêncio	27808690899
Nélia de Souza Silva	09796153807
Thiago Henrique de Castro Freitas	32137739801
RAPHAEL MATIAS DO NASCIMENTO	38760067854
Márcia lopes da Silva	29208619800
Tatiana de Souza Cardoso	33941141864
Jéssica Priscila Andrade Lopes	38804604859
ANA CARLA GONÇALVES DE LIMA	45225908810
Kátia Cilene de faria	11789339880
Charles Garcia	25417115819
Shirlei costa de Souza Gonçalves	29770800821
Bruno Carvalho Furtado	32236166803
Isabela Bueno da Silva	51561758809
Tauana Conceição Ferreira	48654233893
Bianca Borghi Fernandes Vilar	22076470808
Jonathan Araújo Pierrot	38184767803
Bruno Lima Ribeiro	36501256844
Thaís Araújo Antunes	31885441894
Iana Bruna de Jesus Pereira	06852241394
katilene Michelle poma	11991220923
Keliane barros pereira	31013027817
Rodrigo Aleixo da Silva Pereira	11049345401
Silvia cantareli	314.684.788-42
Mayara Bastos de Lima Santos	46917177814
Clerisvaldo Rocha Santos	28376955802
Miria Borges frik	499.012.938-55
Ana Paula Silva	23024907890
Tatiane nascimento	41600077838
liniker Washington de Oliveira Cândido	41415397830
Suelen da Silva	41216647879
Emilly Mayara barros de souza	44915646807
Roberta da costa	02927822506
Luiz Carlos Miranda Junior	37046350817
Angélica lopes dos santos	39745028827
Vinícius Pereira prata	37047915800
William Henrique Gomes	45133682840
Camila Aparecida Vianna rocha	38489903859
Larissa Scarcelli Dallaqua	38303270800
Thaynara da silva Oliveira	38613563848
Alex Sandro de Barros	38631528838
Amanda Fernandes Menezes	31855035898
[19/12/2025 13:54] Rogério: 11049345401 Rodrigo Aleixo da Silva
[19/12/2025 13:55] Rogério: 23024907890 ANA PAULA SILVA
[19/12/2025 14:42] Rogério: 36642526830 Agatha Ximenes Pompeo
[19/12/2025 15:02] magrelo: 38760067854 Raphael matias nascimento
[22/12/2025 19:12] Rogério: 33783213851 YARA ROSA DE OLIVEIRA
[22/12/2025 19:14] magrelo: 46917177814 Mayara Bastos de Lima Santos
[22/12/2025 20:50] magrelo: 45133682840 William Henrique Gomes
[22/12/2025 20:51] magrelo: 49901293855 Mirian Borges frik
"""

TIMESTAMP_RE = re.compile(r'^\[\d{2}/\d{2}/\d{4} \d{2}:\d{2}\]\s+\S+:\s*(.*)', re.DOTALL)


def clean_cpf(raw: str) -> str:
    digits = re.sub(r'[^\d]', '', str(raw))
    return digits


def dedup_name(name: str) -> str:
    """Remove nome duplicado como 'João Silva João Silva' → 'João Silva'."""
    name = re.sub(r'\s{2,}', ' ', name).strip()
    words = name.split()
    n = len(words)
    for half in range(2, n // 2 + 1):
        if n % half != 0:
            continue
        chunk = words[:half]
        if all(words[i * half:(i + 1) * half] == chunk for i in range(1, n // half)):
            return ' '.join(chunk)
    return name


def parse_entries(raw_text: str):
    """Retorna list de (nome, cpf, obs)."""
    entries = []
    current_obs = ''

    for raw_line in raw_text.split('\n'):
        line = raw_line.strip()
        if not line:
            continue

        # Linha de timestamp: [dd/mm/yyyy hh:mm] Author: content
        ts_match = TIMESTAMP_RE.match(line)
        if ts_match:
            content = ts_match.group(1).strip()

            # Detecta CURVAS NÃO FAZER
            if 'CURVAS NÃO FAZER' in content:
                current_obs = 'Rogério: CURVAS NÃO FAZER'
                # Remove o label e continua para parsear o restante (se tab-separado)
                content = content.replace('CURVAS NÃO FAZER', '').lstrip()
            elif re.match(r'^RP[12]\s+SISTEMA', content) or re.match(r'^(?:magrelo|Rogério):\s*RP', content):
                current_obs = ''
            else:
                current_obs = ''

            if not content:
                continue

            # Verifica se é "CPF Nome" linha individual (sem tab)
            m_cpf_name = re.match(r'^([\d]{8,14})\s+(.+)', content)
            if m_cpf_name:
                cpf = clean_cpf(m_cpf_name.group(1))
                nome = dedup_name(m_cpf_name.group(2))
                entries.append((nome, cpf, current_obs))
                continue

            # Procura tab-separated na mesma linha (quando o bloco começa na linha do timestamp)
            if '\t' in content:
                # Pode ter label antes do primeiro tab: "RP2 SISTEMA RAIMUNDO\tNome\tCPF"
                parts = content.split('\t')
                # Pula o primeiro elemento se parecer label (sem dígitos suficientes)
                start = 0
                if parts[0] and not re.match(r'^[\d\s\.\-]+$', parts[0]):
                    if not re.search(r'\d{8}', parts[0]):
                        start = 1

                i = start
                while i < len(parts) - 1:
                    nome_raw = parts[i].strip()
                    cpf_raw  = parts[i + 1].strip()
                    cpf_digits = clean_cpf(cpf_raw)
                    if nome_raw and len(cpf_digits) >= 7:
                        entries.append((dedup_name(nome_raw), cpf_digits, current_obs))
                        i += 2
                    else:
                        i += 1
            continue

        # Linha de dados comum: tab-separado Nome\tCPF
        if '\t' in line:
            parts = line.split('\t')
            nome_raw = parts[0].strip()
            cpf_raw  = parts[-1].strip()
            cpf_digits = clean_cpf(cpf_raw)
            if nome_raw and len(cpf_digits) >= 7:
                entries.append((dedup_name(nome_raw), cpf_digits, current_obs))

    return entries


def insert_entries(entries):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    inserted = 0
    skipped  = 0

    for nome, cpf, obs in entries:
        if not nome:
            skipped += 1
            continue
        try:
            cur.execute(
                """INSERT OR IGNORE INTO clientes
                   (nome, cpf, telefone, email, endereco, cidade, uf, status, observacao, criado_em)
                   VALUES (?,?,?,?,?,?,?,?,?,datetime('now','localtime'))""",
                (nome, cpf, '', '', '', '', '', 'ativo', obs)
            )
            if cur.rowcount:
                inserted += 1
            else:
                skipped += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()
    return inserted, skipped


if __name__ == '__main__':
    entries = parse_entries(RAW)
    # Remove duplicatas internas (mesmo CPF, mantém primeira ocorrência)
    seen = {}
    deduped = []
    for e in entries:
        cpf_key = e[1]
        if cpf_key not in seen:
            seen[cpf_key] = True
            deduped.append(e)

    print(f"Entradas parseadas: {len(entries)}  |  Após deduplicação interna: {len(deduped)}")

    inserted, skipped = insert_entries(deduped)
    print(f"✔  Inseridos: {inserted}")
    print(f"✘  Ignorados (CPF já existe no banco): {skipped}")
