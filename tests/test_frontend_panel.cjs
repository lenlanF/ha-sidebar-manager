/* Isolated native custom-element regression tests. No DOM/browser runtime. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("custom_components/panel_iframe/www/panel_iframe.js","utf8");
let navigations = 0;
const events = [];
const registered = new Map();
const location = {protocol:"https:",hostname:"ha.local",pathname:"/menu",search:"",hash:""};
const history = {replaceState(_a,_b,uri){navigations++;location.pathname=uri;}};
class Element {
  constructor(){
    this.isConnected = true;
    this.shadowRoot = null;
  }
  attachShadow(){
    this.shadowRoot={innerHTML:"",addEventListener(){}};
    return this.shadowRoot;
  }
  dispatchEvent(event){events.push(event.type);return true;}
}
class Event {
  constructor(type, opts){this.type=type;this.detail=opts.detail;}
}
const context={
  HTMLElement:Element,
  CustomEvent:Event,
  customElements:{get(name){return registered.get(name)},define(name,ctor){registered.set(name,ctor)}},
  location,
  history,
  queueMicrotask(callback){callback();},
  URL,
};
vm.runInNewContext(source,context);
const Panel=registered.get("ha-panel_iframe");
assert.ok(Panel,"native custom element is registered without waiting for Lovelace");

const item=new Panel();
item.panel={title:"自动化",config:{mode:"3",url:"/config/automation/dashboard"}};
assert.equal(navigations,1,"internal HA route navigates exactly once");
assert.ok(events.includes("location-changed"));
item.connectedCallback();
assert.equal(navigations,1,"rerenders cannot retrigger navigation");
item.panel={title:"自动化",config:{mode:"3",url:"https://evil.example/"}};
assert.equal(navigations,1,"external URL forbidden for internal mode");

const iframe=new Panel();
iframe.panel={title:"控制台",config:{mode:"0",url:"https://nas.example/"}};
assert.ok(iframe.shadowRoot.innerHTML.includes("<iframe"));
assert.ok(iframe.shadowRoot.innerHTML.includes("https://nas.example/"));
assert.ok(iframe.shadowRoot.innerHTML.includes('class="open-link"'), "embedded toolbar offers a fallback for blocked CSP");
assert.ok(iframe.shadowRoot.innerHTML.includes('rel="noopener noreferrer"'), "fallback must not grant opener access");
const full=new Panel();
full.panel={title:"全屏仪表盘",config:{mode:"1",url:"https://nas.example/"} };
assert.ok(full.shadowRoot.innerHTML.includes('class="floating-actions"'), "full-screen mode exposes a fallback");
assert.ok(full.shadowRoot.innerHTML.includes('target="_blank"'));


const popup=new Panel();
popup.panel={title:"网站",config:{mode:"2",url:"https://example.org/"}};
assert.ok(popup.shadowRoot.innerHTML.includes('target="_blank"'));
assert.ok(!popup.shadowRoot.innerHTML.includes("<iframe"));

const mixed=new Panel();
mixed.panel={title:"HTTP legacy service",config:{mode:"0",url:"http://nas.local:8080/"}};
assert.ok(mixed.shadowRoot.innerHTML.includes('target="_blank"'), "HTTPS parent must provide a mixed-content fallback");
assert.ok(!mixed.shadowRoot.innerHTML.includes("<iframe"), "HTTPS parent must never force an HTTP iframe");

const ingress=new Panel();
ingress.panel={title:"HAOS test path",config:{mode:"0",url:"/api/hassio_ingress/test-only/"}};
assert.ok(ingress.shadowRoot.innerHTML.includes('src="/api/hassio_ingress/test-only/"'));
assert.ok(ingress.shadowRoot.innerHTML.includes('class="open-link"'), "ingress-like paths retain a manual fallback");
assert.ok(!ingress.shadowRoot.innerHTML.includes("Authorization:"), "frontend does not fabricate ingress auth");

const invalid=new Panel();
invalid.panel={title:"不合法",config:{mode:"0",url:"javascript:alert(1)"}};
assert.ok(invalid.shadowRoot.innerHTML.includes("URL 无效"));
assert.ok(!invalid.shadowRoot.innerHTML.includes("<iframe"));
console.log("Native panel and internal navigation behavior: OK");
