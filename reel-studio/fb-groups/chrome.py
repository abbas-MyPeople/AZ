"""Drive the owner's own Chrome (already signed in to Facebook) through AppleScript, so the group job never
has a separate login that Facebook can sign out. Needs Chrome's View > Developer > Allow JavaScript from
Apple Events (owner turned it on 2026-10-29). Each run uses its own minimized window and closes it."""
import base64, json, os, subprocess, time

def _osa(script, timeout=120):
    r = subprocess.run(["osascript", "-"], input=script.encode(), capture_output=True, timeout=timeout)
    if r.returncode: raise RuntimeError("osascript: " + r.stderr.decode()[-300:])
    return r.stdout.decode().strip()

def _q(s): return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

class Window:
    def __init__(self):
        show = os.environ.get("AZ_FB_SHOW") == "1"
        self.id = _osa('tell application "Google Chrome"\nset w to make new window\n' + ("" if show else "set minimized of w to true\n") + 'return id of w\nend tell')
    def go(self, url, wait=8):
        _osa(f'tell application "Google Chrome" to set URL of active tab of (window id {self.id}) to {_q(url)}'); time.sleep(wait)
    def js(self, code, timeout=120):
        """Run code (an expression or a function body ending in a value) and return its JSON result."""
        wrapped = "(function(){try{return JSON.stringify((function(){" + code + "})())}catch(e){return JSON.stringify({__err:String(e)})}})()"
        out = _osa(f'tell application "Google Chrome" to execute active tab of (window id {self.id}) javascript {_q(wrapped)}', timeout)
        v = json.loads(out) if out and out != "missing value" else None
        if isinstance(v, dict) and "__err" in v: raise RuntimeError("page script: " + v["__err"][:200])
        return v
    def url(self): return self.js("return location.href")
    def push_file(self, path, chunk=600_000):
        """Hand a local file to the page as window.__azFile (Facebook's page cannot fetch our files itself)."""
        data = base64.b64encode(open(path, "rb").read()).decode()
        self.js("window.__azParts=[];return 1")
        for i in range(0, len(data), chunk):
            self.js(f"window.__azParts.push({json.dumps(data[i:i+chunk])});return window.__azParts.length")
        name = os.path.basename(path)
        return self.js("const b=atob(window.__azParts.join(''));const u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);"
                       f"window.__azFile=new File([u],{json.dumps(name)},{{type:'video/mp4'}});window.__azParts=null;return window.__azFile.size")
    def close(self):
        try: _osa(f'tell application "Google Chrome" to close (window id {self.id})')
        except Exception: pass
