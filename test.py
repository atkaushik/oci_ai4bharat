from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent / "IndicTransToolkit"))

import IndicTransToolkit
print(dir(IndicTransToolkit))
