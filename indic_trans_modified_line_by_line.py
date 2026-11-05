from pathlib import Path
import torch
import time
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

import sys
sys.path.append(str(Path(__file__).resolve().parent / "IndicTransToolkit"))

from IndicTransToolkit import IndicProcessor



from constants import LANGUAGE_CODE_TO_INDIC_TRANS_LANGUAGE, DISTILLED_MODEL_ID_MAPPINGS, LARGE_MODEL_ID_MAPPINGS


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def model_translate(texts, source_language, target_language, input_path):

    src_lang, tgt_lang = LANGUAGE_CODE_TO_INDIC_TRANS_LANGUAGE[source_language], LANGUAGE_CODE_TO_INDIC_TRANS_LANGUAGE[target_language]
    key = ""
    if source_language == "en":
        key = "en_to_indic"
    elif target_language == "en":
        key = "indic_to_en"
    else:
        key = "indic_to_indic"
    
    overall_time = time.time()
    model_name = DISTILLED_MODEL_ID_MAPPINGS[key]
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name, 
        trust_remote_code=True, 
        torch_dtype=torch.float16, 
        attn_implementation="flash_attention_2"
    ).to(DEVICE)

    ip = IndicProcessor(inference=True)

    translated_results = []
    for text in texts:

        input_sentences = [text]

        batch = ip.preprocess_batch(
            input_sentences,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
        )
        print ("input sentence ", input_sentences)
        
        inputs = tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(DEVICE)

        
        with torch.no_grad():
            generated_tokens = model.generate(
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=256,
                num_beams=5,
                num_return_sequences=1,
            )

        
        with tokenizer.as_target_tokenizer():
            generated_tokens = tokenizer.batch_decode(
                generated_tokens.detach().cpu().tolist(),
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )

        
        translations = ip.postprocess_batch(generated_tokens, lang=tgt_lang)

        print(f"Total time taken for the entire text {input_path} is {time.time() - overall_time}")
        
        print ("output sentence ", translations)
        translated_results.append(translations[0])
        
    return translated_results
    print (translated_results)