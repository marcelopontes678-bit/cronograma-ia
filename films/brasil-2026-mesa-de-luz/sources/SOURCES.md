# SOURCES — Brazil 2026 light-table documentary

Compiled 2026-10-20. Legend: **[DL]** = downloaded here, HTTP 200 checked · **[URL-UNVERIFIED]** = identifier/URL from search results, but the host blocked or challenged us · **[NOT FOUND]** = no reliable identifier found. Nothing below is invented. Where an ID is uncertain, the entry says so.

Network reality this session: `www.stf.jus.br`, `portal.stf.jus.br`, `noticias.stf.jus.br`, `www.stj.jus.br`, `cdn.tse.jus.br`, conjur, jusbrasil and Agência Brasil are all refused by the egress proxy. WebFetch could not resolve any of these hosts either. `redir.stf.jus.br` always returns the AWS WAF challenge (202, empty body). `processo.stj.jus.br` returns 403 on its search pages. `upload.wikimedia.org` began answering **429 "request does not comply with our robot policy"** after the first two requests, even with a policy-style User-Agent. That looks like a per-IP block of the shared proxy.

---

## 1. STF — Fachin monocratic decision, HC 193.726/PR, 08/03/2021
- **Holder:** Supremo Tribunal Federal (Gabinete Min. Edson Fachin)
- **Process:** HC 193.726/PR. One secondary source (jus.com.br) indexes it as "HC 193726 ED/PR". This may be how the STF jurisprudence base classifies the 08/03 decision. Unconfirmed.
- **Date / content:** 08/03/2021. The decision declares the 13ª Vara Federal de Curitiba incompetent, annuls its decisions in the Lula cases (including the convictions) and sends the records to the SJ/DF. It is about 46 pages (per jus.com.br).
- **Legal basis for reuse:** Brazilian judicial decisions are not copyright-protected (Lei 9.610/98, art. 8º, IV).
- **docID for redir.stf.jus.br:** **[NOT FOUND]**. No public citation of a paginador docID for the monocratic decision was found.
- Official alternatives, both **[URL-UNVERIFIED]** because the host is blocked from here:
  - Fachin office press note (PDF): https://www.stf.jus.br/arquivo/cms/noticiaNoticiaStf/anexo/NotaaImprensaHC193726.pdf
  - STF news item "Fachin anula condenações de Lula e manda ações penais para Justiça Federal do DF": https://portal.stf.jus.br/noticias/verNoticiaDetalhe.asp?idConteudo=461870&ori=1
- **To get the PDF:** in a normal browser, open portal.stf.jus.br → processo HC 193726 → aba "Decisões" → decisão 08/03/2021. That gives the paginador/downloadPeca link.

## 2. STF Plenário — HC 193.726 AgR/PR, judgment 15/04/2021
- **Holder:** STF, Tribunal Pleno. Rel. Min. Edson Fachin.
- **Process:** AgR no HC 193.726/PR. The PGR's agravo was denied 8×3, confirming the incompetence of the 13ª Vara. The ementa header reads "Ementa e Acórdão 15/04/2021 PLENÁRIO AG.REG. NO HABEAS CORPUS 193.726 PARANÁ".
- **Acórdão URL (candidate):** https://redir.stf.jus.br/paginadorpub/paginador.jsp?docTP=TP&docID=757078352
  - The docID comes from two academic articles that cite it for "HC 193726 AgR, Rel. Edson Fachin, Tribunal Pleno, j. 15/04/2021": revista.defensoria.df.gov.br (art. 194) and periodicos.unicesumar.edu.br (art. 13355).
  - From here it returns **202 (AWS WAF challenge)**, so it is **not verified**. Open it in a browser to confirm.
- **Secondary copy of the same acórdão (not official host):** https://www.conjur.com.br/wp-content/uploads/2023/09/decisao-lula1.pdf (blocked here)
- **Related official PDF:** Gilmar Mendes vote in HC 193.726 AgR-AgR-AgR, https://www.stf.jus.br/arquivo/cms/noticiaNoticiaStf/anexo/HC193726AgReAgRnoAgRVotoMGM.pdf [URL-UNVERIFIED]
- **STF news items:**
  - "STF confirma anulação de condenações do ex-presidente Lula na Lava Jato": https://portal.stf.jus.br/noticias/verNoticiaDetalhe.asp?idConteudo=464261&ori=1
  - "Plenário fixa competência da Justiça Federal do DF…" (22/04/2021): https://noticias.stf.jus.br/postsnoticias/plenario-fixa-competencia-da-justica-federal-do-df-para-julgar-processos-contra-ex-presidente-lula/
- **Licence:** Lei 9.610/98 art. 8º, IV (judicial decisions are not protected).

## 3. STF — AP 470 (Mensalão) acórdão
- **Holder:** STF, Tribunal Pleno. Rel. Min. Joaquim Barbosa. Rev. Min. Ricardo Lewandowski.
- **Process:** Ação Penal 470/MG. The full acórdão is 8.405 pages and was published 22/04/2013. The 14-page ementa was published in the DJe on 19/04/2013.
- **docID:** **[NOT FOUND]**. No public citation of the paginador docID was found.
- Official URLs, all **[URL-UNVERIFIED]** (hosts blocked or challenged here):
  - Old official FTP path cited by the MPF timeline: ftp://ftp.stf.jus.br/ap470/InteiroTeor_AP470.pdf (may be retired)
  - STF news item "AP 470: baixe a íntegra do acórdão" (carries the download link): https://noticias.stf.jus.br/postsnoticias/ap-470-baixe-a-integra-do-acordao/
  - Official relatório PDF (Min. Joaquim Barbosa), usable as a "first page" prop: https://www.stf.jus.br/arquivo/cms/noticianoticiastf/anexo/relatoriomensalao.pdf
  - Official PDF of Min. Luiz Fux's vote: https://www.stf.jus.br/arquivo/cms/noticianoticiastf/anexo/ap470votominlf.pdf
- **Licence:** Lei 9.610/98 art. 8º, IV.

## 4. STJ 5ª Turma — 09/11/2021, "rachadinha" case (Flávio Bolsonaro)
- **Holder:** Superior Tribunal de Justiça, Quinta Turma
- **Process:** **EDcl no AgRg no RHC 135.206/RJ**. Rel. Min. Jesuíno Rissato (des. convocado TJDFT), vencido. The prevailing dissent was by Min. João Otávio de Noronha, joined by Ribeiro Dantas and Joel Ilan Paciornik.
  - **Confidence: high, but not seen on the STJ site.** The pieces fit together:
    - the STJ certidão of the Quinta Turma for "EDcl no AgRg no RHC 135.206 – RJ", Rel. Jesuíno Rissato, with a pedido de vista by Noronha;
    - Jusbrasil "EDcl no AgRg no RHC … RJ …-8", embargante "F. N. B.";
    - Migalhas: RHC 135.206 was the March 2021 AgRg denied 4×1;
    - Conjur/Migalhas: on 09/11/2021 the Turma accepted embargos de declaração with efeitos infringentes and annulled the cautelares of Juiz Flávio Itabaiana (27ª Vara Criminal/RJ).
- **Registro number:** not found (Jusbrasil masks it as "2020/XXXXX-8").
- **Inteiro teor URL on processo.stj.jus.br:** **[NOT FOUND]**. It needs the registro number, and the search pages return 403 here.
- **Official certidão PDF seen in search** (an earlier session/vista, not the 09/11 result): https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/COL?seq=178043964&tipo=0&nreg=&SeqCgrmaSessao=&CodOrgaoJgdr=&dt=&formato=PDF&salvar=false [URL-UNVERIFIED, host blocked]
- **To get the acórdão:** in a browser, open processo.stj.jus.br → "RHC 135206" → Inteiro Teor of the EDcl no AgRg.
- **Licence:** Lei 9.610/98 art. 8º, IV.

## 5. TJ-RJ Órgão Especial — 16/05/2022, denúncia against Flávio Bolsonaro rejected/archived
- **Holder:** Tribunal de Justiça do Estado do Rio de Janeiro, Órgão Especial
- **Facts:** Unanimous. The court followed the request of PGJ Luciano Mattos, and the relatora was Des. Maria Augusta Vaz Monteiro de Figueiredo (per Brasil de Fato). The denúncia (Nov 2020) covered Flávio, Fabrício Queiroz and 15 others. It was rejected for lack of justa causa after the STJ/STF annulments. The MP-RJ filed embargos on 08/06/2022, under segredo de justiça.
- **Process number (CNJ):** **[NOT FOUND]**. No source found prints it, and the case ran under seal.
- **Official document URL:** **[NOT FOUND]** (www.tjrj.jus.br is unreachable).
- **Best citable news items (not official):**
  - Agência Brasil, https://agenciabrasil.ebc.com.br/politica/noticia/2022-05/justica-do-rio-arquiva-processo-de-caso-de-supostas-rachadinhas. Agência Brasil text is CC BY 3.0 BR.
  - Conjur, https://conjur.com.br/2022-mai-16/tj-rj-arquiva-denuncia-flavio-bolsonaro-rachadinha/

## 6. TSE — official 1st-round 2026 presidential result (04/10/2026) — **[DL] VERIFIED**
- **Holder:** Tribunal Superior Eleitoral. Election code **6257** ("Eleição Ordinária Federal - 2026 1º Turno"). The 2nd round is code 6258. Pleito 3220, ciclo `ele2026`.
- **File:** `tse_br-c0001-e006257-u.json` (9.349 bytes, `application/json`, Last-Modified Wed, 07 Oct 2026 23:35:43 GMT, ETag 2da19dbacd44746287f057d454ed01f0)
  - URL: https://resultados.tse.jus.br/oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json
  - Fields: f="o" (oficial), totalization stamp dt 05/10/2026 12:51:05, 100,00% of sections totalized (499.248).
- **Content (verbatim from file):**
  - FLAVIO NANTES BOLSONARO (PL, nº 22): 56.104.503 votos, **47,03%** (47,027772356), status "2º turno". Vice: Alfredo Gaspar.
  - LUIZ INÁCIO LULA DA SILVA (PT, nº 13, coligação "Brasil Pronto pra Mais"): 53.879.538 votos, **45,16%** (45,162767911), status "2º turno". Vice: Geraldo Alckmin.
  - Ronaldo Caiado (PSD): 2.605.148 votos (2,18%).
  - Totals:
    - eleitorado 158.745.502
    - comparecimento 125.275.835 (78,92%)
    - abstenção 33.469.244 (21,08%)
    - válidos 119.300.788
    - brancos 2.300.798
    - nulos 3.674.249
- Also saved: `ele-c_config.json` (https://resultados.tse.jus.br/oficial/comum/config/ele-c.json), the election index listing code 6257 and date 04/10/2026.
- The `dados-simplificados/.../br-c0001-e006257-r.json` pattern returns 404 for 2026. Use the `dados/.../-u.json` file above.
- **Open-data alternative (Dados Abertos TSE, package `resultados-2026`, licence "Creative Commons Attribution"):**
  - BR totalization report: https://cdn.tse.jus.br/estatistica/sead/odsele/relatorio_resultado_totalizacao/Relatorio_Resultado_Totalizacao_2026_BR.zip
  - Presidente por seção: https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip
  - Both are listed by the CKAN API. **Not downloaded**, because cdn.tse.jus.br is refused by the proxy (403).
- **Licence:** public official data. Lei 9.610/98 art. 8º, IV (official acts). The Dados Abertos package is marked CC BY.

## 7. Wikimedia Commons images
Upload URLs were built from the MD5 of the underscored filename. Licences and authors below come from the Commons file pages as surfaced by search. commons.wikimedia.org itself is unreachable, so re-check each page before publishing.

| Use | File (Commons name) | Author / credit | Licence | Size (px) | Direct URL | Status |
|---|---|---|---|---|---|---|
| (c) Flávio portrait | Foto oficial do senador Flávio Bolsonaro (v. AgSen).jpg | Agência Senado (Senado Federal official photo, 2019; Commons version corrected RJ flag in 2026) | Attribution-only (Senado terms: free use citing source/author) | 1358 × 1441 | https://upload.wikimedia.org/wikipedia/commons/a/ad/Foto_oficial_do_senador_Fl%C3%A1vio_Bolsonaro_%28v._AgSen%29.jpg | **[DL]** 200 image/jpeg, 1.257.581 B → `Foto_oficial_do_senador_Flavio_Bolsonaro_(v._AgSen).jpg` |
| (c) Lula portrait | Foto oficial de Luiz Inácio Lula da Silva (2023–2027).jpg | Ricardo Stuckert/PR, via Palácio do Planalto Flickr, 16/02/2023 | CC BY 2.0 | 1750 × 2400 | https://upload.wikimedia.org/wikipedia/commons/f/f3/Foto_oficial_de_Luiz_In%C3%A1cio_Lula_da_Silva_%282023%E2%80%932027%29.jpg | HEAD 200 image/jpeg, 3.198.098 B. **GET then hit 429, not saved** |
| (c) Lula, full-res | Foto oficial do Presidente da República Luiz Inácio Lula da Silva.jpg | Ricardo Stuckert/PR | CC BY 2.0 (per Commons; confirm) | 3543 × 5315 (~9.67 MB) | https://upload.wikimedia.org/wikipedia/commons/9/91/Foto_oficial_do_Presidente_da_Rep%C3%BAblica_Luiz_In%C3%A1cio_Lula_da_Silva.jpg | 429, not verified |
| (c) Flávio 3x4 crop | Foto oficial do senador Flávio Bolsonaro (v. AgSen) (3x4).jpg | Agência Senado | Attribution-only | ? | https://upload.wikimedia.org/wikipedia/commons/b/b3/Foto_oficial_do_senador_Fl%C3%A1vio_Bolsonaro_%28v._AgSen%29_%283x4%29.jpg | 429, not verified |
| (a) Congress, pre-dawn/night (best fit) | Congresso Nacional (28348723292).jpg | Pedro França/Agência Senado (Flickr: Senado Federal), 2016 | CC BY 2.0 | 1416 × 2128 (portrait) | https://upload.wikimedia.org/wikipedia/commons/7/7e/Congresso_Nacional_%2828348723292%29.jpg | 429, not verified |
| (a) Congress at night, small | Congresso Nacional BR noite.jpg | Steve Evans (Flickr "babasteve") | CC BY 2.0 | 1080 × 720 (below 1500) | https://upload.wikimedia.org/wikipedia/commons/3/34/Congresso_Nacional_BR_noite.jpg | 429, not verified |
| (a) Congress, 15 s night exposure | Congresso Nacional.jpg | Flickr author (not confirmed) | CC BY-SA 2.0 | 2699 × 1829 | https://upload.wikimedia.org/wikipedia/commons/f/f3/Congresso_Nacional.jpg | 429, not verified |
| (a) Congress sunset | Pôr do sol sobre Congresso Nacional do Brasil.jpg | Dennis W. Asfour (Dasfour2022), 2012, WLM 2022 | CC BY-SA 4.0 (multi-licensed GFDL / CC BY-SA 1.0–3.0) | 4567 × 3150 | https://upload.wikimedia.org/wikipedia/commons/f/fa/P%C3%B4r_do_sol_sobre_Congresso_Nacional_do_Brasil.jpg | 429, not verified |
| (a) Congress lit green/white, evening | Congresso Nacional (30521562344).jpg | Agência Senado, 30/11/2016 | Senado Flickr (credit photographer); exact tag not confirmed | ? | https://upload.wikimedia.org/wikipedia/commons/a/a4/Congresso_Nacional_%2830521562344%29.jpg | 429, not verified |
| (b) Urna eletrônica | Urna eletrônica brasileira UE2020.jpg | TSE (Flickr); photo credit Antonio Augusto | Public Domain Mark (FlickreviewR 01/04/2024). Caveat: PDM is not a licence, and the photographer is listed as copyright holder | 3543 × 2362 (2.53 MB) | https://upload.wikimedia.org/wikipedia/commons/6/62/Urna_eletr%C3%B4nica_brasileira_UE2020.jpg | 429, not verified |
| (b) alt. urna | Brazilian DRE voting machine for 2022 elections.jpg | TSE, 13/12/2021 | Conflicting: PDM in text vs CC BY-SA 4.0 in structured data | ? | (not computed) | not tried |
| (d) STF building | Prédio do Supremo Tribunal Federal (Brasilia).jpg | Uploader's own work, 23/09/2007 | Public domain (released by author) | 2048 × 1536 | https://upload.wikimedia.org/wikipedia/commons/7/7b/Pr%C3%A9dio_do_Supremo_Tribunal_Federal_%28Brasilia%29.jpg | 429, not verified |
| (d) STF building, larger | Supreme Federal Court of Brazil.jpg | Rob Sinclair (Flickr) | CC BY-SA 2.0 | 3846 × 2563 | https://upload.wikimedia.org/wikipedia/commons/7/70/Supreme_Federal_Court_of_Brazil.jpg | 429, not verified |

**Same kind of photo for both candidates:** both are official institutional portraits. Lula's is the Planalto official presidential photo (CC BY 2.0). Flávio's is the Senado official senator photo (attribution-only Senado terms). The licences differ: both require credit, and neither is SA.

**Suggested credits:**
- "Foto: Ricardo Stuckert/PR (CC BY 2.0)"
- "Foto: Agência Senado"
- "Foto: Pedro França/Agência Senado (CC BY 2.0)"
- "Foto: TSE / Antonio Augusto (domínio público)"

**To fetch the pending images:** use a normal browser or another network. Wikimedia blocks this sandbox's IP with "robot policy" 429 responses.

---
### Files in this folder
- `tse_br-c0001-e006257-u.json`: official TSE result, 1st round 2026, President, Brazil
- `tse_u_headers.txt`: HTTP response headers for the file above
- `ele-c_config.json`: TSE election index (code 6257 = 04/10/2026 1st round)
- `Foto_oficial_do_senador_Flavio_Bolsonaro_(v._AgSen).jpg`: Agência Senado official portrait, 1358×1441
