const SEGMENTS=[{name:"Champions",color:"#6366f1",count:1136,recency:13,frequency:9.94,monetary:5147,dependency:0.35,satisfied:60},{name:"Loyal Customers",color:"#06b6d4",count:963,recency:66,frequency:4.0,monetary:1835,dependency:0.19,satisfied:70},{name:"Potential Loyalists",color:"#10b981",count:185,recency:37,frequency:1.46,monetary:1005,dependency:0.42,satisfied:33},{name:"New Customers",color:"#8b5cf6",count:234,recency:19,frequency:1.12,monetary:239,dependency:0.96,satisfied:9},{name:"Promising",color:"#f59e0b",count:200,recency:39,frequency:1.92,monetary:364,dependency:0.33,satisfied:64},{name:"At Risk",color:"#f43f5e",count:109,recency:235,frequency:3.53,monetary:1985,dependency:0.18,satisfied:63},{name:"Need Attention",color:"#f97316",count:414,recency:197,frequency:1.71,monetary:551,dependency:0.14,satisfied:42},{name:"Lost",color:"#64748b",count:1093,recency:180,frequency:1.15,monetary:361,dependency:0.13,satisfied:10}];

// Particles
const pc=document.getElementById('particles');
if(pc){for(let i=0;i<30;i++){const p=document.createElement('div');p.className='particle';const s=Math.random()*4+2;p.style.cssText=`width:${s}px;height:${s}px;left:${Math.random()*100}%;animation-duration:${Math.random()*15+8}s;animation-delay:${Math.random()*10}s;`;pc.appendChild(p);}}

// Counters
document.querySelectorAll('.counter').forEach(el=>{const target=+el.dataset.target;let cur=0;const step=target/60;const t=setInterval(()=>{cur=Math.min(cur+step,target);el.textContent=Math.floor(cur).toLocaleString();if(cur>=target)clearInterval(t);},25);});

// KPI animate
setTimeout(()=>document.querySelectorAll('[data-animate]').forEach((el,i)=>{setTimeout(()=>el.classList.add('visible'),i*120);}),200);

// Segment strip
const sg=document.getElementById('segment-grid');
if(sg){SEGMENTS.forEach(s=>{const d=document.createElement('div');d.className='seg-pill';d.style.borderColor=s.color+'55';d.innerHTML=`<span class="seg-dot" style="background:${s.color}"></span><span>${s.name}</span><span class="seg-count">${s.count.toLocaleString()}</span>`;sg.appendChild(d);});}

// SQL data
const SQL_QUERIES={
'rfm-base':{title:'RFM Base Calculation',badge:'Step 1',desc:'Computes Recency, Frequency, Monetary for every customer.',code:`-- RFM Base Query
SELECT
  customer_id,
  DATEDIFF('2011-12-10', MAX(invoice_date))   AS recency,
  COUNT(DISTINCT invoice_no)                   AS frequency,
  SUM(quantity * unit_price)                   AS monetary
FROM orders
WHERE invoice_no NOT LIKE 'C%'
  AND quantity > 0
  AND unit_price > 0
GROUP BY customer_id;`},
'segmentation':{title:'RFM Scoring & Segments',badge:'Step 2',desc:'Assigns quintile scores and maps each customer to a named segment.',code:`-- Score + Segment
WITH scores AS (
  SELECT customer_id,
    NTILE(5) OVER (ORDER BY recency DESC)   AS r,
    NTILE(5) OVER (ORDER BY frequency)      AS f,
    NTILE(5) OVER (ORDER BY monetary)       AS m
  FROM rfm_base
)
SELECT *,
  CASE
    WHEN r>=4 AND f>=4              THEN 'Champions'
    WHEN r>=2 AND f>=3 AND m>=3     THEN 'Loyal Customers'
    WHEN r<=2 AND f>=3 AND m>=3     THEN 'At Risk'
    WHEN r<=2 AND f>=2 AND m>=2     THEN 'Need Attention'
    ELSE 'Lost'
  END AS segment
FROM scores;`},
'champions':{title:'Champions — VIP Profile',badge:'Segment',desc:'Identifies Champions and their full behavioural profile.',code:`-- Champions Profile
SELECT
  customer_id,
  recency, frequency,
  ROUND(monetary,2)           AS lifetime_revenue,
  ROUND(dependency_score,3)   AS promo_dependency,
  satisfaction_flag,
  tenure_days
FROM rfm_features
WHERE segment = 'Champions'
ORDER BY monetary DESC;`},
'at-risk':{title:'At-Risk Win-Back Query',badge:'Priority',desc:'Flags At-Risk customers with revenue at stake and suggests action.',code:`-- At-Risk Win-Back
SELECT
  customer_id,
  recency,
  ROUND(monetary,0)           AS revenue,
  ROUND(dependency_score,3)   AS dependency,
  CASE
    WHEN monetary > 1000 THEN 'Tier-1: Concierge'
    WHEN monetary > 500  THEN 'Tier-2: Email Seq'
    ELSE                      'Tier-3: Monitor'
  END                         AS action
FROM rfm_features
WHERE segment = 'At Risk'
ORDER BY monetary DESC;`},
'lost':{title:'Lost — Sunset Plan',badge:'Churn',desc:'Identifies permanently churned customers for list suppression.',code:`-- Lost Segment Sunset
SELECT
  customer_id,
  recency,
  ROUND(monetary,0) AS revenue,
  CASE
    WHEN dependency_score > 0.7 THEN 'Phase Out Now'
    WHEN monetary > 300         THEN 'Last-Chance Offer'
    ELSE                             'Suppress'
  END AS recommendation
FROM rfm_features
WHERE segment = 'Lost'
ORDER BY monetary DESC;`},
'pareto':{title:'Pareto Revenue Analysis',badge:'80/20',desc:'Shows which customers drive 80% of revenue.',code:`-- Pareto Curve
SELECT
  customer_id, monetary,
  SUM(monetary) OVER (ORDER BY monetary DESC) AS cum_revenue,
  SUM(monetary) OVER ()                        AS total_revenue,
  ROUND(100.0 * ROW_NUMBER() OVER (ORDER BY monetary DESC)
        / COUNT(*) OVER (), 2)                 AS pct_customers,
  ROUND(100.0 * SUM(monetary) OVER (ORDER BY monetary DESC)
        / SUM(monetary) OVER (), 2)            AS pct_revenue
FROM rfm_features
ORDER BY monetary DESC;`},
'cohort':{title:'Cohort Retention Rate',badge:'Retention',desc:'Month-over-month retention by acquisition cohort.',code:`-- Cohort Retention
WITH cohorts AS (
  SELECT customer_id,
    DATE_FORMAT(MIN(invoice_date),'%Y-%m') AS cohort_month
  FROM orders GROUP BY customer_id
),
activity AS (
  SELECT o.customer_id, c.cohort_month,
    TIMESTAMPDIFF(MONTH, STR_TO_DATE(c.cohort_month,'%Y-%m'),
                  DATE(o.invoice_date)) AS month_number
  FROM orders o JOIN cohorts c USING(customer_id)
)
SELECT cohort_month, month_number,
  COUNT(DISTINCT customer_id) AS customers
FROM activity
GROUP BY 1,2 ORDER BY 1,2;`}
};

// SQL tabs
const tabsEl=document.getElementById('sql-tabs');
const panelsEl=document.getElementById('sql-panels');
if(tabsEl&&panelsEl){
  Object.entries(SQL_QUERIES).forEach(([key,q])=>{
    const panel=document.createElement('div');
    panel.className='sql-panel'+(key==='rfm-base'?' active':'');
    panel.id='panel-'+key;
    panel.innerHTML=`<div class="sql-block"><div class="sql-header"><span class="sql-title">${q.title}</span><div style="display:flex;gap:.5rem;align-items:center"><span class="sql-badge">${q.badge}</span><button class="copy-btn" onclick="copySQL(this,'panel-${key}')">Copy</button></div></div><div class="sql-desc">${q.desc}</div><pre class="sql-code">${q.code}</pre></div>`;
    panelsEl.appendChild(panel);
  });
  tabsEl.querySelectorAll('.tab-btn').forEach(btn=>{
    btn.addEventListener('click',()=>{
      tabsEl.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      const key=btn.dataset.tab;
      panelsEl.querySelectorAll('.sql-panel').forEach(p=>p.classList.remove('active'));
      document.getElementById('panel-'+key)?.classList.add('active');
    });
  });
}
window.copySQL=(btn,panelId)=>{
  const code=document.getElementById(panelId)?.querySelector('.sql-code')?.textContent||'';
  navigator.clipboard.writeText(code).then(()=>{btn.textContent='Copied!';btn.classList.add('copied');setTimeout(()=>{btn.textContent='Copy';btn.classList.remove('copied');},2000);});
};

// Accordion
const RETENTION={
"Champions":{color:"#6366f1",count:1136,revenue:"£5,147",dep:"0.35",actions:["💎 VIP Early Access — new-season previews 2 weeks before launch","🎁 Surprise & Delight — branded gift at order #10 milestone","📣 Brand Ambassador — referral bonus in store credit, not cash","📊 Personalised recap email — 'Your Year in Style' monthly"],promo:"No discounts — they buy without incentive",lift:"+12% referral revenue / 6mo"},
"Loyal Customers":{color:"#06b6d4",count:963,revenue:"£1,835",dep:"0.19",actions:["🔼 Category Upsell — premium tier within favourite category","🎂 Anniversary Reward — store credit at 6 & 12-month marks","📱 App-Only Perks — shift to app channel for lower CAC"],promo:"Loyalty points only — no flat % discount",lift:"+8% AOV in Q2"},
"At Risk":{color:"#f43f5e",count:109,revenue:"£1,985",dep:"0.18",actions:["📩 Win-Back 3-email sequence over 21 days","🎯 Personalised reactivation using last-purchase category","📞 Concierge call for customers with revenue > £1,000"],promo:"15% max — email 3 only, track if next purchase needs it",lift:"Recover 12% = ~£26k saved"},
"Lost":{color:"#64748b",count:1093,revenue:"£361",dep:"0.13",actions:["💌 Last-chance email: 20% offer, 30-day hard expiry","🗑️ Suppress from all lists if no response — save send cost"],promo:"Single 20% shot. Accept churn if no response.",lift:"8% reactivation target"},
"New Customers":{color:"#8b5cf6",count:234,revenue:"£239",dep:"0.96",actions:["📬 5-email welcome series over 21 days","📦 Premium unboxing + handwritten note + community QR"],promo:"No welcome discount — or cap at 10% with 45-day expiry",lift:"+10% 30-day retention"},
"Need Attention":{color:"#f97316",count:414,revenue:"£551",dep:"0.14",actions:["📖 Content-first re-engagement (trend guides, styling tips)","⭐ Review request email — prompts recall without discount"],promo:"Max 10% only after 2 content touches with no response",lift:"+5% reactivation"},
"Promising":{color:"#f59e0b",count:200,revenue:"£364",dep:"0.33",actions:["🔁 Frequency builder — 'Complete your look' at 30-day silence","💳 Loyalty enrolment push with tangible benefits"],promo:"Free shipping on 3rd order only. No % off.",lift:"+7% frequency in 90 days"},
"Potential Loyalists":{color:"#10b981",count:185,revenue:"£1,005",dep:"0.42",actions:["🚀 Second purchase trigger — free shipping within 14 days","🧩 Bundle introduction at perceived value","🏅 Automatic loyalty onboarding"],promo:"Free shipping on 2nd order only",lift:"+15% 2nd purchase conversion"}
};

const acc=document.getElementById('segments-accordion');
if(acc){
  Object.entries(RETENTION).forEach(([name,d])=>{
    const item=document.createElement('div');item.className='acc-item';
    item.innerHTML=`<div class="acc-header"><div class="acc-color" style="background:${d.color}"></div><div class="acc-info"><div class="acc-name">${name}</div><div class="acc-meta">${d.count.toLocaleString()} customers · Avg ${d.revenue} · Dependency ${d.dep}</div></div><div class="acc-kpis"><div class="acc-kpi"><div class="acc-kpi-val" style="color:${d.color}">${d.revenue}</div><div class="acc-kpi-key">Avg Revenue</div></div><div class="acc-kpi"><div class="acc-kpi-val">${d.dep}</div><div class="acc-kpi-key">Dependency</div></div></div><div class="acc-arrow">▼</div></div><div class="acc-body"><div class="acc-content"><div class="acc-strategy">${d.actions.map(a=>`<div class="strategy-item"><div class="strategy-text"><strong>${a.split('—')[0]}</strong><p>${a.split('—')[1]||''}</p></div></div>`).join('')}<div class="strategy-item" style="border-color:${d.color}44"><div class="strategy-text"><strong>🏷️ Promo Action</strong><p>${d.promo}</p></div></div></div><div style="display:flex;flex-direction:column;gap:.75rem;justify-content:center;align-items:center;padding:1rem;background:#080c14;border-radius:12px;"><div style="font-size:2rem">${d.count.toLocaleString()}</div><div style="color:#94a3b8;font-size:.8rem">Customers</div><div style="margin-top:.5rem;font-size:1.2rem;color:${d.color};font-weight:700">${d.revenue}</div><div style="color:#94a3b8;font-size:.75rem">Avg Revenue</div><div style="margin-top:1rem;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:#10b981;font-size:.8rem;padding:.4rem .8rem;border-radius:100px">${d.lift}</div></div></div></div>`;
    item.querySelector('.acc-header').addEventListener('click',()=>{item.classList.toggle('open');});
    acc.appendChild(item);
  });
}

// Playbook grid
const pg=document.getElementById('playbook-grid');
const PRIORITY_MAP={"Champions":"low","Loyal Customers":"low","At Risk":"critical","Can't Lose Them":"critical","Potential Loyalists":"medium","New Customers":"medium","Need Attention":"high","Promising":"medium","Lost":"high"};
if(pg){
  Object.entries(RETENTION).forEach(([name,d])=>{
    const p=PRIORITY_MAP[name]||'medium';
    const card=document.createElement('div');card.className='playbook-card';
    card.innerHTML=`<div class="playbook-top"><div class="playbook-header"><div class="playbook-name">${name}</div><div class="playbook-priority priority-${p}">${p.toUpperCase()}</div></div><div class="playbook-count" style="color:${d.color}">${d.count.toLocaleString()}</div><div class="playbook-subtitle">customers · ${d.revenue} avg revenue</div><div class="playbook-metrics"><div class="playbook-metric"><div class="playbook-metric-val" style="color:${d.color}">${d.dep}</div><div class="playbook-metric-key">Dependency</div></div></div></div><div class="playbook-body"><div class="campaign-list">${d.actions.map(a=>`<div class="campaign-item"><span class="campaign-bullet">◆</span><span>${a}</span></div>`).join('')}</div></div><div class="playbook-footer"><span class="lift-badge">${d.lift}</span><div class="channel-tags"><span class="channel-tag">Email</span><span class="channel-tag">CRM</span></div></div>`;
    pg.appendChild(card);
  });
}

// Nav scroll spy
window.addEventListener('scroll',()=>{
  const nav=document.getElementById('nav');
  nav?.classList.toggle('scrolled',window.scrollY>50);
  document.querySelectorAll('section[id],header[id]').forEach(s=>{
    const link=document.querySelector(`.nav-link[href="#${s.id}"]`);
    if(!link)return;
    const r=s.getBoundingClientRect();
    link.classList.toggle('active',r.top<=100&&r.bottom>100);
  });
},{passive:true});

// Intersection observer for animate
new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible');}),{threshold:.1}).observe(document.querySelector('.hero-kpis')||document.body);
