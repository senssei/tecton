/* Readable schedule: names stay outside the time axis. */
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const date = value => value && /^\d{4}-\d{2}-\d{2}$/.test(value) ? d3.utcParse('%Y-%m-%d')(value) : null;
  const fmt = d3.utcFormat('%d %b %Y');
  function render(host, state) {
    const rows = [...(state.plateaus || []).map(p => ({...p, milestone:true})), ...(state.workPackages || [])];
    if (!rows.length) { host.innerHTML = '<p class="schedule-empty">No transformation schedule yet. Add milestones or work packages with dates to this catalog.</p>'; return; }
    const dates = rows.flatMap(r => [date(r.start_date), date(r.target_date)]).filter(Boolean);
    const packages = new Map(rows.map(r => [r.id,r.name]));
    host.innerHTML = '<p class="schedule-intro">Milestones mark target dates. Initiative bars show the declared start and end dates.</p><div class="schedule-scroll"><div class="schedule-grid"></div></div><div class="schedule-legend"><span>◆ Milestone</span><span class="schedule-progress">In progress</span><span>Planned</span><span class="schedule-completed">Completed</span><span class="schedule-cancelled">Cancelled</span><span class="schedule-current">Dashed line: today</span></div>';
    const grid = host.querySelector('.schedule-grid');
    const width = 740, pad = 30;
    const min = dates.length ? d3.min(dates) : null, max = dates.length ? d3.max(dates) : null;
    const scale = min && d3.scaleUtc().domain([d3.utcMonth.offset(min,-1),d3.utcMonth.offset(max,1)]).range([pad,width-pad]);
    const span = min ? (max-min)/86400000 : 0;
    const ticks = scale ? scale.ticks(span > 1500 ? d3.utcYear : span > 240 ? d3.utcMonth.every(3) : d3.utcMonth) : [];
    grid.innerHTML = '<div class="schedule-heading">Milestones & initiatives</div><div class="schedule-axis"></div>';
    if (scale) {
      const axis = d3.select(grid.querySelector('.schedule-axis')).append('svg').attr('width',width).attr('height',58);
      axis.append('g').attr('transform','translate(0,48)').call(d3.axisTop(scale).tickValues(ticks).tickFormat(d3.utcFormat('%b %Y')).tickSize(6)).call(g=>g.select('.domain').remove());
    }
    rows.forEach(row => {
      const start = date(row.start_date), end = date(row.target_date);
      const valid = start && end && end >= start;
      const status = String(row.status || '').replaceAll('_',' ').toLowerCase();
      const range = row.milestone ? (end ? fmt(end) : 'Date not specified') : valid ? `${fmt(start)} – ${fmt(end)}` : start && end ? 'End date precedes start date' : start ? `Starts ${fmt(start)} · end not specified` : end ? `Due ${fmt(end)} · start not specified` : 'Dates not specified';
      const label = document.createElement('div'); label.className = 'schedule-label';
      label.innerHTML = `<strong>${esc(row.name)}</strong><div>${esc(range)}</div>${status ? `<span class="schedule-status">${esc(status)}</span>` : '<span class="schedule-status">milestone</span>'}<details><summary>Details</summary><p>${esc(row.description || 'No description provided.')}</p>${row.owner ? `<p>Owner: ${esc(row.owner)}</p>` : ''}${row.depends_on?.length ? `<p>Depends on: ${row.depends_on.map(id=>esc(packages.get(id)||id)).join(', ')}</p>` : ''}</details>`;
      grid.appendChild(label);
      const track = document.createElement('div'); track.className='schedule-track'; grid.appendChild(track);
      const svg = d3.select(track).append('svg').attr('width',width).attr('height',100).attr('role','img').attr('aria-label',`${row.name}: ${range}`);
      if (!scale) return;
      svg.selectAll('.schedule-gridline').data(ticks).join('line').attr('class','schedule-gridline').attr('x1',scale).attr('x2',scale).attr('y1',0).attr('y2',100);
      if (row.milestone && end) svg.append('path').attr('class','schedule-milestone').attr('d',d3.symbol().type(d3.symbolDiamond).size(240)()).attr('transform',`translate(${scale(end)},50)`);
      else if (valid) svg.append('rect').attr('class',`schedule-bar status-${String(row.status).toLowerCase()}`).attr('x',scale(start)).attr('y',34).attr('width',Math.max(3,scale(end)-scale(start))).attr('height',32).attr('rx',6);
      else if (start || end) svg.append('circle').attr('class','schedule-milestone').attr('cx',scale(start || end)).attr('cy',50).attr('r',6);
      const today = new Date();
      if (today >= scale.domain()[0] && today <= scale.domain()[1]) svg.append('line').attr('class','schedule-today').attr('x1',scale(today)).attr('x2',scale(today)).attr('y1',0).attr('y2',100).append('title').text(`Today: ${fmt(today)}`);
    });
  }
  window.TectonRoadmap = {render};
})();
