#!/usr/bin/env python3
import os
import json
import logging
import openai
from dotenv import load_dotenv

# ─── Load API Key ───────────────────────────────────────────────────────────────
load_dotenv(".llm.env")
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in .llm.env or environment")

# ─── Configure Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main():
    client = openai.OpenAI(api_key=API_KEY)

    PROMPT_ID      = "pmpt_68904ffc3ae88194b547c10cdb24cff2078274ab40fc00de"
    PROMPT_VERSION = "5"

    domains = [
        "https://www.aarti-surfactants.com/",
        # "https://www.drewshoneybees.com/",
        # "https://palmbeachherbalteas.com/",
    ]

    all_results = []

    for domain in domains:
        logging.info(f"▶️  Processing {domain}")
        try:
            response = client.responses.create(
                prompt={"id": PROMPT_ID, "version": PROMPT_VERSION},
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": domain}
                    ]
                }],
                text={"format": {"type": "text"}},
                reasoning={},
                store=True
            )

            # ─── Extract Usage ────────────────────────────────────────────
            usage = response.usage
            in_toks  = usage.input_tokens    # total input tokens consumed :contentReference[oaicite:0]{index=0}
            out_toks = usage.output_tokens   # total output tokens generated :contentReference[oaicite:1]{index=1}
            tot_toks = usage.total_tokens    # sum of the above :contentReference[oaicite:2]{index=2}

            logging.info(
                f"   ✓ Tokens — input: {in_toks}, output: {out_toks}, total: {tot_toks}"
            )

            # ─── Extract Model Reply ──────────────────────────────────────
            text = getattr(response, "output_text", None)
            if text is None:
                # fallback: stitch together any output items
                outputs = getattr(response, "output", [])
                fragments = []
                for item in outputs:  # TResponseOutputItem list :contentReference[oaicite:3]{index=3}
                    fragment = getattr(item, "text", None) or getattr(item, "content", None)
                    if fragment:
                        fragments.append(fragment)
                text = "\n".join(fragments)

            # ─── Build & Save Result ───────────────────────────────────────
            result = {
                "domain": domain,
                "usage": {
                    "input_tokens":  in_toks,
                    "output_tokens": out_toks,
                    "total_tokens":  tot_toks,
                },
                "response": text.strip(),
            }

            safe_name = domain.replace("https://", "").replace("/", "_").rstrip("_")
            fname = f"output_{safe_name}.json"
            with open(fname, "w") as f:
                json.dump(result, f, indent=2)
            logging.info(f"   💾  Saved to {fname}")

            all_results.append(result)

        except openai.APIConnectionError as e:
            logging.exception(f"❌ Network error for {domain}: {e}")
        except openai.APIStatusError as e:
            logging.exception(f"❌ HTTP error for {domain}: {e}")
        except openai.RateLimitError as e:
            logging.exception(f"❌ Rate limit hit for {domain}: {e}")
        except openai.APIError as e:
            logging.exception(f"❌ OpenAI API error for {domain}: {e}")
        except Exception as e:
            logging.exception(f"❌ Unexpected error for {domain}: {e}")

    # ─── Write Aggregate ────────────────────────────────────────────────
    with open("all_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    logging.info("✅ Done. Wrote all_results.json")

if __name__ == "__main__":
    main()
