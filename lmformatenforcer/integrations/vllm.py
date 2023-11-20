try:
    import torch
    import vllm
except ImportError:
    raise ImportError('vllm is not installed. Please install it with "pip install vllm"')
from lmformatenforcer import CharacterLevelParser, TokenEnforcer, FormatEnforcerAnalyzer
from lmformatenforcer.integrations.transformers import build_regular_tokens_list
from typing import List
import math


class VLLMLogitsProcessor:
    def __init__(self, token_enforcer: TokenEnforcer, analyze):
        self.token_enforcer = token_enforcer
        self.analyzer = FormatEnforcerAnalyzer(token_enforcer) if analyze else None

    def __call__(self, input_ids: List[int], scores: torch.Tensor) -> torch.Tensor:
        token_sequence = input_ids
        if self.analyzer:
            self.analyzer.report_raw_logits(token_sequence, scores.tolist())
        allowed_tokens = self.token_enforcer.get_allowed_tokens(token_sequence)
        mask = torch.full_like(scores, -math.inf)
        mask[allowed_tokens] = 0
        scores = scores + mask
        return scores


def build_vllm_logits_processor(llm: vllm.LLM, character_level_parser: CharacterLevelParser, analyze: bool=False) -> VLLMLogitsProcessor:
    """Build the logits processor function that llama.cpp will use to filter the tokens generated by the model. The result
    can be passed in the logits_processor list that is sent to the call or generate() method of llama.cpp models."""
    tokenizer = llm.get_tokenizer()
    regular_tokens = build_regular_tokens_list(tokenizer)
    token_enforcer = TokenEnforcer(regular_tokens, character_level_parser, tokenizer.decode, tokenizer.eos_token_id)
    return VLLMLogitsProcessor(token_enforcer, analyze)


__all__ = ['build_vllm_logits_processor']