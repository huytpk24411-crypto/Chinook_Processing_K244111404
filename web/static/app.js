import {t,number,month,language,setLanguage,translate} from './i18n.js';
import {drawChart,exportPng} from './charts.js';

const $=id=>document.getElementById(id);
const el=(tag,cls='',text=null)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==null)node.textContent=text;return node;};
const S={token:'',server:null,page:'overview',dirty:false,localBusy:false,overview:null,audit:null,rankingScope:'track',forecast:null,forecastSequence:0,
  f:{scope:'total',entity:null,method:'linear',horizon:1},explore:{scope:'track',q:'',offset:0,rows:[],count:0,detail:null,sequence:0,detailSequence:0},
  evaluation:{scope:'total',entity:'total',q:'',subset:'all',data:null,history:null,sequence:0,optionsSequence:0},notice:null};
const pageKeys=['overview','explore','forecast','evaluation','quality','method'];
const isBusy=()=>S.localBusy||S.server?.job?.status==='running';
const ready=()=>S.server?.ready&&!S.dirty;
const nameOf=item=>item.name??t(item.id==='unassigned'?'unassigned':'unknown_name');
const query=values=>new URLSearchParams(Object.entries(values).filter(([,value])=>value!==undefined&&value!==null)).toString();
function debounce(fn,wait=180){let timer;return(...args)=>{clearTimeout(timer);timer=setTimeout(()=>fn(...args),wait);};}

async function api(path,body){
  let response;
  try{response=await fetch(path,{cache:'no-store',...(body?{method:'POST',headers:{'Content-Type':'application/json','X-Chinook-Token':S.token},body:JSON.stringify(body)}:{})});}
  catch{throw{key:'network_error'};}
  let result;try{result=await response.json();}catch{throw{key:'unexpected_error'};}
  if(!response.ok)throw(result.error??{key:'unexpected_error'});
  return result;
}
const get=(route,params={})=>api(`/api/${route}?${query({revision:S.server?.revision,...params})}`);
function notice(error,type='error'){
  S.notice=typeof error==='string'?{key:error,type}:{...error,type};
  if(S.notice.key==='stale'&&!S.dirty)invalidateData();
  const node=$('notice');node.textContent=t(S.notice.key)+(S.notice.detail?` (${S.notice.detail})`:'');node.className=`notice ${type}`;node.hidden=false;
}
function clearNotice(){S.notice=null;$('notice').hidden=true;}
function toast(key){$('toast').textContent=t(key);$('toast').hidden=false;setTimeout(()=>$('toast').hidden=true,3500);}
function segment(id,value){$(id).querySelectorAll('button').forEach(button=>{const active=button.dataset.value===String(value);button.classList.toggle('active',active);button.setAttribute('aria-pressed',active);});}
function segments(id,callback){$(id).addEventListener('click',event=>{const button=event.target.closest('button');if(button&&!button.disabled){segment(id,button.dataset.value);callback(button.dataset.value);}});}
function table(target,columns,rows,onClick=null){
  const host=$(target);host.replaceChildren();const table=el('table');const head=el('thead');const tr=el('tr');
  for(const column of columns)tr.append(el('th',column.numeric?'numeric':'',column.label??t(column.key)));head.append(tr);table.append(head);const body=el('tbody');
  if(!rows.length){const row=el('tr');const cell=el('td','empty-row',t('no_results'));cell.colSpan=columns.length;row.append(cell);body.append(row);}
  for(const row of rows){const tr=el('tr');if(onClick){tr.dataset.id=row.id;tr.tabIndex=0;tr.addEventListener('click',()=>onClick(row));tr.addEventListener('keydown',event=>{if(event.key==='Enter')onClick(row);});}
    for(const column of columns){const value=row[column.key];const cell=el('td',`${column.numeric?'numeric ':''}${column.className??''}`);if(column.node)cell.append(column.node(row));else cell.textContent=column.format?column.format(value,row):String(value??'—');if(column.best?.(row))cell.classList.add('best-value');tr.append(cell);}body.append(tr);}
  table.append(body);host.append(table);
}
function nameNode(row){const div=el('div','',nameOf(row));div.append(el('small','',`ID: ${row.id}`));return div;}
function download(name,params={}){if(!ready()){notice('stale');return;}const a=el('a');a.href=`/api/download/${name}?${query({revision:S.server.revision,...params})}`;a.download=`chinook-${name}`;document.body.append(a);a.click();a.remove();}
function downloadJson(value,name){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

function renderState(){
  const state=S.server;const busy=isBusy();$('work-progress').hidden=!busy;
  const status=state?.job?.status==='running'?({connect:'connecting',filters:'loading',train:'training',forecast:'forecasting',load_model:'working'}[state.job.kind]??'working'):null;
  $('task-status').textContent=status?t(status):'';
  $('connection-badge').querySelector('.status-dot').classList.toggle('connected',!!state?.connected);
  $('connection-text').textContent=state?.connected?`MySQL · ${state.config.database}`:t('not_connected');
  $('source-name').textContent=state?.source?`MySQL · ${state.source.name}`:'';
  const readAt=state?.source?.read_at;
  $('source-read-at').textContent=readAt?t('updated_time',{time:new Intl.DateTimeFormat(language==='vi'?'vi-VN':'en-US',{hour:'2-digit',minute:'2-digit'}).format(new Date(readAt))}):'';
  $('source-read-at').title=readAt?new Intl.DateTimeFormat(language==='vi'?'vi-VN':'en-US',{dateStyle:'short',timeStyle:'medium'}).format(new Date(readAt)):'';
  $('reload-data').disabled=busy;
  document.querySelectorAll('.retry-data').forEach(button=>button.disabled=busy);
  $('apply-filters').disabled=busy||!state?.connected;
  for(const id of ['filter-start','filter-end','filter-boundaries','filter-coverage'])$(id).disabled=busy||!state?.connected;
  $('filter-dirty').hidden=!S.dirty;
  document.querySelectorAll('.data-shell').forEach(node=>node.hidden=!ready());
  document.querySelectorAll('.data-empty').forEach(node=>{node.hidden=!!ready();node.querySelector('h2').textContent=t(S.dirty?'stale':status?'loading':state?.connected?'no_data':'waiting_title');const p=node.querySelector('.empty-description');if(p)p.textContent=t(S.dirty?'':status?'working':'waiting_note');});
  $('train-model').disabled=busy||!ready()||!state?.eligible;
  $('load-model').disabled=busy||!ready();$('save-model').disabled=busy||!ready()||!state?.model;
  $('run-forecast').disabled=busy||!ready()||(S.f.scope!=='total'&&!S.f.entity);
  $('page-export').disabled=busy||(!ready()&&S.page!=='quality');
  $('forecast-export').disabled=busy||!S.forecast;
  $('forecast-model-state').textContent=t(S.f.method!=='linear'?'baseline_ready':state?.model?'model_ready':'not_trained');
  $('model-dot').classList.toggle('connected',S.f.method!=='linear'||!!state?.model);
}
function setFiltersFromServer(){
  const f=S.server.filters;const bounds=S.server.bounds;
  if(f){$('filter-start').value=f.start.slice(0,7);$('filter-end').value=f.end.slice(0,7);$('filter-boundaries').checked=f.include_boundaries;$('filter-coverage').checked=f.confirm_coverage;}
  else if(bounds){$('filter-start').value=bounds.start;$('filter-end').value=bounds.end;}
  if(bounds){for(const id of ['filter-start','filter-end']){$(id).min=bounds.start;$(id).max=bounds.end;}}
}
function invalidateData(){S.dirty=true;S.overview=null;S.explore.detail=null;S.explore.sequence++;S.explore.detailSequence++;S.evaluation.data=null;S.evaluation.sequence++;S.evaluation.optionsSequence++;clearForecast();renderState();}
function clearForecast(){S.forecast=null;S.forecastSequence++;$('forecast-result').hidden=true;$('forecast-empty').hidden=false;$('forecast-table').replaceChildren();$('forecast-chart').replaceChildren();$('forecast-reconcile-table').replaceChildren();renderState();}

async function waitJob(id){
  for(;;){await new Promise(resolve=>setTimeout(resolve,350));S.server=await api('/api/state');renderState();const job=S.server.job;if(job?.id!==id)throw{key:'stale'};if(job.status==='error')throw job.error;if(job.status==='done')return;}
}
async function perform(route,body={},onDone=null){
  if(isBusy())return;
  clearNotice();S.localBusy=true;renderState();
  try{const result=await api(`/api/${route}`,{revision:S.server?.revision,...body});S.localBusy=false;await waitJob(result.job_id);if(onDone)await onDone(result);else await refresh();}
  catch(error){S.localBusy=false;try{S.server=await api('/api/state');}catch{}notice(error);renderState();if(S.page==='quality')await loadAudit();}
  finally{S.localBusy=false;renderState();}
}
async function refresh(){
  S.server=await api('/api/state');S.dirty=false;clearForecast();setFiltersFromServer();
  if(S.server.ready){[S.overview,S.audit]=await Promise.all([get('overview'),get('audit')]);renderOverview();renderModel();}
  else{S.overview=null;await loadAudit();}
  renderState();renderAudit();await loadCurrentPage();
  if(S.server.model_notice)notice(S.server.model_notice,'info');
}

function renderOverview(){
  if(!S.overview)return;const v=S.overview,s=v.summary;
  $('metric-revenue').textContent=number(s.revenue);$('metric-mean').textContent=number(s.monthly_mean);$('metric-months').textContent=t('months_value',{n:number(s.months,0)});
  $('metric-period').textContent=`${month(s.start)} – ${month(s.end)}`;$('metric-catalog').textContent=t('catalog_counts',{tracks:number(s.tracks,0),albums:number(s.albums,0)});
  $('effective-range').textContent=`${month(s.start)} – ${month(s.end)}`;
  drawChart($('overview-chart'),{history:v.history});renderRanking();
  $('overview-reconcile').replaceChildren();for(const [key,label]of[['invoice','invoice_total'],['track','track_total'],['album','album_total']]){const row=el('div','reconcile-row');row.append(el('span','',t(label)),el('strong','',number(s[key])));$('overview-reconcile').append(row);}
  $('overview-quality-note').textContent=t(s.max_difference<=.005&&v.quality.safe_for_forecast?'quality_match':'quality_mismatch');
}
function renderRanking(){
  if(!S.overview)return;const rows=S.overview[S.rankingScope==='track'?'top_tracks':'top_albums'];$('overview-ranking').replaceChildren();
  rows.forEach((item,index)=>{const row=el('a','ranking-row');row.href='#explore';const name=el('div');name.append(el('div','rank-name',nameOf(item)),el('div','rank-id',`ID: ${item.id}`));const value=el('div','rank-value',number(item.revenue));const meter=el('meter','rank-meter');meter.value=item.revenue;meter.max=rows[0]?.revenue||1;meter.min=0;meter.setAttribute('aria-label',t('revenue'));value.append(meter);row.append(el('span','rank-number',String(index+1).padStart(2,'0')),name,value);row.addEventListener('click',()=>{S.explore.scope=S.rankingScope;S.explore.q='';S.explore.offset=0;S.explore.detail={id:item.id};segment('explore-scope',S.explore.scope);$('explore-search').value='';});$('overview-ranking').append(row);});
}

async function forecastOptions(){
  const scope=S.f.scope,q=$('forecast-search').value,sequence=S.forecastSequence;
  if(scope==='total'||!ready())return;
  try{const result=await get('catalog',{scope,q,limit:20});if(scope!==S.f.scope||q!==$('forecast-search').value||sequence!==S.forecastSequence)return;
    const host=$('forecast-options');host.replaceChildren();if(!result.rows.length)host.append(el('div','empty-row',t('no_results')));
    result.rows.forEach(row=>{const button=el('button','picker-item');button.type='button';button.append(el('span','',nameOf(row)),el('small','',`ID ${row.id}${row.revenue===0?' · '+t('never_sold_tag'):''}`));button.addEventListener('click',()=>{S.f.entity=row.id;S.f.name=row.name;$('forecast-search').value=nameOf(row);host.replaceChildren();$('forecast-selected').textContent=`${nameOf(row)} · ID: ${row.id}`;clearForecast();});host.append(button);});
  }catch(error){notice(error);}
}
function changeForecastScope(scope){S.f.scope=scope;S.f.entity=scope==='total'?'total':null;S.f.name=null;segment('forecast-scope',scope);$('forecast-picker').hidden=scope==='total';$('forecast-search').value='';$('forecast-selected').textContent='';$('forecast-options').replaceChildren();clearForecast();if(scope!=='total')forecastOptions();}
async function runForecast(){
  const sequence=S.forecastSequence;
  await perform('forecast',{scope:S.f.scope,entity:S.f.scope==='total'?'total':S.f.entity,method:S.f.method,horizon:S.f.horizon},async result=>{
    if(sequence!==S.forecastSequence)return;
    const forecast=await get('forecast',{request_id:result.request_id});if(sequence!==S.forecastSequence)return;
    S.forecast=forecast;renderForecast();
  });
}
function renderForecast(){
  if(!S.forecast)return;const f=S.forecast,req=f.request;
  $('forecast-empty').hidden=true;$('forecast-result').hidden=false;
  $('forecast-result-title').textContent=req.scope==='total'?t('total'):`${nameOf(f.entity)} · ID ${req.entity}`;
  $('forecast-origin').textContent=t('forecast_origin',{origin:month(f.history.at(-1)?.month),start:month(f.rows[0]?.month),end:month(f.rows.at(-1)?.month)});
  $('forecast-value').textContent=number(f.rows.reduce((sum,row)=>sum+row.predicted,0));$('forecast-value-label').textContent=t('forecast_sum_label',{n:req.horizon});$('forecast-method-label').textContent=t(req.method);
  drawChart($('forecast-chart'),{history:f.history,predicted:f.rows.map(row=>({month:row.month,value:row.predicted})),boundary:f.rows[0]?.month});
  table('forecast-table',[{key:'month',format:month},{key:'predicted',numeric:true,format:v=>number(v)},{key:'method',label:t('method_label'),format:t}],f.rows);
  table('forecast-reconcile-table',[{key:'month',format:month},{key:'total',label:t('total_short'),numeric:true,format:v=>number(v)},{key:'track',label:'Track',numeric:true,format:v=>number(v)},{key:'album',label:'Album',numeric:true,format:v=>number(v)},{key:'difference',numeric:true,format:v=>number(Math.abs(v)<1e-9?0:v,6)}],f.reconciliation);
  $('never-sold-note').hidden=!f.entity.never_sold;
}

async function loadExplore(){
  if(!ready())return;const state=S.explore,sequence=++state.sequence;
  try{const result=await get('catalog',{scope:state.scope,q:state.q,offset:state.offset,limit:15});if(sequence!==state.sequence)return;Object.assign(state,{rows:result.rows,count:result.count});renderExplore();if(state.detail?.id)await loadEntityDetail(state.detail.id);}
  catch(error){notice(error);}
}
function renderExplore(){
  const state=S.explore;segment('explore-scope',state.scope);
  $('explore-count').textContent=t('items_found',{n:number(state.count,0)});
  table('explore-table',[{key:'name',label:t('name'),className:'name-cell',node:nameNode},{key:'revenue',numeric:true,format:v=>number(v)},{key:'positive_months',numeric:true,format:(value,row)=>value===0?t('never_sold_tag'):number(value,0)}],state.rows,row=>loadEntityDetail(row.id));
  $('explore-page-label').textContent=t('page_range',{start:state.count?number(state.offset+1,0):0,end:number(Math.min(state.offset+15,state.count),0),count:number(state.count,0)});
  $('explore-prev').disabled=state.offset===0;$('explore-next').disabled=state.offset+15>=state.count;
  $('entity-detail').hidden=!state.detail?.history;
}
async function loadEntityDetail(id){
  const scope=S.explore.scope,sequence=++S.explore.detailSequence,revision=S.server.revision;try{const result=await get('entity',{scope,entity:id});if(scope!==S.explore.scope||sequence!==S.explore.detailSequence||revision!==S.server.revision||S.dirty)return;S.explore.detail=result;$('entity-detail').hidden=false;$('entity-detail-name').textContent=nameOf(result);$('entity-detail-description').textContent=t('entity_detail',{id:result.id,revenue:number(result.revenue),positive:result.positive_months,months:result.months});drawChart($('entity-chart'),{history:result.history});}catch(error){notice(error);}
}

function renderModel(){
  const model=S.server?.model;$('model-empty').hidden=!!model;$('model-result').hidden=!model;
  $('model-features').replaceChildren();$('model-summary').textContent=t('not_trained');
  if(!model)return;
  const window=model.allocation_window?t('months_value',{n:model.allocation_window}):t('all_history');
  $('model-summary').textContent=t('model_description',{n:model.split.deployment_fit.n,window});model.features.forEach(feature=>$('model-features').append(el('span','',feature)));
  $('model-split').replaceChildren();for(const [key,label]of[['train','train_split'],['validation','validation_split'],['test','test_split']]){const block=el('div','split-block');const period=model.split[key];block.append(el('strong','',t(label)),el('span','',t('split_range',{n:period.n,start:month(period.start),end:month(period.end)})));$('model-split').append(block);}
}
async function evaluationOptions(){
  const state=S.evaluation;if(state.scope==='total'||!ready())return;
  const scope=state.scope,q=state.q,sequence=++state.optionsSequence,revision=S.server.revision;
  try{const result=await get('catalog',{scope,q,limit:100});if(scope!==state.scope||q!==state.q||q!==$('evaluation-search').value||sequence!==state.optionsSequence||revision!==S.server.revision||!ready())return;
    $('evaluation-entity').replaceChildren();result.rows.forEach(row=>{const option=el('option','',`${nameOf(row)} · ID ${row.id}`);option.value=row.id;$('evaluation-entity').append(option);});
    const valid=result.rows.some(row=>row.id===state.entity);if(!valid)state.entity=result.rows[0]?.id??null;
    $('evaluation-entity').value=state.entity??'';await loadEvaluation();
  }catch(error){notice(error);}
}
async function loadEvaluation(){
  renderModel();const state=S.evaluation;$('evaluation-picker').hidden=state.scope==='total';
  if(!ready()||!S.server.model||!state.entity)return;
  const sequence=++state.sequence;state.data=null;$('evaluation-table').replaceChildren();$('evaluation-chart').replaceChildren();
  try{const [result,detail]=await Promise.all([get('evaluation',{scope:state.scope,entity:state.entity}),get('entity',{scope:state.scope,entity:state.entity})]);if(sequence!==state.sequence)return;state.data=result;state.history=detail.history;renderEvaluation();}
  catch(error){notice(error);}
}
function renderEvaluation(){
  const state=S.evaluation;if(!state.data)return;
  segment('evaluation-scope',state.scope);const scores=state.data.scores.filter(row=>row.subset===state.subset);
  const best=key=>Math.min(...scores.map(row=>row[key]).filter(value=>value!==null));
  table('metrics-table',[{key:'method',label:t('method_label'),className:'method-cell',format:t},...['MAE','MSE','RMSE'].map(key=>({key,label:key,numeric:true,format:v=>number(v,4),best:row=>row[key]!==null&&row[key]===best(key)})),{key:'n',numeric:true,format:v=>number(v,0)}],scores);
  const rows=state.data.rows;
  drawChart($('evaluation-chart'),{history:state.history??[],predicted:rows.filter(row=>row.method==='linear').map(row=>({month:row.month,value:row.predicted})),boundary:rows[0]?.month});
  table('evaluation-table',[{key:'month',format:month},{key:'method',label:t('method_label'),className:'method-cell',format:t},{key:'actual',numeric:true,format:v=>number(v)},{key:'predicted',numeric:true,format:v=>number(v)},{key:'error',numeric:true,format:v=>number(v)}],rows.toSorted((a,b)=>a.month.localeCompare(b.month)||a.method.localeCompare(b.method)));
}

async function loadAudit(){try{S.audit=await get('audit');}catch{S.audit=null;}}
function renderAudit(){
  const report=S.audit;$('quality-empty').hidden=!!report;$('quality-content').hidden=!report;if(!report)return;
  $('audit-title').textContent=t(report.safe_for_forecast?'audit_passed':'audit_failed');
  $('audit-banner').classList.toggle('failed',!report.safe_for_forecast);
  const sum=value=>typeof value==='object'?Object.values(value??{}).reduce((acc,v)=>acc+sum(v),0):Number(value??0);
  const integrity=['invoice_mismatches','duplicate_primary_keys','missing_line_invoice','missing_line_track','nulls','tracks_without_album','missing_track_album','negative_values'];
  $('integrity-checks').replaceChildren();for(const key of integrity){const row=el('div','check-row');row.append(el('span','',t(key)),el('strong','',number(sum(report[key]),0)));$('integrity-checks').append(row);}
  $('coverage-checks').replaceChildren();for(const key of ['date_min','date_max','calendar_months','observed_months','never_sold_tracks','never_sold_albums','track_zero_fraction','album_zero_fraction']){const value=report[key];const row=el('div','check-row');const text=key.startsWith('date_')?new Intl.DateTimeFormat(language==='vi'?'vi-VN':'en-US').format(new Date(value.replace(' ','T'))):key.endsWith('fraction')?number(value*100,2)+'%':number(value,0);row.append(el('span','',t(key)),el('strong','',text));$('coverage-checks').append(row);}
  table('audit-counts',[{key:'name',label:t('table_name')},{key:'n',label:t('row_count'),numeric:true,format:v=>number(v,0)}],Object.entries(report.table_counts).map(([name,n])=>({name,n})));
  table('audit-schema',[{key:'TABLE_NAME',label:t('table_name')},{key:'COLUMN_NAME',label:t('column_name')},{key:'COLUMN_TYPE',label:t('column_type')},{key:'IS_NULLABLE',label:t('nullable')},{key:'COLUMN_KEY',label:t('key')}],report.schema);
  table('audit-relations',[{key:'relation',label:t('relation')},{key:'missing',numeric:true,format:v=>number(v,0)}],Object.entries(report.declared_foreign_keys_missing).map(([relation,missing])=>({relation,missing})));
}

async function loadCurrentPage(){
  if(S.page==='overview')renderOverview();
  if(S.page==='forecast')renderForecast();
  if(S.page==='explore')await loadExplore();
  if(S.page==='evaluation'){if(S.evaluation.scope!=='total'&&!S.evaluation.entity)await evaluationOptions();else await loadEvaluation();}
  if(S.page==='quality'){if(!S.audit)await loadAudit();renderAudit();}
  renderState();
}
function renderPageHeading(){
  $('page-title').textContent=t(`${S.page}_title`);$('page-subtitle').textContent=t(`${S.page}_subtitle`);$('breadcrumb-page').textContent=t(S.page);
  $('page-export').hidden=S.page==='method';$('filter-bar').hidden=['method','quality'].includes(S.page);
  document.title=`Chinook · ${t(`${S.page}_title`)}`;
}
async function navigate(){
  const page=location.hash.slice(1);S.page=pageKeys.includes(page)?page:'overview';
  document.querySelectorAll('[data-view]').forEach(node=>node.hidden=node.dataset.view!==S.page);
  document.querySelectorAll('[data-page]').forEach(node=>{node.classList.toggle('active',node.dataset.page===S.page);if(node.dataset.page===S.page)node.setAttribute('aria-current','page');else node.removeAttribute('aria-current');});
  $('sidebar').classList.remove('open');renderPageHeading();await loadCurrentPage();
}
async function changeLanguage(){
  setLanguage($('language').value);translate();renderPageHeading();renderState();renderOverview();renderModel();renderAudit();renderForecast();renderExplore();renderEvaluation();
  if(S.explore.detail?.history){const detail=S.explore.detail;$('entity-detail-name').textContent=nameOf(detail);$('entity-detail-description').textContent=t('entity_detail',{id:detail.id,revenue:number(detail.revenue),positive:detail.positive_months,months:detail.months});drawChart($('entity-chart'),{history:detail.history});}
  if(S.notice)notice(S.notice,S.notice.type);
}

function bind(){
  for(const [id,value]of[['overview-ranking-scope','track'],['forecast-scope','total'],['forecast-horizon','1'],['explore-scope','track'],['evaluation-scope','total']])segment(id,value);
  $('language').value=language;$('language').addEventListener('change',changeLanguage);window.addEventListener('hashchange',navigate);
  window.addEventListener('resize',debounce(()=>{if(S.page==='overview')renderOverview();if(S.page==='forecast')renderForecast();if(S.page==='evaluation')renderEvaluation();if(S.page==='explore'&&S.explore.detail?.history)drawChart($('entity-chart'),{history:S.explore.detail.history});},120));
  $('menu-toggle').addEventListener('click',()=>$('sidebar').classList.toggle('open'));
  for(const id of ['filter-start','filter-end','filter-boundaries','filter-coverage'])$(id).addEventListener('change',invalidateData);
  $('apply-filters').addEventListener('click',()=>perform('filters',{start:$('filter-start').value,end:$('filter-end').value,include_boundaries:$('filter-boundaries').checked,confirm_coverage:$('filter-coverage').checked}));
  segments('overview-ranking-scope',value=>{S.rankingScope=value;renderRanking();});
  segments('forecast-scope',changeForecastScope);segments('forecast-horizon',value=>{S.f.horizon=Number(value);clearForecast();});
  $('forecast-method').addEventListener('change',()=>{S.f.method=$('forecast-method').value;clearForecast();});
  $('run-forecast').addEventListener('click',runForecast);
  $('forecast-search').addEventListener('input',()=>{S.f.entity=null;$('forecast-selected').textContent='';$('forecast-options').replaceChildren();clearForecast();});
  $('forecast-search').addEventListener('input',debounce(forecastOptions));$('forecast-search').addEventListener('focus',forecastOptions);
  document.addEventListener('click',event=>{if(!event.target.closest('.entity-picker'))$('forecast-options').replaceChildren();});
  $('forecast-export').addEventListener('click',()=>{if(S.forecast)download('forecast.csv',{request_id:S.forecast.request.id});});
  segments('explore-scope',value=>{S.explore.detailSequence++;Object.assign(S.explore,{scope:value,q:'',offset:0,detail:null});$('explore-search').value='';$('entity-detail').hidden=true;loadExplore();});
  $('explore-search').addEventListener('input',()=>{S.explore.sequence++;S.explore.detailSequence++;Object.assign(S.explore,{q:$('explore-search').value,offset:0,detail:null,rows:[],count:0});renderExplore();});
  $('explore-search').addEventListener('input',debounce(loadExplore));
  $('explore-prev').addEventListener('click',()=>{S.explore.offset=Math.max(0,S.explore.offset-15);loadExplore();});$('explore-next').addEventListener('click',()=>{S.explore.offset+=15;loadExplore();});
  $('entity-use-forecast').addEventListener('click',()=>{const detail=S.explore.detail;if(!detail)return;changeForecastScope(S.explore.scope);S.f.entity=detail.id;S.f.name=detail.name;$('forecast-search').value=nameOf(detail);$('forecast-selected').textContent=`${nameOf(detail)} · ID: ${detail.id}`;$('forecast-options').replaceChildren();renderState();location.hash='forecast';});
  $('train-model').addEventListener('click',()=>perform('train',{},async()=>{await refresh();toast('trained');}));
  $('load-model').addEventListener('click',()=>$('model-file').click());$('model-file').addEventListener('change',async()=>{const file=$('model-file').files[0];if(!file)return;try{if(file.size>32*1024*1024)throw{key:'model_incompatible'};const bundle=JSON.parse(await file.text());await perform('model/load',{bundle},async()=>{await refresh();toast('model_loaded');});}catch{notice('model_incompatible');}$('model-file').value='';});
  $('save-model').addEventListener('click',()=>download('model.json'));
  segments('evaluation-scope',async scope=>{S.evaluation.sequence++;Object.assign(S.evaluation,{scope,entity:scope==='total'?'total':null,q:'',data:null});$('evaluation-search').value='';$('evaluation-picker').hidden=scope==='total';$('metrics-table').replaceChildren();$('evaluation-table').replaceChildren();$('evaluation-chart').replaceChildren();if(scope==='total')await loadEvaluation();else await evaluationOptions();});
  $('evaluation-subset').addEventListener('change',()=>{S.evaluation.subset=$('evaluation-subset').value;renderEvaluation();});
  $('evaluation-search').addEventListener('input',debounce(()=>{S.evaluation.q=$('evaluation-search').value;S.evaluation.entity=null;evaluationOptions();}));
  $('evaluation-search').addEventListener('input',()=>{S.evaluation.sequence++;S.evaluation.optionsSequence++;S.evaluation.entity=null;S.evaluation.data=null;$('evaluation-entity').replaceChildren();$('evaluation-table').replaceChildren();$('evaluation-chart').replaceChildren();});
  const reload=()=>perform('refresh',{},async()=>{await refresh();toast('loaded');});
  $('reload-data').addEventListener('click',reload);
  document.querySelectorAll('.retry-data').forEach(button=>button.addEventListener('click',reload));
  $('evaluation-entity').addEventListener('change',()=>{S.evaluation.entity=$('evaluation-entity').value;loadEvaluation();});
  document.querySelectorAll('[data-png]').forEach(button=>button.addEventListener('click',async()=>{try{await exportPng($(button.dataset.png));toast('exported');}catch(error){notice(error.message==='no_data'?'no_data':'png_failed');}}));
  $('page-export').addEventListener('click',()=>{switch(S.page){case'overview':download('reconciliation.csv');break;case'forecast':if(S.forecast)download('forecast.csv',{request_id:S.forecast.request.id});else notice('no_data');break;case'explore':download('ranking.csv',{scope:S.explore.scope});break;case'evaluation':download('evaluation.csv',{scope:S.evaluation.scope});break;case'quality':if(S.audit)downloadJson(S.audit,'chinook-data-audit.json');break;}});
}

async function start(){
  setLanguage(language);translate();bind();await navigate();
  try{const boot=await api('/api/bootstrap');S.token=boot.token;S.server=boot;renderState();
    if(boot.job?.status==='running')await waitJob(boot.job.id);
    if(S.server.job?.status==='error')notice(S.server.job.error);
    await refresh();
  }catch(error){notice(error);renderState();}
}
export const applicationReady=start();
