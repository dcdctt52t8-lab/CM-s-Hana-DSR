const {chromium}=require('playwright'); const fs=require('fs');
const cases=JSON.parse(fs.readFileSync(process.argv[2]));
(async()=>{const b=await chromium.launch();const p=await b.newPage();
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.route('**/rest/v1/rpc/*',r=>r.fulfill({status:200,contentType:'application/json',body:'[]'}));
await p.goto('file://'+require('path').resolve(__dirname,'../index.html'));
let pass=0; const rows=[];
for(const [k,c] of cases.entries()){
  const got=await p.evaluate(c=>{
    const set=(id,v)=>{document.getElementById(id).value=v;};
    set('income',c.income);set('new-term',c.term);set('new-rate',c.rate);set('new-amt',c.amt);
    const pick=(g,a,v)=>{document.querySelectorAll('#'+g+' .pill').forEach(x=>x.classList.toggle('sel',x.dataset[a]===String(v)));};
    pick('itype','val',c.itype);pick('dsrlim','val',c.dsrlim);pick('new-repay','val',c.repay);pick('stype','key',c.stype);
    loans=c.loans.map((l,i)=>({id:1000+i,...l})); renderLoans(); calc();
    const lim=[...document.querySelectorAll('#lim-box .lim-item')].find(x=>x.querySelector('.lk').textContent==='최대 대출 한도').querySelector('.lv').textContent;
    return {dsr:lastResult.dsr,dti:lastResult.dti,bigDsr:document.getElementById('big-dsr').textContent,bigDti:document.getElementById('big-dti').textContent,lim,
            inputs:[document.getElementById('income').value,document.getElementById('new-rate').value,document.getElementById('new-amt').value,document.getElementById('new-term').value].join('/')};
  },c);
  const e=c.expect;
  const fo=n=>n>=10000?(n/10000).toFixed(n%10000===0?0:2)+'억원':Math.round(n).toLocaleString('ko-KR')+'만원';
  const want={bigDsr:e.dsr.toFixed(1)+'%',bigDti:e.dti.toFixed(1)+'%',lim:fo(e.maxLoan)};
  const inOk=got.inputs===[c.income,c.rate,c.amt,c.term].join('/');
  const ok=inOk&&Math.abs(got.dsr-e.dsr)<=0.005001&&Math.abs(got.dti-e.dti)<=0.005001&&got.bigDsr===want.bigDsr&&got.bigDti===want.bigDti&&got.lim===want.lim;
  if(ok)pass++;
  rows.push(`${String(k+1).padStart(2)} ${ok?'OK  ':'FAIL'} | ${c.repay.padEnd(9)} ${c.stype.padEnd(12)} 기존${c.loans.map(l=>l.type).join(',')||'-'} | DSR 기준 ${e.dsr.toFixed(2)} 앱 ${(+got.dsr).toFixed(2)} | DTI 기준 ${e.dti.toFixed(2)} 앱 ${(+got.dti).toFixed(2)} | 최대한도 기준 ${want.lim} 앱 ${got.lim}${inOk?'':' [입력값 반올림됨 '+got.inputs+']'}`);
}
console.log(rows.join('\n'));console.log(`\n통과 ${pass}/${cases.length}`,'오류',errs);await b.close();})();
