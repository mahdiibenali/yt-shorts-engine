"""
AI Provider Router — Zero-Cost Multi-Tier LLM Access

Provides a unified interface to generate text using free AI backends:
  Tier 1: Ollama (local LLM, fastest, fully private)
  Tier 2: g4f (free cloud LLM proxy)
  Tier 3: Pollinations.ai (100% free, no API key)
  Tier 4: 9Router (unified local proxy)
  Tier 5: OpenAI (paid, if key provided)
  Tier 6: Template-based fallback (no AI needed at all)

Optional: JimengScriptProvider (jimeng-api Docker container)
"""
import random
import logging
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    """Result from an AI provider."""
    text: str
    provider: str
    model: str


# =============================================================================
# VIRAL SCRIPT TEMPLATES — Used as ultimate fallback when no AI is available
# =============================================================================

HOOK_TEMPLATES = [
    "You won't believe what happened next...",
    "This changed everything I thought I knew.",
    "Nobody talks about this, but it's insane.",
    "I wish someone told me this sooner.",
    "Here's something that will blow your mind.",
    "Stop scrolling. You need to hear this.",
    "Scientists just discovered something terrifying.",
    "This is the craziest thing I've learned all week.",
    "I tested this for 30 days and here's what happened.",
    "Everyone gets this wrong. Here's the truth.",
]

CTA_TEMPLATES = [
    "Follow for more mind-blowing facts!",
    "Like if you didn't know this. Subscribe for more!",
    "Drop a comment — did you know this already?",
    "Share this with someone who needs to hear it!",
    "Hit follow so you don't miss the next one!",
]

THEME_SCRIPTS = {
    "facts": [
        "Did you know that honey never spoils? Archaeologists found 3000-year-old honey in Egyptian tombs and it was still perfectly edible. The secret is its low moisture content and acidic pH which create an inhospitable environment for bacteria.",
        "Octopuses have three hearts and blue blood. Two hearts pump blood to the gills while the third pumps it to the rest of the body. Their blood uses copper-based hemocyanin instead of iron-based hemoglobin.",
        "The shortest war in history lasted just 38 minutes. It was between Britain and Zanzibar on August 27th, 1896. Zanzibar surrendered after their only warship was sunk.",
    ],
    "motivation": [
        "The most successful people in the world all have one thing in common. They failed more times than most people even tried. The difference isn't talent. It's that they refused to stop after getting knocked down.",
        "Your comfort zone is a beautiful place, but nothing ever grows there. Every single breakthrough in your life happened because you did something that scared you. Remember that the next time fear tries to hold you back.",
    ],
    "mystery": [
        "In 1948, a man was found dead on Somerton Beach in Australia. He had no identification, his clothes had no labels, and a scrap of paper in his pocket read 'Tamam Shud' — meaning 'ended' or 'finished'. To this day, nobody knows who he was.",
        "The Wow Signal was a strong narrowband radio signal received by the Big Ear radio telescope in 1977. It lasted 72 seconds and appeared to come from deep space. Despite decades of searching, the signal has never been detected again.",
    ],
    "tech": [
        "Your smartphone has more computing power than the entire NASA mission control had during the Apollo 11 moon landing. The guidance computer on Apollo 11 had just 74 kilobytes of memory. Your phone has millions of times more.",
        "Every minute, over 500 hours of video are uploaded to YouTube. That means it would take you over 82 years of non-stop watching just to see everything uploaded in a single day.",
    ],
    "default": [
        "Here's something incredible that most people don't know about. The human brain processes images 60,000 times faster than text. That's why video content is so powerful — your brain is literally wired to prefer it over reading.",
    ],
}


# =============================================================================
# PROVIDER IMPLEMENTATIONS
# =============================================================================

class OllamaProvider:
    """Tier 1: Local LLM via Ollama (OpenAI-compatible API)."""

    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "llama3.1:8b"):
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def name(self) -> str:
        return f"ollama/{self.model}"

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key="ollama")
        return self._client

    def is_available(self) -> bool:
        try:
            import httpx
            resp = httpx.get(self.base_url.replace("/v1", "") + "/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if not models:
                    return False
                
                # Check for exact or prefix match (e.g., llama3.1 in llama3.1:latest)
                base_name = self.model.split(":")[0]
                for m in models:
                    if m == self.model or base_name in m:
                        self.model = m  # Dynamically set exact tag
                        return True
                
                # Fallback: if Ollama has models installed, use the first available model
                self.model = models[0]
                logger.info(f"Requested Ollama model not found, using first available: {self.model}")
                return True
            return False
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content.strip()
            if text:
                logger.info(f"Ollama generated {len(text)} chars with {self.model}")
                return ProviderResult(text=text, provider="ollama", model=self.model)
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
        return None


class G4FProvider:
    """Tier 2: Free cloud LLM access via g4f (gpt4free)."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    @property
    def name(self) -> str:
        return f"g4f/{self.model}"

    def is_available(self) -> bool:
        try:
            import g4f
            return True
        except ImportError:
            logger.info("g4f not installed. Run: pip install -U g4f")
            return False

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        try:
            from g4f.client import Client
            client = Client()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            text = response.choices[0].message.content.strip()
            if text:
                logger.info(f"g4f generated {len(text)} chars with {self.model}")
                return ProviderResult(text=text, provider="g4f", model=self.model)
        except Exception as e:
            logger.warning(f"g4f generation failed: {e}")
        return None


class NineRouterProvider:
    """Tier 3: 9Router local proxy (OpenAI-compatible API)."""

    def __init__(self, base_url: str = "http://localhost:20128/v1", model: str = "auto"):
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def name(self) -> str:
        return f"9router/{self.model}"

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key="9router")
        return self._client

    def is_available(self) -> bool:
        try:
            import httpx
            resp = httpx.get(f"{self.base_url}/models", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content.strip()
            if text:
                logger.info(f"9Router generated {len(text)} chars")
                return ProviderResult(text=text, provider="9router", model=self.model)
        except Exception as e:
            logger.warning(f"9Router generation failed: {e}")
        return None


class OpenAIProvider:
    """Optional: Standard OpenAI API (for users who have a key)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def name(self) -> str:
        return f"openai/{self.model}"

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content.strip()
            if text:
                logger.info(f"OpenAI generated {len(text)} chars with {self.model}")
                return ProviderResult(text=text, provider="openai", model=self.model)
        except Exception as e:
            logger.warning(f"OpenAI generation failed: {e}")
        return None


class PollinationsProvider:
    """Tier 3: Cloud LLM via Pollinations.ai (API key optional but recommended for higher limits)."""

    SUPPORTED_MODELS = (
        "openai", "openai-fast", "gpt-oss", "deepseek", "mistral", "mistral-small-3.2",
        "llama", "llama-scout", "gemma", "gemma-4-31b", "grok", "qwen-coder",
        "qwen-large", "mimo-v2.5", "nova-fast", "nova", "glm", "step-flash",
        "minimax", "minimax-m2.7", "step-3.5-flash",
    )

    def __init__(self, model: str = "openai", api_key: str = None):
        self.model = model if model in self.SUPPORTED_MODELS else "openai"
        self.api_key = api_key
        self.base_url = "https://gen.pollinations.ai"

    @property
    def name(self) -> str:
        return f"pollinations/{self.model}"

    def is_available(self) -> bool:
        try:
            import httpx
            resp = httpx.get(f"{self.base_url}/models", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        try:
            import httpx
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            resp = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            if text:
                logger.info(f"Pollinations generated {len(text)} chars with {self.model}")
                return ProviderResult(text=text, provider="pollinations", model=self.model)
        except Exception as e:
            logger.warning(f"Pollinations generation failed: {e}")
        return None


class JimengScriptProvider:
    """Optional: Jimeng/Dreamina script generation via jimeng-api Docker container."""

    def __init__(self, base_url: str = "http://localhost:5100/v1", api_key: str = "", model: str = "jimeng"):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def name(self) -> str:
        return f"jimeng/{self.model}"

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(base_url=self.base_url, api_key=self.api_key or "jimeng")
        return self._client

    def is_available(self) -> bool:
        try:
            import httpx
            resp = httpx.get(f"{self.base_url}/models", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content.strip()
            if text:
                logger.info(f"Jimeng generated {len(text)} chars with {self.model}")
                return ProviderResult(text=text, provider="jimeng", model=self.model)
        except Exception as e:
            logger.warning(f"Jimeng generation failed: {e}")
        return None


class TemplateProvider:
    """Tier 6 (Fallback): Template-based script generation. No AI needed."""

    @property
    def name(self) -> str:
        return "template/builtin"

    def is_available(self) -> bool:
        return True  # Always available

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> Optional[ProviderResult]:
        # Try to match theme from the prompt
        prompt_lower = prompt.lower()
        matched_theme = "default"
        for theme in THEME_SCRIPTS:
            if theme in prompt_lower:
                matched_theme = theme
                break

        body = random.choice(THEME_SCRIPTS[matched_theme])
        hook = random.choice(HOOK_TEMPLATES)
        cta = random.choice(CTA_TEMPLATES)

        script = f"{hook}\n\n{body}\n\n{cta}"
        logger.info(f"Template provider generated script (theme: {matched_theme})")
        return ProviderResult(text=script, provider="template", model=matched_theme)


# =============================================================================
# SMART ROUTER — Tries providers in priority order
# =============================================================================

class SmartRouter:
    """
    Tries AI providers in priority order and returns the first successful result.

    Default order: Ollama → g4f → Pollinations → 9Router → OpenAI → Jimeng → Template
    """

    def __init__(self, providers: Optional[List] = None):
        self.providers = providers or []
        self._initialized = False

    @classmethod
    def from_settings(cls, settings) -> "SmartRouter":
        """Build the provider chain from application settings."""
        providers = []

        # Tier 1: Ollama (local)
        providers.append(OllamaProvider(
            base_url=getattr(settings, "ollama_base_url", "http://localhost:11434/v1"),
            model=getattr(settings, "ollama_model", "llama3.1:8b"),
        ))

        # Tier 2: g4f (free cloud)
        providers.append(G4FProvider(
            model=getattr(settings, "g4f_model", "gpt-4o-mini"),
        ))

        # Tier 3: Pollinations (API key optional but recommended)
        providers.append(PollinationsProvider(
            model=getattr(settings, "pollinations_model", "openai"),
            api_key=getattr(settings, "pollinations_api_key", None),
        ))

        # Tier 4: 9Router (proxy)
        nine_router_url = getattr(settings, "nine_router_url", None)
        if nine_router_url:
            providers.append(NineRouterProvider(base_url=nine_router_url))

        # Tier 5: OpenAI (if key is provided)
        openai_key = getattr(settings, "openai_api_key", None)
        if openai_key:
            providers.append(OpenAIProvider(api_key=openai_key))

        # Optional: Jimeng (if jimeng-api is running)
        jimeng_url = getattr(settings, "jimeng_base_url", None)
        jimeng_key = getattr(settings, "jimeng_api_key", "")
        if jimeng_url:
            providers.append(JimengScriptProvider(
                base_url=jimeng_url,
                api_key=jimeng_key,
                model=getattr(settings, "jimeng_model", "jimeng"),
            ))

        # Tier 6: Template fallback (always works)
        providers.append(TemplateProvider())

        router = cls(providers=providers)
        router._log_providers()
        return router

    def _log_providers(self):
        """Log which providers are configured."""
        names = [p.name for p in self.providers]
        logger.info(f"SmartRouter initialized with providers: {' → '.join(names)}")

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 500, temperature: float = 0.8) -> ProviderResult:
        """Try each provider in order. Always returns something (template fallback)."""
        for provider in self.providers:
            if not provider.is_available():
                logger.debug(f"Provider {provider.name} not available, skipping")
                continue

            logger.info(f"Trying provider: {provider.name}")
            result = provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if result:
                return result
            logger.info(f"Provider {provider.name} returned empty result, trying next")

        # This should never happen because TemplateProvider.is_available() is always True
        logger.error("All providers failed. Using emergency template.")
        return TemplateProvider().generate(prompt)

    def get_status(self) -> List[dict]:
        """Return availability status for all providers."""
        return [
            {"name": p.name, "available": p.is_available()}
            for p in self.providers
        ]
