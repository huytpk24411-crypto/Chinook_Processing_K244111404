// Node unit checks for interface copy, selectors and chart geometry. No browser is controlled.
import assert from 'node:assert/strict';
import fs from 'node:fs';
globalThis.localStorage={data:new Map(),getItem(key){return this.data.get(key)??null;},setItem(key,value){this.data.set(key,value);}};
class Node {
  constructor(tag){this.tagName=tag;this.attributes={};this.children=[];this.events={};this.textContent='';}
  setAttribute(key,value){this.attributes[key]=String(value);}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  addEventListener(key,callback){this.events[key]=callback;}
}
globalThis.document={documentElement:{lang:'vi'},createElement:tag=>new Node(tag),createElementNS:(ns,tag)=>new Node(tag)};
const {COPY,t,number,month,setLanguage}=await import('../web/static/i18n.js');
const {drawChart}=await import('../web/static/charts.js');
const html=fs.readFileSync(new URL('../web/static/index.html',import.meta.url),'utf8');
const js=fs.readFileSync(new URL('../web/static/app.js',import.meta.url),'utf8');
const css=fs.readFileSync(new URL('../web/static/styles.css',import.meta.url),'utf8');
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(match=>match[1]);
assert.equal(ids.length,new Set(ids).size,'HTML IDs must be unique');
for(const match of html.matchAll(/data-(?:i18n|placeholder)="([^"]+)"/g))assert.ok(COPY[match[1]],`Missing translation ${match[1]}`);
for(const match of js.matchAll(/\$\('([^']+)'\)/g))assert.ok(ids.includes(match[1]),`Missing HTML target ${match[1]}`);
for(const pair of Object.values(COPY))assert.ok(pair.length===2&&pair.every(value=>typeof value==='string'&&value.length));
assert.ok(css.includes('@media(max-width:700px)'),'Mobile layout breakpoint required');
assert.ok(!html.includes('https://'),'Interface must not depend on external CDNs');
assert.ok(!html.includes('view-settings')&&!html.includes('connection-form')&&!html.includes('type="password"'),'Web must not expose connection settings or a password form');
assert.ok(!html.includes('MIDTERM')&&!html.includes('REVENUE WORKSPACE'),'EDA layout must omit decorative project banners');
assert.ok(js.includes("perform('refresh',{}"),'Refresh must use saved configuration, without a credential form');
const vi=number(1234.5);setLanguage('en');assert.notEqual(number(1234.5),vi);assert.equal(t('overview'),'Overview');assert.equal(month('2013-06'),'Jun 2013');
const container=new Node('div');
drawChart(container,{history:[{month:'2013-01',value:0},{month:'2013-02',value:20}],predicted:[{month:'2013-03',value:12}],boundary:'2013-03'});
const svg=container.children[0];assert.equal(svg.tagName,'svg');assert.ok(svg.children.some(node=>node.tagName==='circle'));assert.ok(svg.children.some(node=>node.tagName==='rect'&&node.attributes.fill==='#edf3fa'));
for(const node of svg.children){for(const value of Object.values(node.attributes))assert.ok(!value.includes('NaN')&&!value.includes('Infinity'),'Chart geometry must remain finite');}
const paths=svg.children.filter(node=>node.tagName==='path');assert.equal(paths.length,3,'History area, history line and recursive forecast line');
drawChart(container,{history:[{month:'2013-01',value:0}]});assert.ok(container.children.length>0,'Single zero month must render');
drawChart(container,{});assert.equal(container.children[0].textContent,t('no_data'));
console.log('Frontend unit checks passed: translation coverage, unique IDs, JS targets, local assets, responsive breakpoint, locale formatting and chart geometry.');
