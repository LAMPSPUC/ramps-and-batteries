# Caso Brasil — dados e proveniência

Dia de referência: **quarta-feira, 4 de fevereiro de 2026**. Escolhido varrendo
180 dias de CMO semi-horário do SE (01/09/2025 a 28/02/2026) e tomando o maior
spread entre a hora de vale e a hora de ponta. É o dia mais extremo do período,
com folga: spread de R$ 4.550/MWh contra R$ 1.782 do segundo colocado.

**t1 = vale da curva do parque controlável (12h). t2 = ponta (19h).**

## De onde vem cada número

| Grandeza | Fonte | Consulta |
|---|---|---|
| Carga bruta e MMGD | ONS, carga verificada semi-horária | `ops_get_carga_verificada` |
| Hidráulica, térmica, eólica, solar por hora | ONS, balanço por subsistema | `ops_get_geracao` (SE, S, NE, N) |
| CMO semi-horário | ONS | `ops_get_cmo` |
| PLD horário | CCEE | `market_get_pld` |
| CVU por térmica (PMO Fev/2026) | ONS | `ops_get_cvu_termico` |
| Geração e pico por usina | ONS | `ops_get_geracao_usina` |
| Potência instalada | ANEEL SIGA | `list_usinas` |

## O dia

| MWmed | t1 · 12h | t2 · 19h | Δ |
|---|---:|---:|---:|
| Carga bruta | 97.168 | 99.352 | +2.185 |
| Eólica + solar | 41.281 | 5.464 | −35.816 |
| Geração distribuída | 28.428 | 278 | −28.150 |
| Hidráulica | 41.696 | 81.048 | +39.352 |
| Térmica | 8.453 | 12.064 | +3.611 |
| **Controlável** | **50.148** | **93.111** | **+42.963** |
| CMO (SE), R$/MWh | 308,5 | 2.520,6 | ×8,2 |
| PLD (SE), R$/MWh | 350,19 | 1.199,88 | ×3,4 |

Pico do CMO no dia: **R$ 4.833** às 20h, com PLD de R$ 1.558 na mesma hora.

## Cuidado com a contabilização da MMGD

As séries de **carga** e de **geração** do ONS tratam a geração distribuída em
bases diferentes: a identidade `geração = carga − MMGD − eólica − solar` **não
fecha** (sobram cerca de 20 GW ao meio-dia e zero à noite). Por isso o material
apresenta grandezas medidas lado a lado e usa como demanda do modelo a soma
medida de **hidráulica + térmica**, que é o que o parque controlável entregou e
não depende de nenhuma hipótese contábil.

## Valor da água: há diversidade?

Pouca, e é um achado que vale registrar. O valor da água publicado é um custo de
oportunidade **por subsistema**, não por usina. Em 04/02 e em 06/02 os quatro
subsistemas ficaram praticamente colados; o Sul só se descola entre 13h e 15h30
de 06/02, com no máximo R$ 24 de diferença. Não existe, nos dados abertos, um
valor da água por usina. O modelo usa um único valor, igual ao CMO da hora do
vale, e isso é fiel ao que a cadeia de modelos publica.

## Hidráulica inflexível

Separada como pedido. O **piso do dia**, 41.696 MW às 12h, é o nível que a
hidráulica não furou justamente no momento de maior sobra solar, quando havia
todo o incentivo econômico para baixar mais: fio d'água, vazão mínima, usos
múltiplos e restrições de cascata. A **parcela flexível** é a diferença até a
ponta, 39.352 MW. O percentual de rampa do modelo incide **só sobre a parcela
flexível**. A rampa observada entre o vale e a ponta foi 5.622 MW/h, ou
**14,3%/h do parque flexível** (seria 6,9%/h se medida sobre a hidráulica total,
que é a forma errada de olhar).

## A pilha

`stack.json`: 73 unidades, 23.190 MW, CVU de R$ 0 a R$ 2.319,64/MWh, do PMO de
fevereiro de 2026 (mesma semana operativa do dia). Capacidade por CEG do SIGA
para 61 unidades; GNA I (1.338 MW) e GNA II (1.673 MW) por busca nominal; para
10 unidades que geraram no dia mas não casaram por CEG, o pico observado, que é
limite inferior da capacidade. Cobertura de cerca de 86% da térmica de ponta.

## O modelo

Duas horas, hidráulica flexível limitada por rampa ao valor da água, pilha
térmica flexível, bateria despachada de forma ótima. `modelo.py` é a referência
e o solver em JavaScript do deck reproduz seus resultados.

Validação: com a rampa observada de 14,3%/h o modelo devolve térmica de 12.063 MW
na ponta contra **12.064 medidos**.

| Rampa da hidro flexível | Preço t1 | Preço t2 | Spread |
|---|---:|---:|---:|
| 14,3%/h (o dia) | 309 | 446 | 137 |
| 12%/h | 116 | 501 | 385 |
| 10%/h | −190 | 807 | 996 |
| 8%/h | −395 | 1.012 | 1.407 |

O modelo é conservador: pelo mecanismo de rampa e ordem de mérito sozinho, o
spread do dia seria R$ 137, e o sistema precificou R$ 2.212. A diferença está em
tudo o que um modelo de duas horas não carrega (reserva, rede, unit commitment,
valor da água subindo na ponta). O modelo serve para mostrar o mecanismo e a
sensibilidade, não para reproduzir o CMO.

## O que cada slide mostra

**Slide 8.** A curva do dia. Três linhas no eixo da esquerda, em MW: carga bruta,
eólica mais solar, e a demanda líquida, que é o que o parque controlável precisa
atender. O CMO entra em barras no eixo da direita, em escala própria e com
transparência, para não competir com as curvas. O vale e a ponta ficam marcados
com ponto e rótulo.

**Slide 9.** A pilha de ordem de mérito, com a hidráulica separada em inflexível
e flexível, mais dois controles (rampa da hidráulica flexível e tamanho da
bateria) e, abaixo deles, a **liquidação do dia por agente**, no mesmo formato do
exemplo didático: receita, custo e lucro de cada agente, sem e com bateria, em
R$ milhões, com os preços de cada caso no cabeçalho do grupo. A tabela é viva:
recalcula a cada movimento dos controles. A coluna de receita soma zero nos dois
casos, que é a adequação de receita do exemplo didático reaparecendo com dados
reais. A hidráulica inflexível entra a custo zero, porque a água que ela usa não
tem uso alternativo naquela hora.

O resultado que a tabela torna visível: com 2.000 MWh a bateria derruba o preço
da ponta de 446 para 347 R$/MWh. A demanda passa a pagar R$ 47,8 milhões em vez
de R$ 57,0, uma economia de R$ 9,2 milhões, mas o **custo de operação cai apenas
R$ 0,2 milhão** (16,5 para 16,3). Quase tudo é transferência dos geradores
inframarginais para o consumidor, e a bateria fica com R$ 0,1 milhão. É a
explicação, em números reais, de por que o investimento privado em armazenamento
fica atrás do valor social.

## Quanto uma bateria ganharia, de fato

Arbitragem de 1 MWh com previsão perfeita, um ciclo por dia, sobre 180 dias
(01/09/2025 a 28/02/2026), submercado SE:

| Referência | R$/MWh-ano | Cobre do custo anualizado |
|---|---:|---:|
| CMO (custo marginal real) | 94.253 | 53% |
| PLD (preço efetivamente pago) | 74.012 | 42% |

Custo anualizado: R$ 142 a 213 mil por MWh-ano (US$ 200 a 300/kWh instalado,
15 anos, 10% ao ano, câmbio 5,40); a cobertura usa o ponto médio, R$ 177,5 mil.

Dois fatos que saem daí: a receita é **muito concentrada** (os 10 melhores dias
respondem por 23,6% de seis meses, e o dia 4 de fevereiro sozinho responde por
quase 10%); e os cerca de **R$ 20 mil por MWh-ano de diferença entre o CMO e o
PLD** são valor que o sistema criou e que o preço não entregou a ninguém.
