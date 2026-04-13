import { useMemo, useState } from "react"

import { AnalyzeButton } from "./components/AnalyzeButton"
import { IssueCard } from "./components/IssueCard"
import { PopupHeader } from "./components/PopupHeader"
import { StatusCard } from "./components/StatusCard"
import browser from "./lib/extensionApi"
import { extractTabTextForAnalyze, isPdfLikeTabUrl } from "./lib/extractPageText"
import { tr } from "./lib/uiStrings"
import { theme } from "./styles/theme"
import { RED_CATEGORY_KEYS, CATEGORY_HINTS } from "./lib/categoryMeta"
import type { AnalyzeResponse, RiskIssue } from "../../packages/shared-types"

const DEFAULT_API_URL = "http://localhost:8000"

async function getApiUrl(): Promise<string> {
  try {
    const result = await browser.storage.sync.get({ apiUrl: DEFAULT_API_URL })
    return (result.apiUrl || DEFAULT_API_URL).replace(/\/+$/, "")
  } catch {
    return DEFAULT_API_URL
  }
}


/** Strip LLM/UI wrapping quotes so matching uses the same text as the page. */
function cleanEvidenceForLocate(raw: string): string {
  let s = (raw || "").trim()
  for (;;) {
    let changed = false
    if (
      (s.startsWith('"') && s.endsWith('"')) ||
      (s.startsWith("'") && s.endsWith("'"))
    ) {
      s = s.slice(1, -1).trim()
      changed = true
    } else if (s.startsWith("\u201c") && s.endsWith("\u201d")) {
      s = s.slice(1, -1).trim()
      changed = true
    } else if (s.startsWith("\u2018") && s.endsWith("\u2019")) {
      s = s.slice(1, -1).trim()
      changed = true
    }
    if (!changed) break
  }
  return s.trim()
}

function IndexPopup() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [actionMessage, setActionMessage] = useState("")
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  /** Tab URL at analyze time; used to hide locate on PDF viewer tabs. */
  const [analyzedTabUrl, setAnalyzedTabUrl] = useState<string | undefined>(undefined)

  const signalLabel = useMemo(() => {
    if (!result) return tr("awaitingScan")
    return result.signal === "red"
      ? tr("highRisk")
      : result.signal === "yellow"
        ? tr("caution")
        : tr("secure")
  }, [result])

  const issuesSorted = useMemo(() => {
    if (!result?.issues?.length) return []
    const rank = (s: string) => (s === "red" ? 0 : s === "yellow" ? 1 : 2)
    return [...result.issues].sort((a, b) => {
      const ra = rank(a.severity)
      const rb = rank(b.severity)
      if (ra !== rb) return ra - rb
      return (b.confidence ?? 0) - (a.confidence ?? 0)
    })
  }, [result?.issues])

  const analyzeCurrentPage = async () => {
    setLoading(true)
    setError("")
    setActionMessage("")
    setAnalyzedTabUrl(undefined)
    try {
      const [tab] = await browser.tabs.query({ active: true, currentWindow: true })
      if (!tab?.id) {
        throw new Error(tr("noTab"))
      }

      const extractedText = await extractTabTextForAnalyze(tab.id, tab.url)

      if (!extractedText.trim()) {
        throw new Error(tr("noReadableText"))
      }

      const apiBase = await getApiUrl()
      const response = await fetch(`${apiBase}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: extractedText || "",
          source_url: tab.url || null
        })
      })

      if (!response.ok) {
        throw new Error(tr("apiFailed"))
      }

      const json = (await response.json()) as AnalyzeResponse
      setAnalyzedTabUrl(tab.url)
      setResult(json)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed"
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const showIssueOnPage = async (issue: RiskIssue) => {
    setActionMessage("")
    try {
      const [tab] = await browser.tabs.query({ active: true, currentWindow: true })
      if (!tab?.id) return
      if (isPdfLikeTabUrl(tab.url ?? analyzedTabUrl)) {
        return
      }

      const cleanedQuote = cleanEvidenceForLocate(issue.evidence_quote)

      const redCatArray = Array.from(RED_CATEGORY_KEYS)
      const hintsObj = CATEGORY_HINTS
      const locateScript = {
        target: { tabId: tab.id, allFrames: true },
        args: [cleanedQuote, issue.label, issue.category, redCatArray, hintsObj],
        func: (evidenceQuote: string, label: string, category: string, redCats: string[], catHints: Record<string, string[]>) => {
          const HIGHLIGHT_ATTR = "data-fairterms-highlight";
          document.querySelectorAll(`mark[${HIGHLIGHT_ATTR}]`).forEach((el) => {
            const p = el.parentNode; if (!p) return;
            p.replaceChild(document.createTextNode(el.textContent || ""), el); p.normalize();
          });
          const strip = (s: string) => { let t = (s||"").trim(); for(;;){let ch=false;if(t.length>=2){if((t[0]==='"'&&t.at(-1)==='"')||(t[0]==="'"&&t.at(-1)==="'")){t=t.slice(1,-1).trim();ch=true}else if(t[0]==="\u201c"&&t.at(-1)==="\u201d"){t=t.slice(1,-1).trim();ch=true}else if(t[0]==="\u2018"&&t.at(-1)==="\u2019"){t=t.slice(1,-1).trim();ch=true}}if(!ch)break}return t};
          const cc = (c:string) => {if("\u201c\u201d\u201e\u201f".includes(c))return'"';if("\u2018\u2019\u201a\u201b".includes(c))return"'";if(c==="\u2013"||c==="\u2014")return"-";return c};
          const nm = (raw:string) => {let out="";const map:number[]=[];let ps=true;for(let i=0;i<raw.length;i++){const c=cc(raw[i]).toLowerCase();const sp=/\s/.test(c);if(sp){if(!ps){out+=" ";map.push(i);ps=true}}else{out+=c;map.push(i);ps=false}}while(out.endsWith(" ")){out=out.slice(0,-1);map.pop()}return{text:out,map}};
          const core=strip(evidenceQuote);if(!core)return false;
          const redSet=new Set(redCats);
          const hc=label.toLowerCase().includes("safe")||category==="safe"?"#22C55E":redSet.has(category)?"#EF4444":"#F59E0B";
          const isDec=(s:string,i:number)=>{if(i<0||i>=s.length||s[i]!==".")return false;return/\d/.test(s[i-1]||"")&&/\d/.test(s[i+1]||"")};
          const fcp=(s:string)=>{for(let i=0;i<s.length;i++){if(s[i]!==".")continue;if(isDec(s,i))continue;const sl=s.slice(0,i).trim();if(sl.length>=18)return sl}return""};
          const eof=(t:string,s:number,e:number)=>{const ls=t.lastIndexOf("\n",Math.max(0,s-1))+1;let le=t.indexOf("\n",e);if(le===-1)le=t.length;return{start:ls,end:le}};
          const erl=(range:Range)=>{const{startContainer:sc,endContainer:ec,startOffset:so,endOffset:eo}=range;if(sc!==ec||sc.nodeType!==Node.TEXT_NODE)return range.cloneRange();const t=sc.textContent||"";let{start:ls,end:le}=eof(t,so,eo);if(le<=ls)le=Math.min(t.length,ls+1);const r=document.createRange();r.setStart(sc,Math.max(0,Math.min(ls,t.length)));r.setEnd(sc,Math.max(0,Math.min(le,t.length)));return r};
          const wm=(range:Range)=>{const m=document.createElement("mark");m.setAttribute(HIGHLIGHT_ATTR,label);m.style.backgroundColor=`${hc}33`;m.style.outline=`2px solid ${hc}`;m.style.borderRadius="4px";m.style.padding="0 2px";m.style.boxShadow=`0 0 12px ${hc}44`;m.style.transition="all 0.3s ease";try{range.surroundContents(m)}catch{const f=range.extractContents();m.appendChild(f);range.insertNode(m)}m.scrollIntoView({behavior:"smooth",block:"center"});return true};
          const cp=fcp(core);const probes=[core,core.slice(0,260),core.slice(0,180),core.slice(0,120),cp,core.split(";")[0]||""].map(x=>x.trim()).filter(x=>x.length>=18);
          const sel=window.getSelection();
          for(const p of probes){sel?.removeAllRanges();const f=(window as any).find(p,false,false,true,false,false,false);if(!f)continue;const s=window.getSelection();if(!s||s.rangeCount===0)continue;const r=erl(s.getRangeAt(0).cloneRange());s.removeAllRanges();return wm(r)}
          const vis=(n:Text)=>{const p=n.parentElement;if(!p)return false;const tag=p.tagName;if(tag==="SCRIPT"||tag==="STYLE"||tag==="NOSCRIPT"||tag==="TEXTAREA"||tag==="OPTION")return false;const st=window.getComputedStyle(p);return st.display!=="none"&&st.visibility!=="hidden"};
          type NR={node:Text;start:number;end:number};const nodes:NR[]=[];let flat="";const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);while(w.nextNode()){const n=w.currentNode as Text;if(!n.textContent||!n.textContent.trim())continue;if(!vis(n))continue;const s=flat.length;flat+=n.textContent;nodes.push({node:n,start:s,end:flat.length});flat+="\n"}
          if(!flat||!nodes.length)return false;const dn=nm(flat);const qn=nm(core).text;if(!qn)return false;
          const tw=qn.split(" ").filter(w=>w.length>2);const qp=[qn,qn.slice(0,260),qn.slice(0,180),qn.slice(0,120),qn.slice(0,80)].filter(p=>p.length>=22);
          let bns=-1,bnl=-1,bs=-1;
          for(const p of qp){const i=dn.text.indexOf(p);if(i!==-1&&p.length>bs){bns=i;bnl=p.length;bs=p.length+50;break}}
          if(bns===-1&&tw.length>0){const aw=tw.slice(0,12);const f=aw[0];const el=Math.max(90,Math.min(340,qn.length+60));let i=dn.text.indexOf(f);while(i!==-1){let sc=0,cu=i;for(const w of aw){const nx=dn.text.indexOf(w,cu);if(nx!==-1&&nx-i<=520){sc+=w.length;cu=nx+w.length}}const hints=(catHints[category]||[]).map(h=>nm(h).text);for(const h of hints){if(h&&dn.text.indexOf(h,i)!==-1&&dn.text.indexOf(h,i)-i<=520)sc+=8}if(sc>bs){bs=sc;bns=i;bnl=el}i=dn.text.indexOf(f,i+1)}}
          if(bns===-1||bs<20)return false;
          const ne=Math.min(dn.text.length,bns+bnl);const rs=dn.map[Math.max(0,bns)]??0;const re=(dn.map[Math.max(0,ne-1)]??rs)+1;if(re<=rs)return false;
          let ch:NR|null=null,cls=0,cle=0,ob=0;for(const r of nodes){const os=Math.max(rs,r.start);const oe=Math.min(re,r.end);const o=oe-os;if(o>ob){ob=o;ch=r;cls=os-r.start;cle=oe-r.start}}
          if(!ch||ob<=0)return false;const nt=ch.node.textContent||"";if(!nt)return false;
          let st=Math.max(0,Math.min(cls,nt.length-1)),en=Math.max(st+1,Math.min(cle,nt.length));const ln=eof(nt,st,en);st=ln.start;en=ln.end;if(en<=st)en=Math.min(nt.length,st+1);
          const rng=document.createRange();rng.setStart(ch.node,st);rng.setEnd(ch.node,en);return wm(rng);
        }
      }

      const tryLocate = async () => {
        const results = await browser.scripting.executeScript(locateScript)
        return results.some((res) => Boolean(res.result))
      }

      const waitForTabReload = async (tabId: number) =>
        await new Promise<void>((resolve) => {
          let done = false
          const onUpdated = (updatedTabId: number, info: { status?: string }) => {
            if (updatedTabId === tabId && info.status === "complete") {
              browser.tabs.onUpdated.removeListener(onUpdated)
              done = true
              resolve()
            }
          }
          browser.tabs.onUpdated.addListener(onUpdated)
          setTimeout(() => {
            if (!done) {
              browser.tabs.onUpdated.removeListener(onUpdated)
              resolve()
            }
          }, 6000)
        })

      let didHighlight = false
      try {
        didHighlight = await tryLocate()
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        const isContextInvalidated =
          msg.toLowerCase().includes("extension context invalidated") ||
          msg.toLowerCase().includes("context invalidated")

        if (!isContextInvalidated) throw err

        setActionMessage(tr("recoverContext"))
        await browser.tabs.reload(tab.id)
        await waitForTabReload(tab.id)
        didHighlight = await tryLocate()
      }

      if (didHighlight) {
        setActionMessage(`${tr("locatedPrefix")} ${issue.label}`)
      } else {
        setActionMessage(tr("locateFailed"))
      }
    } catch (err) {
      // silent fail for highlight
      setActionMessage(tr("locateFailed"))
    }
  }

  return (
    <div
      style={{
        padding: "20px 16px",
        width: 340,
        minHeight: 400,
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        background: theme.background,
        color: theme.textPrimary,
        display: "flex",
        flexDirection: "column",
        position: "relative",
        overflow: "hidden"
      }}>
      {/* Background Glow */}
      <div style={{
        position: "absolute",
        top: -100,
        right: -100,
        width: 200,
        height: 200,
        background: `${theme.primary}22`,
        filter: "blur(60px)",
        borderRadius: "50%",
        zIndex: 0
      }} />

      <div style={{ zIndex: 1 }}>
        <PopupHeader />
        <AnalyzeButton loading={loading} onClick={analyzeCurrentPage} />
        <StatusCard signal={result?.signal} label={signalLabel} />

        {error ? (
          <div style={{ 
            marginTop: 16, 
            padding: 12, 
            borderRadius: 8, 
            background: `${theme.danger}11`, 
            border: `1px solid ${theme.danger}33`,
            color: theme.danger,
            fontSize: 12,
            textAlign: "center"
          }}>
            {error}
          </div>
        ) : null}

        {actionMessage ? (
          <div style={{ 
            marginTop: 12, 
            textAlign: "center",
            color: theme.secondary,
            fontSize: 11,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em"
          }}>
            {actionMessage}
          </div>
        ) : null}

        <div style={{ marginTop: 20, display: "grid", gap: 12 }}>
          {issuesSorted.map((issue, idx) => (
            <IssueCard
              key={`${issue.category}-${idx}`}
              issue={issue}
              onShowOnPage={showIssueOnPage}
              showLocateButton={!isPdfLikeTabUrl(analyzedTabUrl)}
            />
          ))}
          
          {result && result.issues.length === 0 && !loading && (
            <div style={{ 
              textAlign: "center", 
              padding: "40px 20px",
              color: theme.textMuted
            }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>🛡️</div>
              <div style={{ color: theme.success, fontWeight: 700, marginBottom: 4 }}>{tr("noRisksTitle")}</div>
              <div style={{ fontSize: 12 }}>{tr("noRisksBody")}</div>
            </div>
          )}
        </div>
      </div>
      
      <div style={{ 
        marginTop: "auto", 
        paddingTop: 24, 
        textAlign: "center", 
        fontSize: 10, 
        color: theme.textMuted,
        opacity: 0.6
      }}>
        {result?.disclaimer || tr("footerFallback")}
      </div>
    </div>
  )
}

export default IndexPopup
