const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const sandbox={localStorage:{getItem:()=>null},navigator:{language:'en'},document:{documentElement:{},querySelectorAll:()=>[],getElementById:()=>({addEventListener(){}})}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('static/i18n.js','utf8'),sandbox);
const result=vm.runInContext('({catalogs,supported,t})',sandbox),keys=Object.keys(result.catalogs.es);
for(const [locale,catalog] of Object.entries(result.catalogs)){
 assert.deepEqual(Object.keys(catalog).sort(),[...keys].sort(),locale);
 for(const key of keys){assert(catalog[key].trim());assert.deepEqual(catalog[key].match(/\{\w+\}/g)||[],key.match(/\{\w+\}/g)||[],locale+': '+key);}
}
for(const [input,expected] of Object.entries({'de-AT':'de','es-MX':'es','ja-JP':'ja','zh-Hans-SG':'zh-CN','zh-Hant':'zh-TW','zh-HK':'zh-TW','zh-MO':'zh-TW','fr-FR':'en'}))assert.equal(result.supported(input),expected);
assert.equal(result.t('Unknown diagnostic'), 'Unknown diagnostic');
console.log('PASS: all five translated catalogs, placeholder parity, regional fallback and English diagnostics');
