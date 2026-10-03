"""Read official Excel values even when vendor styles violate OOXML; preserve original."""
from io import BytesIO
import zipfile
import pandas as pd

def read_values(path,**kwargs):
    try:
        return pd.read_excel(path,**kwargs)
    except ValueError as exc:
        if 'stylesheet' not in str(exc) and 'aRGB' not in str(exc): raise
        buf=BytesIO()
        with zipfile.ZipFile(path) as src,zipfile.ZipFile(buf,'w') as out:
            for info in src.infolist():
                if info.filename!='xl/styles.xml':out.writestr(info,src.read(info.filename))
        buf.seek(0)
        return pd.read_excel(buf,**kwargs)
