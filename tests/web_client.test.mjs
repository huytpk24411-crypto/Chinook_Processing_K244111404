// Exercise client JavaScript against the real local HTTP API using a minimal test DOM.
// This is a protocol/state test, not browser rendering or visual QA.
import assert from 'node:assert/strict';
import fs from 'node:fs';
const base=`http://127.0.0.1:${process.env.CHINOOK_TEST_PORT??8765}`;
const ids=new Map();
class Element {
  constructor(tag){this.tagName=tag.toLowerCase();this.attributes={};this.dataset={};this.children=[];this.parentElement=null;this.events=new Map();this._text='';this._value=undefined;this.hidden=false;this.disabled=false;this.checked=false;this.className='';this.classList={toggle:(name,force)=>{const list=new Set(this.className.split(/\s+/).filter(Boolean));const active=force??!list.has(name);if(active)list.add(name);else list.delete(name);this.className=[...list].join(' ');},add:name=>this.classList.toggle(name,true),remove:name=>this.classList.toggle(name,false)};}
  set textContent(value){this._text=String(value);this.children=[];}
  get textContent(){return this._text+this.children.map(node=>node.textContent??'').join('');}
  set value(value){this._value=String(value);}
  get value(){return this._value??this.attributes.value??(this.tagName==='select'?this.children.find(child=>child.tagName==='option')?.value:'')??'';}
  setAttribute(key,value){value=String(value);this.attributes[key]=value;if(key==='id')ids.set(value,this);if(key==='class')this.className=value;if(key.startsWith('data-'))this.dataset[key.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=value;if(key==='hidden')this.hidden=true;if(key==='value')this.value=value;}
  removeAttribute(key){delete this.attributes[key];}
  append(...nodes){for(const node of nodes){this.children.push(node);node.parentElement=this;}}
  replaceChildren(...nodes){this._text='';this.children=[];this.append(...nodes);}
  addEventListener(key,fn){if(!this.events.has(key))this.events.set(key,[]);this.events.get(key).push(fn);}
  async fire(key,target=this){for(const fn of this.events.get(key)??[])await fn({target,preventDefault(){}});}
  click(){return this.fire('click');}
  matches(selector){return selector.startsWith('.')?this.className.split(/\s+/).includes(selector.slice(1)):selector.startsWith('[')?Object.hasOwn(this.attributes,selector.slice(1,-1)):this.tagName===selector;}
  querySelectorAll(selector){const result=[];for(const child of this.children){if(child.matches(selector))result.push(child);result.push(...child.querySelectorAll(selector));}return result;}
  querySelector(selector){return this.querySelectorAll(selector)[0]??null;}
  closest(selector){return this.matches(selector)?this:this.parentElement?.closest(selector)??null;}
  remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(node=>node!==this);}
}
const doc=new Element('document');const stack=[doc];const html=fs.readFileSync(new URL('../web/static/index.html',import.meta.url),'utf8');
for(const token of html.matchAll(/<!--[\s\S]*?-->|<[^>]+>|[^<]+/g)){
  const text=token[0];if(text.startsWith('<!--')||text.startsWith('<!'))continue;
  if(text.startsWith('</')){if(stack.length>1)stack.pop();continue;}
  if(text.startsWith('<')){const tag=text.match(/^<([\w-]+)/)?.[1];if(!tag)continue;const node=new Element(tag);for(const match of text.matchAll(/\s([\w:-]+)(?:="([^"]*)")?/g))node.setAttribute(match[1],match[2]??'');stack.at(-1).append(node);if(!text.endsWith('/>')&&!['meta','link','input','br','hr','img','use','path','rect','circle','ellipse'].includes(tag))stack.push(node);}
  else stack.at(-1)._text+=text.trim();
}
globalThis.document={getElementById:id=>ids.get(id)??null,querySelectorAll:selector=>doc.querySelectorAll(selector),createElement:tag=>new Element(tag),createElementNS:(ns,tag)=>new Element(tag),documentElement:doc.querySelector('html'),body:doc.querySelector('body'),addEventListener(){}};
const windowEvents=new Map();globalThis.window={addEventListener:(key,fn)=>windowEvents.set(key,fn)};globalThis.location={hash:'#overview'};
globalThis.localStorage={getItem:()=>null,setItem(){}};
const originalFetch=globalThis.fetch;globalThis.fetch=(path,options={})=>originalFetch(new URL(path,base),{...options,headers:{...options.headers,...(options.method==='POST'?{Origin:base}:{})}});
const {applicationReady}=await import('../web/static/app.js');await applicationReady;
const liveOverview=await(await originalFetch(base+'/api/overview')).json();
assert.equal(ids.get('metric-revenue').textContent,new Intl.NumberFormat('vi-VN',{minimumFractionDigits:2,maximumFractionDigits:2}).format(liveOverview.summary.revenue));
assert.ok(ids.get('overview-chart').querySelector('svg'));
assert.ok(ids.get('overview-ranking').children.length>0);
assert.equal(ids.get('notice').hidden,true,'Initial API/render flow must not raise an error');
assert.ok(!ids.has('connection-form')&&!ids.has('db-password'),'No credentials should be entered in the web interface');
const beforeRefresh=await(await originalFetch(base+'/api/state')).json();
await ids.get('reload-data').fire('click');
const afterRefresh=await(await originalFetch(base+'/api/state')).json();
assert.ok(afterRefresh.ready&&afterRefresh.source.read_at!==beforeRefresh.source.read_at,'Refresh must read a new MySQL snapshot without a password form');
assert.deepEqual(afterRefresh.filters,beforeRefresh.filters,'Refresh must preserve the applied EDA period');
assert.equal(ids.get('notice').hidden,true,'Automatic saved-config refresh must succeed');
await ids.get('run-forecast').fire('click');
assert.equal(ids.get('forecast-result').hidden,false,'Forecast result must render after the real background job');
assert.ok(ids.get('forecast-table').querySelector('table'));
await ids.get('forecast-horizon').fire('click',ids.get('forecast-horizon').children[1]);
assert.equal(ids.get('forecast-result').hidden,true,'Horizon changes must clear old forecasts');
await ids.get('run-forecast').fire('click');
assert.equal(ids.get('forecast-table').querySelector('tbody').children.length,3);
async function until(predicate){for(let i=0;i<50;i++){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,30));}assert.fail('Client async render timed out');}
for(const index of [1,2]){
  await ids.get('forecast-scope').fire('click',ids.get('forecast-scope').children[index]);
  assert.equal(ids.get('forecast-result').hidden,true,'Changing scope must clear the prior entity result');
  await until(()=>ids.get('forecast-options').children.some(node=>node.tagName==='button'));
  await ids.get('forecast-options').children.find(node=>node.tagName==='button').fire('click');
  await ids.get('run-forecast').fire('click');
  assert.equal(ids.get('forecast-result').hidden,false);
  assert.ok(ids.get('forecast-result-title').textContent.includes('ID '));
  assert.equal(ids.get('forecast-table').querySelector('tbody').children.length,3);
}
ids.get('forecast-search').value='NO MATCH FOR THIS CATALOG';await ids.get('forecast-search').fire('input');
assert.equal(ids.get('forecast-result').hidden,true);assert.equal(ids.get('run-forecast').disabled,true);
await until(()=>ids.get('forecast-options').children.some(node=>node.className==='empty-row'));
await ids.get('forecast-scope').fire('click',ids.get('forecast-scope').children[0]);await ids.get('run-forecast').fire('click');
ids.get('language').value='en';await ids.get('language').fire('change');
assert.equal(ids.get('page-title').textContent,'Revenue overview');
assert.equal(ids.get('forecast-result').hidden,false,'Language changes must preserve forecasts');
assert.ok(ids.get('forecast-origin').textContent.includes('History through'));
location.hash='#evaluation';await windowEvents.get('hashchange')();
assert.equal(ids.get('metrics-table').querySelector('tbody').children.length,3,'Metrics must compare all three methods');
assert.equal(ids.get('evaluation-table').querySelector('tbody').children.length,18);
// Hold an old search response while a newer input arrives (before debounce).
let releaseOptions,optionsStarted=false;
const fetchBeforeRace=globalThis.fetch;
const optionsGate=new Promise(resolve=>releaseOptions=resolve);
globalThis.fetch=async(path,options)=>{const result=await fetchBeforeRace(path,options);if(String(path).includes('/api/catalog')){optionsStarted=true;await optionsGate;}return result;};
const pendingOptions=ids.get('evaluation-scope').fire('click',ids.get('evaluation-scope').children[1]);
await until(()=>optionsStarted);
ids.get('evaluation-search').value='NO MATCH FOR DELAYED SEARCH';await ids.get('evaluation-search').fire('input');
releaseOptions();await pendingOptions;
assert.equal(ids.get('evaluation-entity').children.length,0,'Old options must not reappear during input debounce');
globalThis.fetch=fetchBeforeRace;
await new Promise(resolve=>setTimeout(resolve,220));
location.hash='#explore';await windowEvents.get('hashchange')();
assert.equal(ids.get('explore-table').querySelector('tbody').children.length,15);
await ids.get('explore-table').querySelector('tbody').children[0].fire('click');
assert.equal(ids.get('entity-detail').hidden,false);
assert.ok(ids.get('entity-chart').querySelector('svg'));
let releaseDetail,detailStarted=false;
const detailGate=new Promise(resolve=>releaseDetail=resolve);
globalThis.fetch=async(path,options)=>{const result=await fetchBeforeRace(path,options);if(String(path).includes('/api/entity')){detailStarted=true;await detailGate;}return result;};
const pendingDetail=ids.get('explore-table').querySelector('tbody').children[0].fire('click');
await until(()=>detailStarted);
ids.get('explore-search').value='NO MATCH FOR DELAYED DETAIL';await ids.get('explore-search').fire('input');
assert.equal(ids.get('entity-detail').hidden,true,'Typing must clear the old entity immediately');
releaseDetail();await pendingDetail;
assert.equal(ids.get('entity-detail').hidden,true,'Old entity response must not overwrite a new search');
globalThis.fetch=fetchBeforeRace;
await new Promise(resolve=>setTimeout(resolve,220));
ids.get('filter-start').value='2010-01';await ids.get('filter-start').fire('change');
assert.equal(ids.get('forecast-result').hidden,true);
assert.equal(ids.get('train-model').disabled,true,'Dirty filters must disable use of stale data');
assert.equal(ids.get('notice').hidden,true);
console.log('Client protocol/state checks passed against live MySQL HTTP: bootstrap, overview, all three forecast selectors, search, stale entity/horizon handling, language, evaluation, catalog detail and shared filters. Visual browser QA remains separate.');
