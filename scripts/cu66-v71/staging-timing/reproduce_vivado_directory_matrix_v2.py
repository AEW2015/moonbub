"""Same matrix runner, corrected Windows-case metadata and native child flag trace."""
from pathlib import Path
runner=Path(__file__).with_name('reproduce_vivado_directory_matrix.py');s=runner.read_text();s=s.replace("env.get('NoDefaultCurrentDirectoryInExePath')","next((v for k,v in env.items()if k.upper()=='NODEFAULTCURRENTDIRECTORYINEXEPATH'),None)")
needle='puts "OBSERVED_NATIVE_TMP $::env(TMP)"';s=s.replace(needle,needle+'\nforeach envkey [array names ::env] {if {[string equal -nocase $envkey NODEFAULTCURRENTDIRECTORYINEXEPATH]} {puts "OBSERVED_NATIVE_NODEFAULT $::env($envkey)"}}')
exec(compile(s,str(runner),'exec'),globals())
