// Serves the AZ site the way GitHub Pages did, so every indexed address keeps answering unchanged:
//   /x.html -> x.html (no rewrite to /x, which would move every page Google already knows)
//   /x      -> x.html, else x/index.html via a 301 to /x/
//   /dir/   -> dir/index.html
// Assets are served with html_handling = "none", so only this file decides how a path resolves.
export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }
    const url = new URL(request.url);
    const path = url.pathname;
    const get = (p) => env.ASSETS.fetch(new Request(new URL(p + url.search, url), request));

    let res = await get(path);
    if (res.status !== 404) return res;

    if (path.endsWith("/")) {
      res = await get(path + "index.html");
      if (res.status !== 404) return res;
    } else {
      res = await get(path + ".html");
      if (res.status !== 404) return res;
      res = await get(path + "/index.html");
      if (res.status !== 404) {
        return Response.redirect(new URL(path + "/" + url.search, url).toString(), 301);
      }
    }
    const notFound = await get("/404.html");
    if (notFound.status === 200) {
      return new Response(notFound.body, { status: 404, headers: notFound.headers });
    }
    return new Response("Not found", { status: 404, headers: { "content-type": "text/plain; charset=utf-8" } });
  },
};
