// ---- solver de duas horas, espelho do modelo validado em Python ----
const BRcum = (function(){
  let mw=[0], cost=[0], cvu=[];
  for (const [c,m] of BR.stack){ cvu.push(c); mw.push(mw[mw.length-1]+m); cost.push(cost[cost.length-1]+m*c); }
  return {mw, cost, cvu, total: mw[mw.length-1]};
})();
const R1 = BR.d1 - BR.HFIX, R2 = BR.d2 - BR.HFIX;
function thCost(q){
  if (q <= 0) return 0;
  if (q > BRcum.total + 1e-6) return Infinity;
  let lo=0, hi=BRcum.cvu.length-1;
  while (lo < hi){ const mid=(lo+hi)>>1; if (BRcum.mw[mid+1] < q) lo=mid+1; else hi=mid; }
  return BRcum.cost[lo] + (q - BRcum.mw[lo]) * BRcum.cvu[lo];
}
function runFixed(rho, e, r1, r2){
  const R = rho/100 * BR.HFLEX * BR.dt;
  const top = Math.min(r1 + e, BR.HFLEX);
  const cand = [0, top];
  for (let i=1; i<BRcum.mw.length; i++){ cand.push(r1 + e - BRcum.mw[i]); cand.push(r2 - e - BRcum.mw[i] - R); }
  for (let i=0; i<=40; i++) cand.push(top*i/40);
  let best = Infinity;
  for (const h1 of cand){
    if (h1 < 0 || h1 > top) continue;
    const h2 = Math.min(h1 + R, r2 - e, BR.HFLEX);
    if (h2 < 0) continue;
    const t1 = r1 + e - h1, t2 = r2 - e - h2;
    if (t1 < -1e-6 || t2 < -1e-6) continue;
    const c1 = thCost(Math.max(t1,0)), c2 = thCost(Math.max(t2,0));
    if (!isFinite(c1) || !isFinite(c2)) continue;
    const v = c1 + BR.W*h1 + c2 + BR.W*h2;      // dois blocos de uma hora
    if (v < best) best = v;
  }
  return best;
}
function solve(rho, E, r1, r2){
  r1 = r1===undefined ? R1 : r1;  r2 = r2===undefined ? R2 : r2;
  let best = Infinity, eBest = 0;
  for (let i=0; i<=60; i++){
    const e = E*i/60, v = runFixed(rho, e, r1, r2);
    if (v < best){ best = v; eBest = e; }
  }
  return {cost: best, e: eBest};
}
function prices(rho, E){
  const d = 10, base = solve(rho, E);
  if (!isFinite(base.cost)) return {cost:Infinity, e:0, p1:NaN, p2:NaN, spread:NaN};
  const p1 = (solve(rho, E, R1 + d, R2).cost - base.cost)/d;
  const p2 = (solve(rho, E, R1, R2 + d).cost - base.cost)/d;
  return {cost: base.cost, e: base.e, p1, p2, spread: p2 - p1};
}

// despacho otimo detalhado, para montar a liquidacao por agente
function dispatchAt(rho, e){
  const R = rho/100 * BR.HFLEX * BR.dt;
  const top = Math.min(R1 + e, BR.HFLEX);
  const cand = [0, top];
  for (let i=1; i<BRcum.mw.length; i++){ cand.push(R1 + e - BRcum.mw[i]); cand.push(R2 - e - BRcum.mw[i] - R); }
  for (let i=0; i<=40; i++) cand.push(top*i/40);
  let best = Infinity, arg = null;
  for (const h1 of cand){
    if (h1 < 0 || h1 > top) continue;
    const h2 = Math.min(h1 + R, R2 - e, BR.HFLEX);
    if (h2 < 0) continue;
    const t1 = R1 + e - h1, t2 = R2 - e - h2;
    if (t1 < -1e-6 || t2 < -1e-6) continue;
    const c1 = thCost(Math.max(t1,0)), c2 = thCost(Math.max(t2,0));
    if (!isFinite(c1) || !isFinite(c2)) continue;
    const v = c1 + BR.W*h1 + c2 + BR.W*h2;
    if (v < best){ best = v; arg = {h1, h2, t1:Math.max(t1,0), t2:Math.max(t2,0), c1, c2, e}; }
  }
  return arg;
}

// liquidacao por agente, no formato do exemplo didatico
function settle(rho, E){
  const pr = prices(rho, E);
  const d  = dispatchAt(rho, pr.e);
  if (!d || !isFinite(pr.p1)) return null;
  const p1 = pr.p1, p2 = pr.p2, e = pr.e;
  const row = (q1, q2, cost) => ({q1, q2, rec: p1*q1 + p2*q2, cost, luc: p1*q1 + p2*q2 - cost});
  const ag = {
    fix: row(BR.HFIX, BR.HFIX, 0),                    // fio d'agua: agua sem uso alternativo
    flex: row(d.h1, d.h2, BR.W*(d.h1 + d.h2)),
    term: row(d.t1, d.t2, d.c1 + d.c2),
    bat:  row(-e, e, 0),
  };
  const pago = p1*BR.d1 + p2*BR.d2;
  ag.dem = {q1: BR.d1, q2: BR.d2, rec: -pago, cost: null, luc: null};
  ag.soma = {
    rec:  ag.fix.rec + ag.flex.rec + ag.term.rec + ag.bat.rec - pago,   // adequacao de receita
    cost: ag.fix.cost + ag.flex.cost + ag.term.cost,
    luc:  ag.fix.luc + ag.flex.luc + ag.term.luc + ag.bat.luc,
  };
  return {p1, p2, e, ag};
}
