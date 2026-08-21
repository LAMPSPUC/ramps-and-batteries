"""
Despacho de duas termicas com restricao de rampa, com e sem bateria.
Reproduz todos os numeros do conjunto de slides "Quando o preco diz a verdade":
despacho otimo, precos spot (duais de balanco), rendas de rampa, contas por
agente, adequacao de receita, recuperacao de custo e a saturacao do valor da
bateria em 2,5 MWh.

Requer scipy.  Executar:  python3 despacho-check.py
"""

from scipy.optimize import linprog

C1, C2, R = 100.0, 300.0, 25.0          # R$/MWh, R$/MWh, MWh/h
D1, D2 = 100.0, 130.0                   # MWh


def despacho(d1=D1, d2=D2, E=0.0, eps=0.0):
    """x = [g11, g21, g12, g22, e];  e = energia deslocada de t1 para t2."""
    custo = [C1, C2, C1, C2, eps]       # eps>0 desempata a favor do menor e
    r = linprog(
        custo,
        A_ub=[[-1, 0, 1, 0, 0],         # g12 - g11 <= R      (mu_1)
              [0, -1, 0, 1, 0]],        # g22 - g21 <= R      (mu_2)
        b_ub=[R, R],
        A_eq=[[1, 1, 0, 0, -1],         # g11 + g21 = d1 + e  (lambda_1)
              [0, 0, 1, 1, 1]],         # g12 + g22 + e = d2  (lambda_2)
        b_eq=[d1, d2],
        bounds=[(0, None)] * 4 + [(0, E)],
        method="highs",
    )
    assert r.success, r.message
    x = r.x
    total = C1 * (x[0] + x[2]) + C2 * (x[1] + x[3])
    return dict(x=x, custo=total, lam=r.eqlin.marginals,
                mu=-r.ineqlin.marginals, beta=-r.upper.marginals[4])


def caso(nome, E):
    s = despacho(E=E)
    g11, g21, g12, g22, e = s["x"]
    l1, l2 = s["lam"]
    mu1 = s["mu"][0]

    # preco como custo marginal de operacao: +1 MWh de demanda em uma hora
    p1 = despacho(d1=D1 + 1, E=E)["custo"] - s["custo"]
    p2 = despacho(d2=D2 + 1, E=E)["custo"] - s["custo"]

    rec1, cst1 = l1 * g11 + l2 * g12, C1 * (g11 + g12)
    rec2, cst2 = l1 * g21 + l2 * g22, C2 * (g21 + g22)
    recB = (l2 - l1) * e
    pago = l1 * D1 + l2 * D2

    print(f"\n===== {nome} (E = {E:g} MWh) =====")
    print(f"  termica 1  t1={g11:6.1f}  t2={g12:6.1f}")
    print(f"  termica 2  t1={g21:6.1f}  t2={g22:6.1f}")
    print(f"  bateria    t1={-e:6.1f}  t2={e:6.1f}")
    print(f"  custo horario  t1={C1*g11+C2*g21:9.0f}  t2={C1*g12+C2*g22:9.0f}"
          f"   total={s['custo']:9.0f}")
    print(f"  preco spot     t1={l1:9.0f}  t2={l2:9.0f}")
    print(f"     confere por diferenca finita: ({p1:.0f}, {p2:.0f})"
          f"  {'OK' if abs(p1-l1) < 1e-6 and abs(p2-l2) < 1e-6 else 'FALHA'}")
    print(f"  renda da rampa mu_1 = {mu1:.0f} = c2 - c1"
          f"  {'OK' if abs(mu1-(C2-C1)) < 1e-6 else 'FALHA'}")
    print(f"  {'agente':<14}{'receita':>10}{'custo':>10}{'lucro':>10}")
    for nm, rec, cst in (("termica 1", rec1, cst1), ("termica 2", rec2, cst2),
                         ("bateria", recB, 0.0)):
        print(f"  {nm:<14}{rec:>10.0f}{cst:>10.0f}{rec-cst:>10.0f}")
    print(f"  {'consumidores':<14}{-pago:>10.0f}")
    print(f"  {'soma':<14}{rec1+rec2+recB-pago:>10.0f}"
          f"{cst1+cst2:>10.0f}{rec1+rec2+recB-cst1-cst2:>10.0f}")
    print(f"  adequacao de receita (soma de receitas = 0): "
          f"{'OK' if abs(rec1+rec2+recB-pago) < 1e-6 else 'FALHA'}")
    print(f"  recuperacao de custo (lucros >= 0): "
          f"{'OK' if min(rec1-cst1, rec2-cst2, recB) >= -1e-9 else 'FALHA'}")
    return s, (rec1 - cst1, rec2 - cst2, recB, pago)


A, lucA = caso("Caso A, sem bateria", 0.0)
B, lucB = caso("Caso B, com bateria de 1 MWh", 1.0)

print("\n===== Comparacao =====")
print(f"  custo de operacao: {A['custo']:.0f} -> {B['custo']:.0f}"
      f"   economia = {A['custo']-B['custo']:.0f}")
print(f"  lucro da bateria = {lucB[2]:.0f}"
      f"   {'igual a economia' if abs(lucB[2]-(A['custo']-B['custo'])) < 1e-6 else 'DIVERGE'}")
print(f"  pago pelos consumidores: {lucA[3]:.0f} -> {lucB[3]:.0f}")
print(f"  lucro termica 1: {lucA[0]:.0f} -> {lucB[0]:.0f}"
      f" | termica 2: {lucA[1]:.0f} -> {lucB[1]:.0f}")
print(f"  formas fechadas: mu_1 = c2-c1 = {C2-C1:.0f};"
      f" lambda_1 = 2c1-c2 = {2*C1-C2:.0f};"
      f" lambda_2 = c2 = {C2:.0f};"
      f" spread = 2(c2-c1) = {2*(C2-C1):.0f}")

print("\n===== Saturacao: valor marginal da bateria =====")
print(f"  {'E (MWh)':>9}{'e* usado':>10}{'custo':>10}{'preco t1':>10}"
      f"{'preco t2':>10}{'beta':>8}")
for E in (0, 1, 2, 2.5, 3, 4, 6):
    s = despacho(E=E, eps=1e-6)
    print(f"  {E:>9g}{s['x'][4]:>10.2f}{s['custo']:>10.0f}"
          f"{s['lam'][0]:>10.0f}{s['lam'][1]:>10.0f}{s['beta']:>8.0f}")
print("\n  A rampa deixa de amarrar em e = 2,5 MWh, pois 30 - 2e <= 25.")
