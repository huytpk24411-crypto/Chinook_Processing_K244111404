import {t,number,month,locale} from './i18n.js';
const ns='http://www.w3.org/2000/svg';
function node(tag,attributes={},text=null) {const el=document.createElementNS(ns,tag);Object.entries(attributes).forEach(([k,v])=>el.setAttribute(k,v));if(text!==null)el.textContent=text;return el;}
function niceMax(value){const power=10**Math.floor(Math.log10(value||1));return Math.ceil(value/power/0.5)*power*0.5;}
export function drawChart(container,{history=[],predicted=[],boundary=null}={}) {
  container.replaceChildren();
  if(!history.length&&!predicted.length){const e=document.createElement('div');e.className='chart-empty';e.textContent=t('no_data');container.append(e);return;}
  const dates=[...new Set([...history.map(x=>x.month),...predicted.map(x=>x.month)])].sort();
  const width=Math.max(280,Math.min(1100,container.clientWidth||960)),height=width<550?245:285,left=52,right=20,top=20,bottom=43,plotW=width-left-right,plotH=height-top-bottom;
  const values=[...history,...predicted].map(x=>Number(x.value));const max=niceMax(Math.max(...values,1)*1.12);
  const x=date=>left+(dates.length<2?plotW/2:dates.indexOf(date)/(dates.length-1)*plotW);
  const y=value=>top+plotH-(Number(value)/max)*plotH;
  const svg=node('svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':`${t('revenue_timeline')} · ${t('currency')}`,xmlns:ns,'font-family':'Segoe UI, system-ui, sans-serif'});
  svg.append(node('title',{},t('revenue_timeline')));
  for(let i=0;i<=4;i++){const value=max*i/4;const yy=y(value);svg.append(node('line',{x1:left,x2:width-right,y1:yy,y2:yy,stroke:'#e9edf3','stroke-width':1}));svg.append(node('text',{x:left-13,y:yy+4,'text-anchor':'end',fill:'#7b8797','font-size':11},number(value,max<=2?1:0)));}
  if(boundary&&dates.includes(boundary)){const bx=x(boundary);svg.append(node('rect',{x:bx,y:top,width:Math.max(0,width-right-bx),height:plotH,fill:'#edf3fa'}));svg.append(node('line',{x1:bx,x2:bx,y1:top,y2:top+plotH,stroke:'#9bb2c8','stroke-width':1,'stroke-dasharray':'4 5'}));}
  const path=points=>points.map((p,i)=>`${i?'L':'M'}${x(p.month).toFixed(2)},${y(p.value).toFixed(2)}`).join(' ');
  if(history.length){const line=path(history);svg.append(node('path',{d:`${line} L${x(history.at(-1).month)},${top+plotH} L${x(history[0].month)},${top+plotH} Z`,fill:'#edf2f9','fill-opacity':'.65'}));svg.append(node('path',{d:line,fill:'none',stroke:'#426594','stroke-width':2.25,'stroke-linejoin':'round'}));}
  if(predicted.length){const connection=history.filter(p=>p.month<predicted[0].month).at(-1);const points=connection?[connection,...predicted]:predicted;svg.append(node('path',{d:path(points),fill:'none',stroke:'#b77932','stroke-width':2.3,'stroke-dasharray':'5 4'}));predicted.forEach(p=>svg.append(node('circle',{cx:x(p.month),cy:y(p.value),r:3.5,fill:'#b77932',stroke:'#fff','stroke-width':1.5})));}
  const tickCount=Math.min(width<550?3:7,dates.length);for(let i=0;i<tickCount;i++){const index=tickCount===1?0:Math.round(i*(dates.length-1)/(tickCount-1));const date=dates[index];svg.append(node('text',{x:x(date),y:height-15,'text-anchor':i===0?'start':i===tickCount-1?'end':'middle',fill:'#738095','font-size':11},month(date)));}
  const cursor=node('line',{x1:0,x2:0,y1:top,y2:top+plotH,stroke:'#a1afc3','stroke-width':1,'stroke-dasharray':'3 4',visibility:'hidden'});svg.append(cursor);
  const tooltip=document.createElement('div');tooltip.className='chart-tooltip';tooltip.hidden=true;
  const hit=node('rect',{x:left,y:top,width:plotW,height:plotH,fill:'transparent'});svg.append(hit);
  hit.addEventListener('pointermove',event=>{const rect=svg.getBoundingClientRect();const px=(event.clientX-rect.left)*width/rect.width;const index=Math.max(0,Math.min(dates.length-1,Math.round((px-left)/plotW*(dates.length-1))));const date=dates[index];cursor.setAttribute('x1',x(date));cursor.setAttribute('x2',x(date));cursor.setAttribute('visibility','visible');tooltip.replaceChildren();const title=document.createElement('small');title.textContent=month(date);tooltip.append(title);for(const [label,points]of[[t('actual'),history],[t('predicted'),predicted]]){const p=points.find(p=>p.month===date);if(p){const row=document.createElement('div');row.textContent=`${label}: ${number(p.value)}`;tooltip.append(row);}}tooltip.hidden=false;});
  hit.addEventListener('pointerleave',()=>{cursor.setAttribute('visibility','hidden');tooltip.hidden=true;});
  container.append(svg,tooltip);
}
export async function exportPng(container){
  const source=container.querySelector('svg');if(!source)throw new Error('no_data');
  const svg=source.cloneNode(true);const [, ,width,height]=source.getAttribute('viewBox').split(' ').map(Number);svg.setAttribute('width',width);svg.setAttribute('height',height);const blob=new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml;charset=utf-8'});const url=URL.createObjectURL(blob);
  try{const image=new Image();image.src=url;await image.decode();const canvas=document.createElement('canvas');canvas.width=Math.round(width*2);canvas.height=Math.round(height*2);const context=canvas.getContext('2d');context.fillStyle='#fff';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0,canvas.width,canvas.height);const png=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(!png)throw new Error('png_failed');const link=document.createElement('a');link.href=URL.createObjectURL(png);link.download='chinook-chart.png';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);}finally{URL.revokeObjectURL(url);}
}
