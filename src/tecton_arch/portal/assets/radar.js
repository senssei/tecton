/* Tecton radar. D3 7.9.0 is bundled under the accompanying ISC license. */
(() => {
  'use strict';
  const rings = [
    {id:'approved',name:'Approved',color:'#34d399'},
    {id:'under_evaluation',name:'Under evaluation',color:'#60a5fa'},
    {id:'deprecated',name:'Deprecated',color:'#fbbf24'},
    {id:'prohibited',name:'Prohibited',color:'#fb7185'}
  ];
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const compare = (a,b) => a < b ? -1 : a > b ? 1 : 0;
  function normalize(technologies, applications) {
    return technologies.map(t => {
      const systems = t.realizing_system_details || applications.filter(a => (a.technologies || []).includes(t.id)).map(a => ({id:a.id,name:a.name,owner:a.owner}));
      return {...t, category:t.category || 'Uncategorized', status:String(t.status || 'unknown').toLowerCase(), systems,
        count:t.realizing_systems_count ?? systems.length};
    }).sort((a,b) => compare(a.id,b.id));
  }
  function layout(technologies, categories) {
    const nodes = technologies.filter(t => rings.some(r => r.id === t.status)).map((t,i) => ({...t, number:i+1,r:Math.min(19,11+Math.sqrt(t.count)*2)}));
    let outer = 280;
    let overlaps = false;
    for (let attempt=0;attempt<9;attempt++,outer*=1.25) {
      const boundaries = [0,.42,.62,.81,1].map(r => r*outer);
      const angleWidth = 2*Math.PI/categories.length;
      const groups = d3.group(nodes,n=>`${n.category}:${n.status}`);
      nodes.forEach(n => {
        const ring = rings.findIndex(r=>r.id===n.status);
        const sector = categories.indexOf(n.category);
        n.low = boundaries[ring]+n.r+5;
        n.high = boundaries[ring+1]-n.r-5;
        n.start = -Math.PI/2+sector*angleWidth;
        n.end = n.start+angleWidth;
        const peers=groups.get(`${n.category}:${n.status}`),slot=peers.indexOf(n);
        const theta=n.start+(slot+1)/(peers.length+1)*angleWidth;
        const radius=n.low+(n.high-n.low)*(0.35+0.3*(slot%3)/2);
        n.x=Math.cos(theta)*radius;n.y=Math.sin(theta)*radius;n.vx=n.vy=0;
        n.tx=n.x;n.ty=n.y;
      });
      function constrain() {
        nodes.forEach(n => {
          let radius=Math.max(n.low,Math.min(n.high,Math.hypot(n.x,n.y)));
          let angle=Math.atan2(n.y,n.x);
          while(angle<n.start) angle+=2*Math.PI;
          while(angle>n.start+2*Math.PI) angle-=2*Math.PI;
          const margin=categories.length>1?Math.asin(Math.min(.95,(n.r+5)/radius)):0;
          angle=Math.max(n.start+margin,Math.min(n.end-margin,angle));
          n.x=radius*Math.cos(angle);n.y=radius*Math.sin(angle);
        });
      }
      const simulation=d3.forceSimulation(nodes).randomSource(d3.randomLcg(.427))
        .force('x',d3.forceX(n=>n.tx).strength(.015))
        .force('y',d3.forceY(n=>n.ty).strength(.015))
        .force('collide',d3.forceCollide(n=>n.r+4).iterations(4)).stop();
      for(let tick=0;tick<400;tick++) { simulation.tick();constrain(); }
      overlaps=nodes.some((n,i)=>nodes.slice(i+1).some(m=>Math.hypot(n.x-m.x,n.y-m.y)<n.r+m.r+3));
      if(!overlaps) return {nodes,outer,boundaries,overlaps:false};
    }
    return {nodes:[],outer:280,boundaries:[0,117.6,173.6,226.8,280],overlaps:true};
  }
  function render(host,state) {
    const previous=host.__radar;
    const model={filters:previous?.filters || {search:'',category:'',status:'',system:'',owner:''},selected:previous?.selected || null,state};
    host.__radar=model;
    const all=normalize(state.technologies,state.applications);
    const categories=[...new Set(all.map(t=>t.category))].sort(compare);
    const systems=[...new Map(all.flatMap(t=>t.systems).map(s=>[s.id,s])).values()].sort((a,b)=>compare(a.name,b.name));
    const owners=[...new Set(systems.map(s=>s.owner).filter(Boolean))].sort(compare);
    host.className='radar-root';
    host.innerHTML=`<div class="radar-controls"><label>Search<input data-filter="search" type="search" placeholder="Technology name or ID"></label>${[
      ['category','Category',categories.map(c=>[c,c])],['status','Status',[...rings.map(r=>[r.id,r.name]),['unknown','Unknown']]],
      ['system','System',systems.map(s=>[s.id,s.name])],['owner','Owner',owners.map(o=>[o,o])]
    ].map(([key,label,options])=>`<label>${label}<select data-filter="${key}"><option value="">All</option>${options.map(([value,name])=>`<option value="${escape(value)}">${escape(name)}</option>`).join('')}</select></label>`).join('')}<button type="button" data-action="clear">Clear filters</button></div>
    <p data-role="summary" aria-live="polite"></p><div class="radar-layout"><div><div class="radar-controls"><button type="button" data-action="in" aria-label="Zoom in">+</button><button type="button" data-action="out" aria-label="Zoom out">−</button><button type="button" data-action="reset">Reset view</button></div><div class="radar-canvas"></div><div class="radar-legend">${rings.map(r=>`<span style="border-color:${r.color}">${r.name}</span>`).join('')}<span style="border-color:#fb7185">EOL: outer warning border</span></div><p>Point size shows system count. Unknown statuses appear only in the list.</p></div><div><div class="radar-detail" aria-live="polite">Select a technology to inspect its usage and impact.</div><ul class="radar-list" aria-label="Technologies"></ul></div></div>`;
    host.querySelectorAll('[data-filter]').forEach(control=>{
      control.value=model.filters[control.dataset.filter];
      control.addEventListener(control.tagName==='INPUT'?'input':'change',()=>{model.filters[control.dataset.filter]=control.value;draw();});
    });
    let svg,zoom,viewport;
    function select(technology) {
      model.selected=technology.id;
      host.querySelectorAll('.radar-list button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.id===technology.id)));
      if(svg) svg.selectAll('.radar-marker').attr('aria-pressed',n=>String(n.id===technology.id));
      const panel=host.querySelector('.radar-detail');
      panel.innerHTML=`<h3>${escape(technology.name)}</h3><p>${escape(technology.description || 'No description provided.')}</p><dl><dt>Status</dt><dd>${escape(rings.find(r=>r.id===technology.status)?.name || 'Unknown')}</dd><dt>Category</dt><dd>${escape(technology.category)}</dd><dt>End of life</dt><dd>${escape(technology.eol_date || 'Not specified')}${technology.is_eol?' <span class="radar-eol">EOL reached</span>':''}</dd><dt>Systems</dt><dd>${technology.count}</dd></dl><ul>${technology.systems.map(s=>`<li>${escape(s.name)} — ${escape(s.owner || 'Owner not specified')}</li>`).join('') || '<li>No systems use this technology.</li>'}</ul><div data-role="impact">Loading impact analysis…</div>`;
      const impact=panel.querySelector('[data-role=impact]');
      const show=report=>{
        if(!report){impact.textContent='Impact analysis unavailable.';return;}
        impact.innerHTML=`<h4>Impact analysis</h4><p>${escape(report.summary)}</p><p>Risk score: ${escape(report.risk_score ?? 'Unavailable')} / 100</p><p>Direct systems: ${escape((report.directly_affected_system_names || []).join(', ') || 'None')}</p><p>Cascading systems: ${escape((report.cascading_system_names || []).join(', ') || 'None')}</p>`;
      };
      if(state.isStatic) show(state.blastRadiusReports?.[technology.id]);
      else (window.tectonApiFetch || window.fetch)(`/api/v1/trm/blast-radius/${encodeURIComponent(technology.id)}`).then(r=>{if(!r.ok)throw Error('Unavailable');return r.json();}).then(show).catch(()=>show(null));
    }
    function draw() {
      const f=model.filters;
      const shown=all.filter(t=>(!f.search || `${t.name} ${t.id}`.toLowerCase().includes(f.search.toLowerCase()))&&(!f.category || t.category===f.category)&&(!f.status || (f.status==='unknown'?!rings.some(r=>r.id===t.status):t.status===f.status))&&(!f.system || t.systems.some(s=>s.id===f.system))&&(!f.owner || t.systems.some(s=>s.owner===f.owner)));
      host.querySelector('[data-role=summary]').textContent=`${shown.length} of ${all.length} technologies · ${shown.filter(t=>t.is_eol).length} past end of life`;
      const canvas=host.querySelector('.radar-canvas');canvas.replaceChildren();
      const list=host.querySelector('.radar-list');list.replaceChildren();
      if(!shown.length) {
        canvas.innerHTML=`<p style="padding:24px">${all.length?'No technologies match these filters.':'No technologies defined in this catalog.'}</p>`;
        host.querySelector('.radar-detail').textContent='No technology selected.';
        model.selected=null;svg=null;return;
      }
      const plotted=layout(shown,categories);
      const width=plotted.outer*2+160,center=width/2;
      svg=d3.select(canvas).append('svg').attr('viewBox',`0 0 ${width} ${width}`).attr('role','group').attr('aria-label','Technology radar: category sectors and approval status rings');
      svg.style('min-width',`${Math.max(640,width*.85)}px`);
      viewport=svg.append('g');const chart=viewport.append('g').attr('transform',`translate(${center},${center})`);
      const arc=d3.arc();
      categories.forEach((category,index)=>rings.forEach((ring,ringIndex)=>{
        chart.append('path').attr('d',arc({innerRadius:plotted.boundaries[ringIndex],outerRadius:plotted.boundaries[ringIndex+1],startAngle:index*2*Math.PI/categories.length,endAngle:(index+1)*2*Math.PI/categories.length})).attr('fill',ring.color).attr('fill-opacity',.07).attr('stroke','#475569');
      }));
      categories.forEach((category,index)=>{
        const angle=-Math.PI/2+(index+.5)*2*Math.PI/categories.length;
        chart.append('text').attr('x',Math.cos(angle)*(plotted.outer+30)).attr('y',Math.sin(angle)*(plotted.outer+30)).attr('text-anchor','middle').attr('dominant-baseline','middle').attr('fill','#e2e8f0').attr('font-size',15).text(category.length>20?category.slice(0,19)+'…':category).append('title').text(category);
      });
      rings.forEach((ring,i)=>chart.append('text').attr('x',8).attr('y',-plotted.boundaries[i+1]+18).attr('fill',ring.color).attr('font-size',12).text(ring.name));
      const markers=chart.selectAll('.radar-marker').data(plotted.nodes,n=>n.id).join('g').attr('class','radar-marker').attr('transform',n=>`translate(${n.x},${n.y})`).attr('role','button').attr('tabindex',0).attr('aria-label',n=>`${n.name}, ${n.status}, ${n.count} systems${n.is_eol?', end of life reached':''}`).on('click',(event,n)=>select(n)).on('keydown',(event,n)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();select(n);}});
      markers.append('title').text(n=>`${n.name} · ${n.count} systems${n.is_eol?' · EOL':''}`);
      markers.append('circle').attr('r',n=>n.r).attr('fill',n=>rings.find(r=>r.id===n.status).color).attr('stroke',n=>n.is_eol?'#fb7185':'#020617').attr('stroke-width',n=>n.is_eol?4:2);
      markers.append('text').attr('text-anchor','middle').attr('dominant-baseline','central').attr('fill','#020617').attr('font-size',12).attr('font-weight',700).text(n=>n.number);
      zoom=d3.zoom().scaleExtent([.5,5]).on('zoom',event=>viewport.attr('transform',event.transform));svg.call(zoom);
      const numbers=new Map(plotted.nodes.map(n=>[n.id,n.number]));
      shown.forEach(t=>{
        const item=document.createElement('li'),button=document.createElement('button');button.type='button';button.dataset.id=t.id;button.setAttribute('aria-pressed','false');
        button.innerHTML=`<strong>${numbers.get(t.id) || '—'}. ${escape(t.name)} ${t.is_eol?'<span class="radar-eol">EOL</span>':''}</strong><small>${escape(t.category)} · ${escape(rings.find(r=>r.id===t.status)?.name || 'Unknown')} · ${t.count} systems</small>`;
        button.addEventListener('click',()=>select(t));item.append(button);list.append(item);
      });
      if(plotted.overlaps) canvas.insertAdjacentHTML('beforeend','<p style="padding:16px">This catalog is too dense for readable points. Use filters or the technology list.</p>');
      const selected=shown.find(t=>t.id===model.selected);
      if(selected) select(selected);else {model.selected=null;host.querySelector('.radar-detail').textContent='Select a technology to inspect its usage and impact.';}
    }
    host.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',()=>{
      const action=button.dataset.action;
      if(action==='clear'){Object.keys(model.filters).forEach(k=>model.filters[k]='');host.querySelectorAll('[data-filter]').forEach(c=>c.value='');draw();}
      else if(svg) { if(action==='reset')svg.call(zoom.transform,d3.zoomIdentity);else svg.call(zoom.scaleBy,action==='in'?1.25:.8); }
    }));
    draw();
  }
  window.TectonRadar={render,layout,normalize};
})();
