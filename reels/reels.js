/* Shows the AZ reel(s) that belong to this page, newest first. The list comes from reels/reels.json,
   which a scheduled job refreshes from the YouTube channel. A page with no matching reel shows nothing. */
(function () {
  var box = document.querySelector("[data-az-reels]");
  if (!box) return;
  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  var home = here === "index.html" || here === "";
  var css = ".azr{max-width:var(--wrap,1120px);margin:56px auto;padding:0 20px;font-family:inherit}" +
    ".azr h2{font-size:clamp(1.4rem,2.6vw,1.9rem);line-height:1.15;margin:0 0 6px;color:var(--ink,#1b1a17)}" +
    ".azr p{margin:0 0 20px;color:var(--muted,#8a8275)}" +
    ".azr__row{display:flex;gap:18px;flex-wrap:wrap}" +
    ".azr__v{position:relative;width:min(300px,100%);aspect-ratio:9/16;border-radius:16px;overflow:hidden;background:#111;border:1px solid var(--line,rgba(27,26,23,.14));cursor:pointer;padding:0}" +
    ".azr__v img{width:100%;height:100%;object-fit:cover;display:block}" +
    ".azr__v span{position:absolute;left:50%;top:50%;width:68px;height:68px;margin:-34px 0 0 -34px;border-radius:50%;background:var(--accent,#c0492b);box-shadow:0 10px 30px rgba(0,0,0,.35)}" +
    ".azr__v span:after{content:'';position:absolute;left:27px;top:21px;border-style:solid;border-width:13px 0 13px 21px;border-color:transparent transparent transparent #fff}" +
    ".azr__v iframe{width:100%;height:100%;border:0;display:block}" +
    ".azr__v:focus-visible{outline:3px solid var(--accent,#c0492b);outline-offset:3px}";
  fetch("reels/reels.json", { cache: "no-cache" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.reels) return;
    var list = d.reels.filter(function (r) { return home ? true : r.page === here; }).slice(0, home ? 3 : 2);
    if (!list.length) return;
    var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
    var s = document.createElement("section"); s.className = "azr"; s.setAttribute("aria-label", "Watch");
    s.innerHTML = "<h2>" + (home ? "See it in under a minute" : "Watch it in under a minute") + "</h2><p>From our own restaurant.</p><div class='azr__row'></div>";
    var row = s.querySelector(".azr__row");
    list.forEach(function (r) {
      var b = document.createElement("button"); b.type = "button"; b.className = "azr__v"; b.setAttribute("aria-label", "Play: " + r.title);
      var img = document.createElement("img"); img.alt = ""; img.src = "https://i.ytimg.com/vi/" + r.id + "/hqdefault.jpg";  /* 4:3 with the 9:16 short in the middle; cover crops to it */
      b.appendChild(img); b.appendChild(document.createElement("span"));
      b.addEventListener("click", function () {
        b.innerHTML = "<iframe src='https://www.youtube-nocookie.com/embed/" + r.id + "?autoplay=1&rel=0&playsinline=1' title='" + r.title.replace(/'/g, "&#39;") + "' allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen></iframe>";
        b.style.cursor = "default";
      }, { once: true });
      row.appendChild(b);
    });
    box.replaceWith(s);
  }).catch(function () {});
})();
