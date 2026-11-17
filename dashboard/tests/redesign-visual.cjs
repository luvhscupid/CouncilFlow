async page => {
  const checks=[], errors=[], measurements=[];
  const check=(ok,label)=>{if(!ok)throw new Error(label);checks.push(label);};
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>route.continue());
  await page.goto('http://127.0.0.1:4173/');
  await page.emulateMedia({reducedMotion:'reduce'});
  for(const theme of ['dark','light']) {
    if(theme==='light')await page.locator('#theme').click();
    const contrast=await page.evaluate(()=>{
      const css=getComputedStyle(document.documentElement),token=k=>css.getPropertyValue(k).trim();
      const luminance=hex=>{const rgb=hex.replace('#','').match(/../g).map(n=>parseInt(n,16)/255).map(n=>n<=.04045?n/12.92:((n+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;};
      const ratio=(a,b)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
      const backgrounds=['--bg','--surface','--raised'].map(token);
      const values=Object.fromEntries(['--ink','--muted','--accent','--cyan','--violet','--green','--amber','--red'].map(k=>[k,Math.min(...backgrounds.map(bg=>ratio(token(k),bg)))]));
      const light=document.documentElement.dataset.theme==='light';
      values.primary=Math.min(...(light?['#215fa8','#176d87']:['#80b6ff','#83d7ee']).map(bg=>ratio(light?'#ffffff':'#0b213d',bg)));
      values.focus=ratio(token('--cyan'),token('--bg'));
      return values;
    });
    for(const [name,ratio] of Object.entries(contrast))check(ratio>=4.5,`${theme}: ${name} contrast >=4.5:1 (${ratio.toFixed(2)}:1)`);
    for(const width of [320,375,768,1024,1440,1920,2048]) {
      await page.setViewportSize({width,height:1000});
      check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${theme}: no document overflow at ${width}px`);
      const main=await page.locator('main').boundingBox();
      if(width>=1440)check(width-main.x-main.width<1,`${theme}: main uses available width at ${width}px`);
      const heading=await page.locator('#title').evaluate(e=>parseFloat(getComputedStyle(e).fontSize));
      check(heading>=28,`${theme}: main heading >=28px at ${width}px`);
      const smallControls=await page.locator('button:not([hidden]), select:not(:disabled)').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().height>0&&e.getBoundingClientRect().height<44).map(e=>e.id));
      check(smallControls.length===0,`${theme}: controls >=44px high at ${width}px`);
      measurements.push({theme,width,mainWidth:main.width,rightGap:width-main.x-main.width,heading});
      await page.evaluate(()=>scrollTo(0,0));
      if([375,768,1440,2048].includes(width))await page.screenshot({path:`dashboard/evidence/redesign/${theme}-${width}.png`,fullPage:true});
    }
    await page.setViewportSize({width:1440,height:1000});
    for(const scenario of ['empty','failed']) {
      await page.locator('#scenario').selectOption(scenario);
      await page.screenshot({path:`dashboard/evidence/redesign/${theme}-${scenario}.png`,fullPage:true});
      check(await page.locator('#source-banner').textContent().then(t=>t.includes('DEMO DATA')),`${theme}: ${scenario} retains demo provenance`);
    }
    await page.locator('#scenario').selectOption('review');
  }
  await page.locator('#theme').click();
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('.criterion-row').first().click();
  await page.screenshot({path:'dashboard/evidence/redesign/evidence-drawer.png'});
  check(await page.locator('#inspector').evaluate(e=>e.contains(document.activeElement)),'Evidence drawer contains keyboard focus');
  await page.keyboard.press('Escape');
  check(await page.locator('.criterion-row').first().evaluate(e=>e===document.activeElement),'Evidence drawer restores focus');
  await page.setViewportSize({width:375,height:900});
  check(await page.locator('.recorded-active').evaluate(e=>e.getBoundingClientRect().top===Math.min(...[...document.querySelectorAll('.role-card')].map(x=>x.getBoundingClientRect().top))),'Mobile prioritizes recorded active role');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.locator('#attempt').selectOption('attempt-1');
  check(await page.locator('#segments').evaluate(e=>e.getAnimations().length>0),'Acceptance animation is triggered by a candidate change');
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('#attempt').selectOption('attempt-2');
  check(await page.locator('#segments').evaluate(e=>e.getAnimations().every(a=>a.playState!=='running')),'Reduced motion suppresses acceptance animation');
  await page.locator('#role-filter').selectOption('Tester');
  await page.locator('#type-filter').selectOption('handoff');
  check(await page.locator('#events .empty').count()===1,'Filtered console empty state is informative');
  await page.locator('#file').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from('{')});
  await page.locator('#import-status').filter({hasText:'Malformed JSON'}).waitFor();
  check(await page.locator('#import-status').getAttribute('class')==='import-error','Import errors retain visible recovery feedback');
  await page.evaluate(()=>scrollTo(0,0));
  await page.screenshot({path:'dashboard/evidence/redesign/import-error.png'});
  check(errors.length===0,'No browser runtime errors');
  return {passed:checks.length,checks,measurements,errors};
}
