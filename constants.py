LANGUAGE_CODE_TO_LANGUAGE = {
    "as": "Assamese",
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "kn": "Kannada",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ml": "Malayalam",
    "or": "Odia",
    "ks": "Kashmiri",  
    "ne": "Nepali",
    "sa": "Sanskrit",
    "sd": "Sindhi",  
    "ur": "Urdu",
}

LANGUAGE_CODE_TO_INDIC_TRANS_LANGUAGE = {
    "as": "asm_Beng",
    "bn": "ben_Beng",
    "en": "eng_Latn",
    "gu": "guj_Gujr",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ks": "kas_Deva",  
    "ml": "mal_Mlym",
    "mr": "mar_Deva",
    "ne": "npi_Deva",
    "or": "ory_Orya",
    "pa": "pan_Guru",
    "sa": "san_Deva",
    "sd": "snd_Deva",  
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "ur": "urd_Arab",
}

LARGE_MODEL_ID_MAPPINGS = {
    "en_to_indic": "ai4bharat/indictrans2-en-indic-1B",
    "indic_to_indic": "ai4bharat/indictrans2-indic-indic-1B",
    "indc_to_en": "ai4bharat/indictrans2-indic-en-1B",
}

DISTILLED_MODEL_ID_MAPPINGS = {
    "en_to_indic": "ai4bharat/indictrans2-en-indic-dist-200M",
    "indic_to_indic": "ai4bharat/indictrans2-indic-indic-dist-320M",
    "indc_to_en": "ai4bharat/indictrans2-indic-en-dist-200M",
}