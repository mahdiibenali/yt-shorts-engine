"""Pluggable AI image providers for scene generation.

Each provider is a ``(prompt, width, height) -> bytes | None`` callable.  A
provider returns ``None`` when it is not configured or fails, so the caller
can fall through a chain.  Credentials are read from the environment (or the
repo's ``.env`` file).
"""

import base64
import io
import json
import os
import threading
import time

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

_DASHSCOPE_NEGATIVE = (
    "lowres, bad anatomy, bad hands, extra fingers, watermark, text, "
    "low quality, jpeg artifacts, blurry, deformed, disfigured"
)


def _download(url: str, timeout: float):
    r = requests.get(url, timeout=timeout)
    if r.status_code == 200 and len(r.content) > 1000:
        return r.content
    return None


def _dashscope_headers(key: str):
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def dashscope_qwen(prompt: str, width: int, height: int, timeout: float = 240.0):
    """Generate via Alibaba Cloud Model Studio (Qwen-Image / wanx).

    Reads ``DASHSCOPE_API_KEY`` and ``DASHSCOPE_BASE_URL`` from the
    environment.  Tries the OpenAI-compatible ``/images/generations`` route
    first, then the native ``image-generation/generation`` route (handling
    both synchronous results and the async task-poll flow).
    """
    key = os.environ.get("DASHSCOPE_API_KEY")
    base = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com")
    model = os.environ.get("DASHSCOPE_MODEL", "qwen-image-3.0")
    if not key:
        return None

    size = f"{width}x{height}"

    # 1) OpenAI-compatible route
    try:
        r = requests.post(
            f"{base}/compatible-mode/v1/images/generations",
            headers=_dashscope_headers(key),
            json={"model": model, "prompt": prompt, "size": size, "n": 1},
            timeout=timeout,
        )
        if r.status_code == 200:
            data = (r.json().get("data") or [])
            if data:
                item = data[0]
                if item.get("b64_json"):
                    return base64.b64decode(item["b64_json"])
                if item.get("url"):
                    return _download(item["url"], timeout)
    except Exception:
        pass

    # 2) Native route (sync for qwen-image-3.0/2.0; async for wanx/plus)
    native_size = f"{width}*{height}"
    try:
        r = requests.post(
            f"{base}/api/v1/services/aigc/image-generation/generation",
            headers=_dashscope_headers(key),
            json={
                "model": model,
                "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
                "parameters": {
                    "negative_prompt": _DASHSCOPE_NEGATIVE,
                    "prompt_extend": False,
                    "watermark": False,
                    "size": native_size,
                    "n": 1,
                },
            },
            timeout=timeout,
        )
        if r.status_code == 200:
            out = r.json().get("output", {})
            for res in out.get("results") or []:
                if res.get("url"):
                    return _download(res["url"], timeout)
            task_id = out.get("task_id")
            if task_id:
                return _dashscope_poll(base, key, task_id, timeout)
    except Exception:
        pass
    return None


def _dashscope_poll(base: str, key: str, task_id: str, timeout: float):
    url = f"{base}/api/v1/tasks/{task_id}"
    for _ in range(60):
        time.sleep(2)
        try:
            r = requests.get(url, headers=_dashscope_headers(key), timeout=60)
            out = r.json().get("output", {})
            status = out.get("task_status")
            if status == "SUCCEEDED":
                for res in out.get("results") or []:
                    if res.get("url"):
                        return _download(res["url"], timeout)
                return None
            if status in ("FAILED", "CANCELED"):
                return None
        except Exception:
            return None
    return None


_CF_FLUX_TIERS = (
    "@cf/black-forest-labs/flux-2-klein-9b",  # best quality, ~1364 neurons/img
    "@cf/black-forest-labs/flux-2-klein-4b",  # 0 neurons (free), good quality
    "@cf/black-forest-labs/flux-1-schnell",   # 172.8 neurons/img, last resort
)
_CF_NEURON_FILE = os.path.join(
    os.environ.get("DATA_DIR", "./data"), ".cf_neuron_usage.json"
)


def _cf_neurons_used_today() -> float:
    try:
        with open(_CF_NEURON_FILE) as f:
            rec = json.load(f)
        if rec.get("date") == time.strftime("%Y-%m-%d"):
            return float(rec.get("used", 0))
    except Exception:
        pass
    return 0.0


def _cf_add_neurons(cost: float) -> None:
    if not cost:
        return
    try:
        today = time.strftime("%Y-%m-%d")
        try:
            with open(_CF_NEURON_FILE) as f:
                rec = json.load(f)
        except Exception:
            rec = {}
        if rec.get("date") != today:
            rec = {"date": today, "used": 0.0}
        rec["used"] = float(rec.get("used", 0)) + cost
        os.makedirs(os.path.dirname(_CF_NEURON_FILE) or ".", exist_ok=True)
        with open(_CF_NEURON_FILE, "w") as f:
            json.dump(rec, f)
    except Exception:
        pass


def _cf_run(model: str, prompt: str, timeout: float):
    """POST one image to Workers AI; return ``(bytes | None, neurons_cost)``."""
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account or not token:
        return None, 0.0
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
    try:
        if "flux-1-schnell" in model:
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={"prompt": prompt[:2048], "steps": 4},
                timeout=timeout,
            )
        else:
            steps = os.environ.get(
                "CLOUDFLARE_FLUX_STEPS", "12" if "9b" in model else "8"
            )
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                files={"prompt": (None, prompt[:2048]), "steps": (None, steps)},
                timeout=timeout,
            )
        cost = float(r.headers.get("cf-ai-neurons") or 0)
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("result", {}).get("image"):
                return base64.b64decode(data["result"]["image"]), cost
    except Exception:
        pass
    return None, 0.0


def cloudflare_flux(prompt: str, width: int, height: int, timeout: float = 180.0):
    """Generate via Cloudflare Workers AI with automatic quality tiering.

    Tries FLUX.2 [klein] 9B first (best quality, ~1364 neurons/image) while a
    client-side daily neuron budget remains, then the 0-neuron FLUX.2 [klein]
    4B (free/unlimited), and finally FLUX.1-schnell.  Reads
    ``CLOUDFLARE_ACCOUNT_ID`` / ``CLOUDFLARE_API_TOKEN`` from the environment
    and budgets via ``CLOUDFLARE_FLUX_DAILY_BUDGET`` (default 9000).
    """
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account or not token:
        return None

    try:
        budget = int(os.environ.get("CLOUDFLARE_FLUX_DAILY_BUDGET", "9000"))
    except ValueError:
        budget = 9000
    models = (
        _CF_FLUX_TIERS if _cf_neurons_used_today() < budget else _CF_FLUX_TIERS[1:]
    )

    for model in models:
        data, cost = _cf_run(model, prompt, timeout)
        if data:
            _cf_add_neurons(cost)
            return data
    return None


def pollinations_with_token(prompt: str, width: int, height: int, timeout: float = 180.0):
    """Generate via Pollinations' unified API (``gen.pollinations.ai``).

    Uses a registered ``POLLINATIONS_TOKEN`` (free daily Pollen grants unlock
    the free models).  ``POLLINATIONS_IMAGE_MODEL`` selects the primary model
    (default ``kontext``, i.e. FLUX.1 Kontext Pro); when a model is out of
    balance the cheaper ``zimage`` / ``flux`` models are tried as fallbacks.
    Falls back to the legacy ``image.pollinations.ai`` endpoint when the
    unified API refuses.
    """
    token = os.environ.get("POLLINATIONS_TOKEN")
    if not token:
        return None
    import urllib.parse

    primary = os.environ.get("POLLINATIONS_IMAGE_MODEL", "kontext")
    models = []
    for m in [primary, "zimage", "flux"]:
        if m not in models:
            models.append(m)
    quoted = urllib.parse.quote(prompt)
    for model in models:
        urls = [
            f"https://gen.pollinations.ai/image/{quoted}"
            f"?model={model}&width={width}&height={height}&nologo=true",
            f"https://image.pollinations.ai/prompt/{quoted}"
            f"?width={width}&height={height}&model={model}&nologo=true&token={token}",
        ]
        for url in urls:
            try:
                r = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"},
                    timeout=timeout,
                )
                if r.status_code == 200 and len(r.content) > 5000:
                    return r.content
            except Exception:
                pass
    return None


_local_pipe = None
_local_pipe_lock = threading.Lock()


def _load_local_pipe():
    """Lazily load the local SD checkpoint once; return the pipe or ``None``."""
    global _local_pipe
    if _local_pipe is not None:
        return _local_pipe or None
    with _local_pipe_lock:
        if _local_pipe is not None:
            return _local_pipe or None
        ckpt = os.environ.get("LOCAL_SD_CKPT")
        if not ckpt or not os.path.exists(ckpt):
            _local_pipe = False
            return None
        try:
            import torch
            from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

            pipe = StableDiffusionPipeline.from_single_file(
                ckpt, torch_dtype=torch.float16, safety_checker=None
            )
            try:
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                    pipe.scheduler.config
                )
            except Exception:
                pass
            pipe = pipe.to("cuda")
            pipe.enable_attention_slicing()
            try:
                pipe.enable_vae_slicing()
            except Exception:
                pass
            _local_pipe = pipe
        except Exception:
            _local_pipe = False
    return _local_pipe or None


def local_sd(prompt: str, width: int, height: int, timeout: float = 300.0):
    """Generate on-device with a local Stable Diffusion checkpoint.

    Reads ``LOCAL_SD_CKPT`` (a diffusers-compatible single-file checkpoint),
    with optional ``LOCAL_SD_STEPS`` / ``LOCAL_SD_SIZE`` overrides.  The
    generated image is smaller than the requested size; callers upscale it.
    Returns ``None`` when unconfigured or the load fails so the chain can
    fall through to other providers.
    """
    pipe = _load_local_pipe()
    if pipe is None:
        return None
    try:
        steps = int(os.environ.get("LOCAL_SD_STEPS", "25"))
        size = int(os.environ.get("LOCAL_SD_SIZE", "640"))
        neg = os.environ.get(
            "LOCAL_SD_NEGATIVE",
            "lowres, bad anatomy, blurry, watermark, text, deformed, "
            "jpeg artifacts, duplicate",
        )
        img = pipe(
            prompt[:300],
            negative_prompt=neg,
            num_inference_steps=steps,
            guidance_scale=7.0,
            width=size,
            height=size,
        ).images[0]
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()
    except Exception:
        return None


PROVIDERS = {
    "local": local_sd,
    "cloudflare": cloudflare_flux,
    "pollinations": pollinations_with_token,
    "dashscope": dashscope_qwen,
}

_REQUIRED_ENV = {
    "local": "LOCAL_SD_CKPT",
    "cloudflare": "CLOUDFLARE_API_TOKEN",
    "dashscope": "DASHSCOPE_API_KEY",
    "pollinations": "POLLINATIONS_TOKEN",
}


def _env_ready(name: str) -> bool:
    key = _REQUIRED_ENV.get(name)
    if not key or not os.environ.get(key):
        return False
    if name == "local":
        return os.path.exists(os.environ[key])
    return True


def ordered_providers(order: str | None = None):
    """Return ``(name, callable)`` pairs in the configured order.

    ``order`` is a comma-separated provider name list from the
    ``IMAGE_PROVIDER`` env var.  ``"auto"`` (the default) uses every provider
    whose credentials are present, quality-first.
    """
    order = order or os.environ.get("IMAGE_PROVIDER", "auto")
    if order == "auto":
        return [(n, PROVIDERS[n]) for n in PROVIDERS if _env_ready(n)]
    return [(n, PROVIDERS[n]) for n in order.split(",") if n in PROVIDERS]


def generate_image(prompt: str, width: int, height: int, order: str | None = None):
    """Try each configured provider in order; return image bytes or ``None``."""
    for _name, fn in ordered_providers(order):
        try:
            data = fn(prompt, width, height)
            if data:
                return data
        except Exception:
            continue
    return None
