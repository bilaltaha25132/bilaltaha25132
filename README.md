<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
  <img src="./assets/hero-light.svg" width="100%" alt="Bilal Taha, Full Stack AI Engineer in Karachi. I build LLM products end to end: RAG pipelines and LangGraph agents, the APIs around them, and the interfaces people actually use. Now building the AI concierge for Abu Dhabi tourism.">
</picture>

<p>
  <a href="https://mbilaltaha.com"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-site-dark.svg"><img src="./assets/btn-site-light.svg" height="40" alt="Website: mbilaltaha.com"></picture></a>
  <a href="https://linkedin.com/in/bilal-taha25132"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-linkedin-dark.svg"><img src="./assets/btn-linkedin-light.svg" height="40" alt="LinkedIn"></picture></a>
  <a href="mailto:m.bilal.25132@gmail.com"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-email-dark.svg"><img src="./assets/btn-email-light.svg" height="40" alt="Email m.bilal.25132@gmail.com"></picture></a>
  <a href="https://mbilaltaha.com/Bilal_Taha_Resume.pdf"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/btn-resume-dark.svg"><img src="./assets/btn-resume-light.svg" height="40" alt="Résumé (PDF)"></picture></a>
</p>

I take LLM features from a notebook to something the public uses every day: the retrieval and agent layer in Python, the APIs and queues around it, and the interface on top. Most of my job is teaching very confident software to say *"I don't know"*.

Nearly all of my production code lives in private repos, so this page is a guided tour of what's inside them.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/metrics-dark.svg">
  <img src="./assets/metrics-light.svg" width="100%" alt="19 agent tools in production. 300+ daily users on one platform. 2 live AI products in Abu Dhabi. 4.6k contributions since 2024.">
</picture>

## Now: the AI concierge for Abu Dhabi tourism

Working with **Create Group** for the **Department of Culture and Tourism – Abu Dhabi**, I build the conversational AI behind two products, front end and back end:

- **[Ask Abu Dhabi](https://mbilaltaha.com/work/dct-ai-chatbot)**: the AI assistant inside [visitabudhabi.ae](https://www.visitabudhabi.ae). It answers visitor questions about attractions, dining, hotels and events, and builds itineraries in chat.
- **[Digital Concierge](https://mbilaltaha.com/work/digital-concierge)**: a standalone AI trip planner with saved sessions, day-by-day itineraries and a live clustered map.

One request moving through the agent. The tool names are the real ones from production.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/trace-dark.svg">
  <img src="./assets/trace-light.svg" width="100%" alt="Animated agent trace. A visitor asks for a two-day family beach trip. The agent runs check_moderation, search_attractions, search_dining, calculate_distance_to_place, search_itineraries and select_cards_to_display, streams a two-day plan with three place cards over SSE, and sends the trace to Langfuse and Phoenix.">
</picture>

<details>
<summary><b>Architecture</b></summary>
<br>

```mermaid
flowchart LR
    V([Visitor on<br/>visitabudhabi.ae]) --> W[Chat widget<br/>Next.js]
    W <-->|SSE| API[FastAPI]
    API --> G(Moderation +<br/>injection guard)
    G --> A[[LangGraph ReAct agent<br/>GPT-4o · 19 tools]]
    A --> R[(Postgres + pgvector<br/>+ PostGIS)]
    A --> M(Maps · directions<br/>transport)
    A --> I(Itinerary builder)
    CMS[Sitecore CMS] -. scheduled ingestion<br/>+ embeddings .-> R
    A -. traces .-> O(Langfuse · Phoenix)
```

</details>

<details>
<summary><b>What I own on it</b></summary>
<br>

| Layer | Work |
|---|---|
| **Agent** | LangGraph ReAct agent on GPT-4o with 19 tools for search by category, itineraries, distance and directions, transport, links and response cards. Checkpointed conversations, with pruning so long sessions stay cheap. |
| **Retrieval** | Scheduled ingestion of CMS content into Postgres + pgvector, category- and location-aware search, and paginated, deduplicated results so the agent never recommends the same place twice. |
| **Safety** | Input moderation and prompt-injection defences in front of the agent, and links limited to an allow-list so the model can't invent a URL on a government site. |
| **Interface** | The embeddable chat widget on the host site and the Digital Concierge app: SSE streaming, rich listing cards, maps with Mapbox + Supercluster, and offline-friendly state in IndexedDB. |
| **Platform** | Azure B2C sign-in, feedback and reactions, share links, an admin panel for prompts and analytics, tracing with Langfuse and Phoenix, and Azure pipelines. |

</details>

## Selected work

<p>
  <a href="https://mbilaltaha.com/work/harbinger"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/card-harbinger-dark.svg"><img src="./assets/card-harbinger-light.svg" width="49%" alt="Harbinger, AI market intelligence. Reads news, patents and company data around the clock; agents surface the signals worth reading in weekly briefings and a Teams bot. LangGraph, Celery, Redis, pgvector."></picture></a>
  <a href="https://mbilaltaha.com/work/medianet"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/card-medianet-dark.svg"><img src="./assets/card-medianet-light.svg" width="49%" alt="Medianet, offline-first field operations. Daily driver for 300+ field officers at Pakistan's largest power utility. NestJS, Next.js, Prisma, IndexedDB."></picture></a>
  <a href="https://github.com/bilaltaha25132/FYP-VidSense"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/card-vidsense-dark.svg"><img src="./assets/card-vidsense-light.svg" width="49%" alt="VidSense, video RAG. Summaries, timestamped Q&A, highlight reels and AI podcasts from any video. Whisper, Ollama, FastAPI."></picture></a>
  <a href="https://github.com/bilaltaha25132/claude-nestjs"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/card-claude-nestjs-dark.svg"><img src="./assets/card-claude-nestjs-light.svg" width="49%" alt="claude-nestjs, a Claude Code skill that turns a requirements doc into a production NestJS + Prisma backend."></picture></a>
  <a href="https://github.com/bilaltaha25132/linkedin-post-generator"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/card-signal-desk-dark.svg"><img src="./assets/card-signal-desk-light.svg" width="49%" alt="Signal Desk, an LLM content pipeline that finds tech news, scores it and drafts posts in my voice. Next.js, Supabase, pgvector."></picture></a>
  <picture><source media="(prefers-color-scheme: dark)" srcset="./assets/card-remote-hands-dark.svg"><img src="./assets/card-remote-hands-light.svg" width="49%" alt="Remote Hands, an MCP server in Go that lets an AI agent on one machine drive another over the LAN."></picture>
</p>

Also built: **Rihla**, a pilgrimage companion app with indoor maps of the Two Holy Mosques. **Baseline**, an astronaut health self-check PWA for NASA Space Apps 2026. And Claude Code skills that clone websites into Next.js and videos into Remotion templates.

## About me, as code

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BilalTaha:
    role: str = "Full Stack AI Engineer"
    based_in: str = "Karachi, Pakistan"
    now: str = "AI concierge for Abu Dhabi tourism"
    studied: str = "BS Computer Science, IBA Karachi"
    ships: tuple[str, ...] = ("RAG pipelines", "LangGraph agents", "APIs", "the UI on top")
    stack: dict[str, list[str]] = field(default_factory=lambda: {
        "llm": ["LangGraph", "LangChain", "OpenAI", "Azure OpenAI", "Ollama"],
        "retrieval": ["pgvector", "FAISS", "ChromaDB"],
        "llmops": ["Langfuse", "Arize Phoenix"],
        "backend": ["Python", "FastAPI", "Celery", "NestJS", "Node"],
        "frontend": ["Next.js", "React", "TypeScript", "Tailwind", "Flutter"],
        "data": ["PostgreSQL", "Redis", "MongoDB", "Prisma", "Docker", "Azure"],
    })

    def contact(self) -> str:
        return "m.bilal.25132@gmail.com"
```

## Writing

- [Let your chatbot say "I don't know"](https://mbilaltaha.com/blog/let-your-chatbot-say-i-dont-know)
- [The same story, five times: deduplicating before the LLM](https://mbilaltaha.com/blog/deduplicating-before-the-llm)
- [Building for people who lose signal](https://mbilaltaha.com/blog/building-for-people-who-lose-signal)
- [When the fast, dumb approach beats the smart one](https://mbilaltaha.com/blog/when-the-dumb-approach-wins)

## Activity

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/activity-dark.svg">
  <img src="./assets/activity-light.svg" width="100%" alt="Contribution heatmap for the last year, including private client work. Refreshed daily.">
</picture>

---

If you're building LLM products that real users touch, I'd enjoy talking: [m.bilal.25132@gmail.com](mailto:m.bilal.25132@gmail.com) · [case studies](https://mbilaltaha.com/work) · [LinkedIn](https://linkedin.com/in/bilal-taha25132)

<sub>Every graphic on this page is generated by <a href="./scripts/build.py"><code>scripts/build.py</code></a>, set in Geist, and the heatmap is rebuilt daily by a GitHub Action.</sub>
