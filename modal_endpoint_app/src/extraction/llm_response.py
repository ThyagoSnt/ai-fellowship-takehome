# src/extraction/llm_extraction.py
import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import time

class FieldExtractor:
    def __init__(
            self,
            openai_api_key: Optional[str] = None,
            model: str = "gpt-5-mini-2025-08-07"
            ):
        
        # Load API key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        load_dotenv()

        self.llm = ChatOpenAI(
            model=model,
            reasoning={"effort": "minimal"},
            text={"verbosity": "low"},
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        # System prompt for strict JSON extraction
        self.system_prompt = (
            "You are an information extraction agent. "
            "Your job is to extract specific fields from the provided document TEXT. "
            "Return a valid JSON object. "
            "Always respond with a single valid JSON object containing EXACTLY the requested keys. "
            "If a value is missing or not present, use null. "
            "Never include explanations, markdown, or extra keys. "
            "The document may be in Brazilian Portuguese."
        )

    @staticmethod
    def try_parse_json(s: str) -> Dict[str, Any]:
        """Strict parse; if it fails, try slicing the first {...} block."""
        try:
            return json.loads(s)
        except Exception:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = s[start : end + 1]
                try:
                    return json.loads(snippet)
                except Exception:
                    return {}
            return {}
        
    def _as_text(self, resp) -> str:
        """
        Normalize LangChain response to plain text.
        Works for: AIMessage, [AIMessage], string content, or content blocks.
        """
        msg = resp[0] if isinstance(resp, list) else resp
        content = getattr(msg, "content", msg)

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):  # content blocks
            parts = []
            for b in content:
                if isinstance(b, dict) and b.get("type") == "text":
                    parts.append(b.get("text", "") or "")
                else:
                    if getattr(b, "type", None) == "text":
                        parts.append(getattr(b, "text", "") or "")
            return "".join(parts).strip()

        return str(content).strip()



    def _extract_with_gpt(
        self,
        text: str,
        schema_keys: List[str],
        label: str,
        rag_context: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        """Call GPT via LangChain and extract the requested fields as JSON."""
        context_block = (
            "You may use the following previous example from the same document type. "
            "Only reuse a value if it clearly matches the CURRENT document.\n"
            "----- BEGIN PREVIOUS EXAMPLE -----\n"
            f"{rag_context}\n"
            "----- END PREVIOUS EXAMPLE -----\n\n"
            if rag_context
            else ""
        )

        user_instructions = (
            "Current task information:\n"
            f"- document_label: {label}\n"
            f"- required_fields: {schema_keys}\n"
            "----- BEGIN CURRENT DOCUMENT TEXT -----\n"
            f"{text}\n"
            "----- END CURRENT DOCUMENT TEXT -----\n\n"
            "Instructions:\n"
            "1. Return ONLY a valid JSON object.\n"
            "2. The JSON MUST contain exactly the keys in required_fields.\n"
            "3. If a field does not appear, set it to null.\n"
            "4. Do not include explanations or markdown.\n"
            "5. Use ONLY the provided text; do not infer beyond it.\n\n"
            + context_block
        )

        # If the user passed a custom model, update it
        if model:
            self.llm.model = model

        # Perform the call
        start_inference = time.time()
        response = self.llm.invoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_instructions),
        ])
        end_inference = time.time()
        print(f"[DEBUG] Inference time: {end_inference - start_inference:.2f}s")

        # Always get plain text safely
        raw = self._as_text(response)

        parsed = self.try_parse_json(raw)

        # Post-processing: clean nulls and whitespace
        final: Dict[str, Optional[str]] = {}
        for key in schema_keys:
            value = parsed.get(key, None)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned == "" or cleaned.upper() in {"N/A", "NA", "-", "NULL"}:
                    value = None
                else:
                    value = cleaned
            final[key] = value

        return final