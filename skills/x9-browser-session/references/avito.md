# Avito traffic discipline

Treat one account, browser profile, and public IP as one browsing lane for the whole
parent task. Avito work is sequential even when the rest of the research is delegated:

- appoint one Avito operator; subagents may analyze captured data but must not browse
  `avito.ru` concurrently;
- keep only one Avito navigation, search, or listing load in flight. Prefer one task
  tab; extra tabs may hold queued pages, but interact with only one at a time;
- let the current page finish loading and inspect it before requesting the next page;
  shortlist from search results and reuse captured data instead of repeatedly reopening
  or refreshing listings;
- do not bulk-load listings, paginate rapidly, poll availability, or repeat searches
  and listing loads to work around throttling;
- when Avito shows a security warning, a `Продолжить`/`Continue` button leading to
  CAPTCHA, or the CAPTCHA itself, keep the same page, controller, and profile. Wait
  five seconds without another request and inspect it. If the challenge remains,
  refresh that page at most twice, waiting five seconds and inspecting after each
  refresh. Do not click that button, attempt to solve the CAPTCHA, or hand it off.
  Continue serial browsing as soon as the requested content is visible;
- use the same bounded refreshes for a transient Avito error or site timeout page only
  when the page can be safely reloaded. If the challenge or error remains after them,
  or Avito returns `429` or access-denied, stop Avito requests across the parent task,
  preserve collected results, and return `DEGRADED`. Do not switch controllers,
  profiles, agents, or IP addresses to continue;
- resume only when the user requests another check or ordinary access is already
  visibly restored. Perform that check serially through the same browser profile.
