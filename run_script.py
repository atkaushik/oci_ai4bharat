from pathlib import Path
import subprocess
import os



lang = ["mr", "te", "bn"]
for i in lang:

    proc = subprocess.Popen(['python', 
                    'perform_transcribe_translate_temp.py', '-m', 'ai4bharat', '-s', 'en', "-t", i ], 
                    cwd=str(Path(__file__).resolve().parent), 
                    stdout=subprocess.DEVNULL, preexec_fn=os.setpgrp)

    proc.wait()